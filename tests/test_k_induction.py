import pytest
from pysmt.shortcuts import *

from kipro2.k_induction.incremental_k_induction import *
from kipro2.utils.statistics import Statistics
from tests.sample_programs import *

from tests.programs import *


def run_kinduction(program, post_exp, pre_exp):
    statistics = Statistics(dict())
    res = IncrementalKInduction(program, post_exp, pre_exp, statistics, 30, True).apply_k_induction()
    reset_env()
    return res



test_instances = [
    brp_simple_parameterized_k_test_1, brp_simple_parameterized_k_test_2,
    brp_simple_parameterized_k_test_3, geometric_k_test_1, geometric_k_test_2
]




@pytest.mark.parametrize("test_instance", test_instances)
def test_k_induction_instances(test_instance):
    (program, post_exp, upper_exp, expected_result) = test_instance
    statistics = Statistics(dict())
    res = IncrementalKInduction(program, post_exp, upper_exp, statistics, 20,
                                True).apply_k_induction()
    assert res == expected_result
    reset_env()


def test_brp():
    #// ARGS: --post "totalFailed" --pre "[toSend <= 4]*(totalFailed + 1) + [not (toSend <= 4)]*\\infty" --checker both
    program = brp
    post_exp = "totalFailed"
    pre_exp = "[toSend <= 4]*(totalFailed + 1) + [not (toSend <= 4)]*\\infty"
    assert run_kinduction(program, post_exp, pre_exp) == True

    # // ARGS: --post "totalFailed" --pre "[toSend <= 10]*(totalFailed + 3) + [not (toSend <= 10)]*\\infty" --checker both
    program = brp
    post_exp = "totalFailed"
    pre_exp = "[toSend <= 10]*(totalFailed + 3) + [not (toSend <= 10)]*\\infty"
    assert run_kinduction(program, post_exp, pre_exp) == True

    # // ARGS: --post "totalFailed" --pre "[toSend <= 20]*(totalFailed + 3) + [not (toSend <= 20)]*\\infty" --checker both
    program = brp
    post_exp = "totalFailed"
    pre_exp = "[toSend <= 20]*(totalFailed + 3) + [not (toSend <= 20)]*\\infty"
    assert run_kinduction(program, post_exp, pre_exp) == True


def test_geo():
    #// ARGS: --post c --pre "c+1" --checker both
    program = geo
    post_exp = "c"
    pre_exp = "c+1"
    assert run_kinduction(program, post_exp, pre_exp) == True


def test_rabin():
    #// ARGS: --post "[i=1]" --pre "[1<i & i<2 & phase=0] * (2/3) + [not (1<i & i<2 & phase=0)]*1" --checker both
    program = rabin
    post_exp = "[i=1]"
    pre_exp = "[1<i & i<2 & phase=0] * (2/3) + [not (1<i & i<2 & phase=0)]*1"
    assert run_kinduction(program, post_exp, pre_exp) == True

    # // ARGS: --post "[i=1]" --pre "[1<i & i<3 & phase=0] * (2/3) + [not (1<i & i<3 & phase=0)]*1" --checker both
    program = rabin
    post_exp = "[i=1]"
    pre_exp = "[1<i & i<3 & phase=0] * (2/3) + [not (1<i & i<3 & phase=0)]*1"
    assert run_kinduction(program, post_exp, pre_exp) == True


def test_unifgen():
    #// ARGS: --post "[c=i]" --pre "[elow+1=ehigh & n=ehigh-elow+1 & v=1 & c=0 & running=0 & (not (i < elow)) & (i <= ehigh)]*(1/2) + [not (elow+1=ehigh & n=ehigh-elow+1 & v=1 & c=0 & running=0 & (not (i < elow)) & (i <= ehigh))]*1" --checker both
    program = unif_gen
    post_exp = "[c=i]"
    pre_exp = "[elow+1=ehigh & n=ehigh-elow+1 & v=1 & c=0 & running=0 & (not (i < elow)) & (i <= ehigh)]*(1/2) + [not (elow+1=ehigh & n=ehigh-elow+1 & v=1 & c=0 & running=0 & (not (i < elow)) & (i <= ehigh))]*1"
    assert run_kinduction(program, post_exp, pre_exp) == True

    #// ARGS: --post "[c=i]" --pre "[elow+2=ehigh & n=ehigh-elow+1 & v=1 & c=0 & running=0 & (not (i < elow)) & (i <= ehigh)]*(1/3) + [not (elow+2=ehigh & n=ehigh-elow+1 & v=1 & c=0 & running=0 & (not (i < elow)) & (i <= ehigh))]*1" --checker both
    program = unif_gen
    post_exp = "[c=i]"
    pre_exp = "[elow+2=ehigh & n=ehigh-elow+1 & v=1 & c=0 & running=0 & (not (i < elow)) & (i <= ehigh)]*(1/3) + [not (elow+2=ehigh & n=ehigh-elow+1 & v=1 & c=0 & running=0 & (not (i < elow)) & (i <= ehigh))]*1"
    assert run_kinduction(program, post_exp, pre_exp) == True

    # "[elow+3=ehigh & n=ehigh-elow+1 & v=1 & c=0 & running=0 & (not (i < elow)) & (i <= ehigh)]*(1/4) + [not (elow+3=ehigh & n=ehigh-elow+1 & v=1 & c=0 & running=0 & (not (i < elow)) & (i <= ehigh))]*1" --checker both    program = unif_gen
    post_exp = "[c=i]"
    pre_exp = "[elow+3=ehigh & n=ehigh-elow+1 & v=1 & c=0 & running=0 & (not (i < elow)) & (i <= ehigh)]*(1/4) + [not (elow+3=ehigh & n=ehigh-elow+1 & v=1 & c=0 & running=0 & (not (i < elow)) & (i <= ehigh))]*1"
    assert run_kinduction(program, post_exp, pre_exp) == True

    # // ARGS: --post "[c=i]" --pre "[elow+4=ehigh & n=ehigh-elow+1 & v=1 & c=0 & running=0 & (not (i < elow)) & (i <= ehigh)]*(1/5) + [not (elow+4=ehigh & n=ehigh-elow+1 & v=1 & c=0 & running=0 & (not (i < elow)) & (i <= ehigh))]*1" --checker both    pre_exp = "[elow+3=ehigh & n=ehigh-elow+1 & v=1 & c=0 & running=0 & (not (i < elow)) & (i <= ehigh)]*(1/4) + [not (elow+3=ehigh & n=ehigh-elow+1 & v=1 & c=0 & running=0 & (not (i < elow)) & (i <= ehigh))]*1"
    post_exp = "[c=i]"
    pre_exp = "[elow+4=ehigh & n=ehigh-elow+1 & v=1 & c=0 & running=0 & (not (i < elow)) & (i <= ehigh)]*(1/5) + [not (elow+4=ehigh & n=ehigh-elow+1 & v=1 & c=0 & running=0 & (not (i < elow)) & (i <= ehigh))]*1"
    assert run_kinduction(program, post_exp, pre_exp) == True

