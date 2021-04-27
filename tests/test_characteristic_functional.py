import pytest
from pysmt.shortcuts import *

import tests.test_incremental_bmc
from kipro2.characteristic_functional import *
from tests import sample_programs


@pytest.mark.parametrize("test_instance",
                         tests.test_incremental_bmc.test_instances)
def test_characteristic_functional(test_instance):
    (program, post_exp, _, _) = test_instance
    statistics = Statistics(dict())
    CharacteristicFunctional(program, post_exp, statistics)
    reset_env()


def test_failing_infinity():
    with pytest.raises(Exception):
        program = sample_programs.geometric
        post_exp = "[c <=5]*(c + 1) + [not (c<=5)] * (\\infty * 0)"
        statistics = Statistics(dict())
        CharacteristicFunctional(program, post_exp, statistics)
        reset_env()


def test_no_failing_infinity():
    program = sample_programs.geometric
    post_exp = "[c <=5]*(c + 1) + [not (c<=5)] * (\\infty)"
    statistics = Statistics(dict())
    CharacteristicFunctional(program, post_exp, statistics)
    reset_env()
