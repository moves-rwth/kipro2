import logging
import re
import shlex
import subprocess
import time
from pathlib import Path
from typing import List, Optional, Union
import random
import os
from collections import Counter
import string

import attr
import click


def _setup_logger(logger):
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler("benchmark.log")
    fileformatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(fileformatter)
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)

    ch = logging.StreamHandler()
    consoleformatter = logging.Formatter('%(asctime)s: %(message)s')
    ch.setFormatter(consoleformatter)
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)


logger = logging.getLogger("benchmark")
_setup_logger(logger)

RuntimeResult = Union[str, float]
"""A RuntimeResult is either "MO", "TO", "ERR", or a runtime in seconds."""


def human_runtime_result(result: RuntimeResult) -> str:
    """Round numbers and write "<0.1" if values are small."""
    if isinstance(result, str):
        return result
    if result < 0.1:
        return "<0.1"
    return f"{result:.2f}"


class Limits:
    """Limits on execution time and memory."""
    runtime_seconds: int
    memory_mb: int

    @staticmethod
    def parse(runtime_seconds: str, memory_mb: str) -> 'Limits':
        return Limits(runtime_seconds=int(runtime_seconds),
                      memory_mb=int(memory_mb))

    def __init__(self, runtime_seconds: int, memory_mb: int):
        self.runtime_seconds = runtime_seconds
        self.memory_mb = memory_mb

    def command_with_limits(self, command_list: List[str]) -> List[str]:
        return [
            "benchmarks/timeout/timeout", "--confess", "--no-info-on-success",
            "-t",
            str(self.runtime_seconds), "-m",
            str(self.memory_mb * 1024)
        ] + command_list

    def run_with_limits(self, command_list: List[str]) -> RuntimeResult:
        """Execute a command with the limits and time the execution."""

        command_list = self.command_with_limits(command_list)
        command_str = shlex.join(command_list)

        logger.debug("Starting program: %s", command_str)

        # unique identifier string for the timeout script's output
        timeout_ident = ''.join(
            random.choice(string.ascii_uppercase + string.digits)
            for _ in range(10)) + " "
        env = dict(os.environ)
        env["TIMEOUT_IDSTR"] = timeout_ident

        # Now start the process, and measure the time.
        start_time = time.perf_counter()

        process = subprocess.Popen(command_list,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   cwd=Path(__file__).resolve().parent.parent,
                                   text=True,
                                   env=env)

        stdout, stderr = process.communicate()
        extra = {"stdout": stdout, "stderr": stderr}
        if process.returncode != 0:
            if len(stderr) != 0:
                timeout_matches = [
                    line[len(timeout_ident):] for line in stderr.splitlines()
                    if line.startswith(timeout_ident)
                ]
                if len(timeout_matches) != 0:
                    timeout_str = timeout_matches[0]
                else:
                    timeout_str = ""
                if timeout_str.startswith("TIMEOUT"):
                    logger.info(f"Program timed out: {command_str}",
                                extra=extra)
                    return "TO"
                elif timeout_str.startswith("MEM") or "MemoryError" in stderr:
                    logger.info(f"Program ran out of memory: {command_str}",
                                extra=extra)
                    return "MO"
                else:
                    logger.error(
                        f"Program crashed (status {process.returncode}): {command_str}\nStandard output:\n{stdout}\nStandard error:\n{stderr}",
                        extra=extra)
                    return "ERR"
        time_diff = time.perf_counter() - start_time
        logger.info(
            f"Process returned after {time_diff} seconds: {command_str}")
        return time_diff


@attr.s
class Benchmark:
    name: str = attr.ib()
    program: Path = attr.ib()

    def command(self, stats_path: Optional[Path], memory_mb: Optional[int] = None) -> List[str]:
        command = [
            "poetry",
            "run",
            "kipro2",
            self.program,
            "--name",
            self.name,
        ]
        if stats_path is not None:
            command.extend(["--stats-path", stats_path.joinpath(self.name)])
        if memory_mb is not None:
            command.extend(["--memory-limit", memory_mb])
        return list(map(str, command))


