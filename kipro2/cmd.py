import logging
import signal
import sys
from enum import Enum, auto
from multiprocessing import Pool
from pathlib import Path
from typing import Any, Optional, Union, Tuple
import attr

import click

from kipro2.incremental_bmc.incremental_bmc import IncrementalBMC
from kipro2.k_induction.incremental_k_induction import IncrementalKInduction
from kipro2.utils.cmd import CommentArgsCommand
from kipro2.utils.statistics import Statistics
from kipro2.utils.utils import setup_sigint_handler, picklable_exceptions
from kipro2.utils.utils import set_max_memory

logger = logging.getLogger("kipro2")


@click.command(cls=CommentArgsCommand)
@click.argument('program', type=click.Path(exists=True))
@click.option('--post', type=click.STRING, help="The post-expectation.")
@click.option('--pre',
              type=click.STRING,
              help="The upper bound to the pre-expectation.")
@click.option('--stats-path',
              type=click.Path(),
              help="A path where to write a statistics file into.")
@click.option(
    '--assert-inductive',
    type=click.INT,
    help="Throw an error if inductiveness cannot be proven in N steps.")
@click.option('--assert-refute',
              type=click.INT,
              help="Throw an error if refutation cannot be done in N steps.")
@click.option(
    '--checker',
    type=click.Choice(['bmc', 'kind', 'both']),
    default="both",
    help=
    "Which checker to use. If 'both' is selected, the stats path will be modified."
)
@click.option('--name',
              type=click.STRING,
              help="A name to attach to the statistics.")
@click.option(
    '--ert/--no-ert',
    default=False,
    help=
    "Whether to check upper bounds on expected runtimes (ert) or expected outcomes (wp)."
)
@click.option('--memory-limit',
              help="Maximum memory for each process in megabytes.")
def main(program, post, pre, stats_path, assert_inductive, assert_refute,
         checker, name, ert, memory_limit):
    setup_sigint_handler()
    if memory_limit is not None:
        set_max_memory(int(memory_limit))

    print("ERT=%s" % ert)
    _setup_logger("log.txt", logging.DEBUG, logging.DEBUG)

    assert not (
        assert_inductive is not None and assert_refute is not None
    ), "--assert-inductive and --assert-refute are mutually exclusive"

    if assert_inductive is not None:
        assert_inductive = int(assert_inductive)
    if assert_refute is not None:
        assert_refute = int(assert_refute)

    with open(program, 'r') as program_file:
        program_code = program_file.read()

    def bmc_task() -> 'CheckTask':
        if stats_path is not None:
            if checker == 'both':
                stats_path_bmc = Path(str(_append_stem(stats_path, "bmc")))
            else:
                stats_path_bmc = Path(str(stats_path))
        else:
            stats_path_bmc = None
        return CheckTask(name=name,
                         checker=Checker.BMC,
                         program=program,
                         program_code=program_code,
                         post=post,
                         pre=pre,
                         stats_path=stats_path_bmc,
                         assert_inductive=assert_inductive,
                         assert_refute=assert_refute,
                         ert=ert)

    def kind_task() -> 'CheckTask':
        if stats_path is not None:
            if checker == 'both':
                stats_path_kind = Path(str(_append_stem(stats_path, "kind")))
            else:
                stats_path_kind = Path(str(stats_path))
        else:
            stats_path_kind = None
        return CheckTask(name=name,
                         checker=Checker.K_INDUCTION,
                         program=program,
                         program_code=program_code,
                         post=post,
                         pre=pre,
                         stats_path=stats_path_kind,
                         assert_inductive=assert_inductive,
                         assert_refute=assert_refute,
                         ert=ert)

    if checker == 'bmc':
        _run_check_task(bmc_task())
    elif checker == 'kind':
        _run_check_task(kind_task())
    else:
        pool = Pool(2)
        for _done in pool.imap_unordered(_run_check_task_picklable_exceptions,
                                         [bmc_task(), kind_task()]):
            pool.terminate()
            break
        pool.close()
        pool.join()


class Checker(Enum):
    BMC = auto()
    K_INDUCTION = auto()

    def __str__(self) -> str:
        return "bmc" if self == Checker.BMC else "kind"


