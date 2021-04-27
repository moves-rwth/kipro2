import json
import pickle
import time
from types import MethodType
from typing import Any, BinaryIO, Dict, Optional

import attr
from pysmt.shortcuts import Solver


@attr.s
class Timer:
    """
    A timer keeps a total time in seconds and allows starting and stopping it to
    increment the values.
    """

    _elapsed: float = attr.ib(default=0.0)
    _timer_start: Optional[float] = attr.ib(default=None)
    """The start time returned from time.perf_counter()."""
    def start_timer(self):
        assert self._timer_start is None, "cannot start timer twice without stopping in between"
        self._timer_start = time.perf_counter()

    def stop_timer(self):
        end = time.perf_counter()
        assert self._timer_start is not None, "cannot stop timer that is not running"
        self._elapsed += end - self._timer_start
        self._timer_start = None

    @property
    def value(self) -> float:
        """Return the current value of this timer, including running timer values."""
        extra = time.perf_counter(
        ) - self._timer_start if self._timer_start is not None else 0
        return self._elapsed + extra

    def __getstate__(self) -> float:
        return self.value

    def __setstate__(self, value: float):
        self._elapsed = value
        self._timer_start = None

    def __str__(self) -> str:
        return f"{round(self.value, 2)} s"


def _make_running_timer() -> Timer:
    timer = Timer()
    timer.start_timer()
    return timer


@attr.s
class Statistics:

    args: Dict[str, Any] = attr.ib()
    status: str = attr.ib(default="started")
    total_time: Timer = attr.ib(factory=_make_running_timer)
    compute_formulae_time: Timer = attr.ib(factory=Timer)
    sat_check_time: Timer = attr.ib(factory=Timer)
    k: Optional[int] = attr.ib(default=None)
    number_formulae: Optional[int] = attr.ib(default=None)

    def __str__(self) -> str:
        lines = [
            "------ Statistics ------", f"Total time = {self.total_time}.",
            f"Time for computing formulae = {self.compute_formulae_time}.",
            f"Time for sat checks: {self.sat_check_time}."
        ]
        return "\n".join(lines)

    def dump_to_files(self, path: str):
        with open(path + '.pickle', 'wb') as f:
            pickle.dump(self, f)
        with open(path + '.json', 'w') as f:
            f.write(json.dumps(self.__dict__, indent=4, cls=StatisticsEncoder))


class StatisticsEncoder(json.JSONEncoder):
    """A custom encoder that can encode Statistics and Timers."""
    def default(self, obj):
        if isinstance(obj, Timer):
            return obj.value
        return super(json.JSONEncoder, self).default(obj)


def StatisticsSolver(statistics: Statistics, name=None, logic=None, **kwargs):
    """Create a new PySMT solver which also updates the sat check timer automatically."""
    solver = Solver(name, logic, **kwargs)
    old_is_sat = solver.is_sat

    def _timing_is_sat(self, *args, **kwargs):
        statistics.sat_check_time.start_timer()
        try:
            res = old_is_sat(*args, **kwargs)
        finally:
            statistics.sat_check_time.stop_timer()
        return res

    solver.is_sat = MethodType(_timing_is_sat, solver)
    return solver