def glob_benchmarks(base: Path, glob: str = "*.pgcl") -> List[Benchmark]:
    res = []
    for path in base.glob(glob):
        with path.open() as f:
            first_line = f.readline()
            if not first_line.startswith(
                    "// ARGS:") and not first_line.startswith("# ARGS:"):
                logger.warning(
                    "File does not start with // ARGS: comment, skipping: %s",
                    path)
                continue
        res.append(Benchmark(name=path.name.split(".")[0], program=path))
    return res


def filter_benchmarks(filter_str: Optional[str],
                      benchmarks: List[Benchmark]) -> List[Benchmark]:
    if filter_str is None:
        return benchmarks
    pattern = re.compile(filter_str)

    def filter_benchmark(benchmark: Benchmark) -> bool:
        if pattern.match(benchmark.name) is None:
            logger.info("Skipping benchmark %s", benchmark.name)
            return False
        return True

    return list(filter(filter_benchmark, benchmarks))


BENCHMARK_SETS = ["one_loop_examples", "cav21"]


@click.group()
def cli():
    pass


@cli.command(help='run all benchmarks')
@click.argument('filter', required=False)
@click.option('--timeout',
              type=click.INT,
              help='timeout in seconds',
              default=str(15 * 60))
@click.option('--memory',
              type=click.INT,
              help='memory limit in megabytes per process',
              default=str(8 * 1024))
def run(filter, timeout, memory):
    limits = Limits.parse(timeout, int(2.5*memory))
    results = Counter()
    stats_timestamp = time.strftime('%Y-%m-%d-%H-%M-%S')
    for benchmark_set in BENCHMARK_SETS:
        benchmarks = glob_benchmarks(Path(f"benchmarks/{benchmark_set}/"))
        benchmarks = filter_benchmarks(filter, benchmarks)
        stats_path = Path(
            f"benchmarks/stats_{stats_timestamp}/{benchmark_set}/")
        stats_path.mkdir(parents=True)
        for benchmark in benchmarks:
            res = limits.run_with_limits(
                benchmark.command(stats_path=stats_path, memory_mb=memory))
            if isinstance(res, str):
                results.update([res])
            else:
                results.update([True])

    logger.info("Done! Successes: %s, Crashes: %s, Timeouts: %s, OOMs: %s",
                results.get(True), results.get("ERR"), results.get("TO"),
                results.get("MO"))

    print()
    print("-----------------------------------")
    print()
    print("Results for Table 2 of the paper:")
    table2_command = f"poetry run python3 benchmarks/tabulate.py benchmarks/stats_{stats_timestamp}/cav21/"
    print(f"> {table2_command}", flush=True)
    subprocess.run(shlex.split(table2_command))
    print()
    print("-----------------------------------")
    print()
    table3_command = f"poetry run python3 benchmarks/tabulate.py benchmarks/stats_{stats_timestamp}/one_loop_examples/"
    print("Results for Table 3 of the paper:")
    print(f"> {table3_command}", flush=True)
    subprocess.run(shlex.split(table3_command))


@cli.command(name='list',
             help='print benchmark commands as a list to be used in a script')
@click.argument('filter', required=False)
@click.option('--timeout',
              type=click.INT,
              help='timeout in seconds',
              default=str(15 * 60))
@click.option('--memory',
              type=click.INT,
              help='memory limit in megabytes per process',
              default=str(8 * 1024))
def print_list(filter, timeout, memory):
    limits = Limits.parse(timeout, int(2.5*memory))
    stats_timestamp = time.strftime('%Y-%m-%d-%H-%M-%S')
    for benchmark_set in BENCHMARK_SETS:
        benchmarks = glob_benchmarks(Path(f"benchmarks/{benchmark_set}/"))
        benchmarks = filter_benchmarks(filter, benchmarks)
        stats_path = Path(
            f"benchmarks/stats_{stats_timestamp}/{benchmark_set}")
        stats_path.mkdir(parents=True)
        for benchmark in benchmarks:
            command_list = limits.command_with_limits(
                benchmark.command(stats_path=stats_path, memory_mb=memory))
            print(shlex.join(command_list))


def main():
    cli()


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