@attr.s
class CheckTask:
    name: Optional[str] = attr.ib()
    checker: Checker = attr.ib()
    program: Path = attr.ib()
    program_code: str = attr.ib()
    post: str = attr.ib()
    pre: str = attr.ib()
    stats_path: Optional[Path] = attr.ib()
    assert_inductive: Optional[int] = attr.ib()
    assert_refute: Optional[int] = attr.ib()
    ert: Optional[bool] = attr.ib()

    def make_statistics(self) -> Statistics:
        return Statistics({
            "name": self.name,
            "checker": str(self.checker),
            "program": str(self.program),
            "post": self.post,
            "pre": self.pre,
            "assert_inductive": self.assert_inductive,
            "assert_refute": self.assert_refute,
        })

    def make_bmc(self, statistics: Statistics) -> IncrementalBMC:
        assert self.checker == Checker.BMC
        return IncrementalBMC(program=self.program_code,
                              post_expectation=self.post,
                              upper_bound_expectation=self.pre,
                              statistics=statistics,
                              assert_refute=self.assert_refute,
                              ert=self.ert)

    def make_kind(self, statistics: Statistics) -> IncrementalKInduction:
        assert self.checker == Checker.K_INDUCTION
        return IncrementalKInduction(program=self.program_code,
                                     post_expectation=self.post,
                                     upper_bound_expectation=self.pre,
                                     statistics=statistics,
                                     assert_inductive=self.assert_inductive,
                                     assert_refute=self.assert_refute,
                                     ert=self.ert)

    def make_checker(
        self, statistics: Statistics
    ) -> Union[IncrementalBMC, IncrementalKInduction]:
        if self.checker == Checker.BMC:
            return self.make_bmc(statistics)
        else:
            return self.make_kind(statistics)

    def write_statistics(self, statistics: Statistics, status: str):
        statistics.status = status
        if self.stats_path is not None:
            statistics.dump_to_files(str(self.stats_path))


def _run_check_task_picklable_exceptions(check_task: CheckTask) -> Statistics:
    # see https://bugs.python.org/issue37208
    # some exceptions can't be pickled, and so multiprocessing gives weird errors if a subprocess crashes
    return picklable_exceptions(_run_check_task)(check_task)


def _run_check_task(check_task: CheckTask) -> Statistics:
    setup_sigint_handler()

    statistics = check_task.make_statistics()

    check_task.write_statistics(statistics, "started")

    def sigterm_handler(_signum, _frame):
        check_task.write_statistics(statistics, "sigterm")
        sys.exit(1)

    # prev_handler = signal.signal(signal.SIGTERM, sigterm_handler)

    try:
        checker = check_task.make_checker(statistics)
        if isinstance(checker, IncrementalBMC):
            res = checker.apply_bmc()
            status = "undecided" if res else "refuted"
        else:
            res = checker.apply_k_induction()
            status = "inductive" if res else "undecided"
    except MemoryError as e:
        check_task.write_statistics(statistics, "oom")
        raise e
    except Exception as e:
        check_task.write_statistics(statistics, "err")
        raise e

    check_task.write_statistics(statistics, status)

    # signal.signal(signal.SIGTERM, prev_handler)

    return statistics


def _setup_logger(logfile, cmd_loglevel, file_loglevel):
    logger = logging.getLogger("kipro2")
    logger.setLevel(cmd_loglevel)

    # create file handler which logs even debug messages
    fh = logging.FileHandler(logfile)
    fh.setLevel(file_loglevel)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(cmd_loglevel)
    # create formatter and add it to the handlers
    fileformatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    consoleformatter = logging.Formatter('%(name)s: %(message)s')

    ch.setFormatter(consoleformatter)
    fh.setFormatter(fileformatter)
    # add the handlers to logger
    logger.addHandler(ch)
    logger.addHandler(fh)


def _append_stem(path: str, text: str) -> str:
    p = Path(path)
    name_parts = p.name.split(".")
    if len(name_parts) > 0:
        name_parts[0] += "-" + text
    else:
        name_parts = [text]
    return str(p.with_name(".".join(name_parts)))


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
