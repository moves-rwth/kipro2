# TODO: Test infty, test monus
import pytest
from pysmt.shortcuts import *

from kipro2.incremental_bmc.incremental_bmc import *
from kipro2.utils.statistics import Statistics

from tests.programs import *

def run_bmc(program, post_exp, pre_exp):
    statistics = Statistics(dict())
    res = IncrementalBMC(program, post_exp, pre_exp, statistics, 500, 1,
                         True).apply_bmc()
    reset_env()
    return res

def test_brp():
    # // ARGS: --post "totalFailed" --pre "totalFailed + 1" --checker both
    program = brp
    post_exp = "totalFailed"
    pre_exp = "totalFailed +1"
    assert run_bmc(program, post_exp, pre_exp) == False

def test_geo():
    #// ARGS: --post c --pre "c+0.999999999999" --checker both
    program = geo
    post_exp = "c"
    pre_exp = "c+0.999999999999"
    assert run_bmc(program, post_exp, pre_exp) == False

    program = geo
    post_exp = "c"
    pre_exp = "c+0.99"
    assert run_bmc(program, post_exp, pre_exp) == False


def test_rabin():
    # // ARGS: --post "[i=1]" --pre "[1<i & phase=0] * (1/3) + [not (1<i & phase=0)]*1" --checker both
    program = rabin
    post_exp = "[i=1]"
    pre_exp = "[1<i & phase=0] * (1/3) + [not (1<i & phase=0)]*1"
    assert run_bmc(program, post_exp, pre_exp) == False

    # // ARGS: --post "[i=1]" --pre "[1<i & phase=0] * (0.6) + [not (1<i & phase=0)]*1" --checker both
    program = rabin
    post_exp = "[i=1]"
    pre_exp = "[1<i & phase=0] * (0.6) + [not (1<i & phase=0)]*1"
    assert run_bmc(program, post_exp, pre_exp) == False



