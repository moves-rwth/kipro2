# TODO: Test infty, test monus
import pytest
from pysmt.shortcuts import *

from kipro2.incremental_bmc.incremental_bmc import *
from kipro2.utils.statistics import Statistics
from tests.sample_programs import *

test_instances = [
    geometric_test_1, geometric_test_2, geometric_flipping_test_1,
    geometric_monus_test_1, geometric_monus_2_test_1, geometric_monus_2_test_2,
    brp_simple_parameterized_test_1, brp_simple_parameterized_test_2,
    brp_simple_parameterized_test_3
]


@pytest.mark.parametrize("test_instance", test_instances)
def test_bmc_instances(test_instance):
    program, post_exp, upper_exp, expected_result = test_instance
    statistics = Statistics(dict())
    res = IncrementalBMC(program, post_exp, upper_exp, statistics, 50, 5,
                         True).apply_bmc()
    assert res == expected_result
    reset_env()
