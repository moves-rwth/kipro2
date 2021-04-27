import pytest
from pysmt.shortcuts import *

from kipro2.k_induction.incremental_k_induction import *
from kipro2.utils.statistics import Statistics
from tests.sample_programs import *

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
