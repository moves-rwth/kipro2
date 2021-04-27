from kipro2.incremental_bmc.incremental_bmc import IncrementalBMC
from kipro2.k_induction.formula_generator import FormulaGenerator
from pysmt.shortcuts import Solver
from pysmt.logics import QF_UFLIRA
from kipro2.utils.utils import *
import logging
from kipro2.utils.statistics import *
import math
from typing import Optional

logger = logging.getLogger("kipro2")

class IncrementalKInduction():

    def __init__(self, program, post_expectation, upper_bound_expectation, statistics: Statistics, max_iterations = 500, simplify_formulae = True, bmc_if_not_k_inductive = False, assert_inductive: Optional[int] = None, assert_refute: Optional[int] = None, ert:Optional[bool] = False):

        # We build our encoding for incremental k-induction encoding on top of the BMC encoding
        self._incremental_bmc = IncrementalBMC(program, post_expectation, upper_bound_expectation, statistics=Statistics(dict()), ert = ert)
        self._ert = ert
        self._characteristic_functional = self._incremental_bmc.get_characteristic_functional()
        self._formula_generator = FormulaGenerator(self._characteristic_functional, self._incremental_bmc, upper_bound_expectation, simplify_formulae, ert)
        self._bmc_if_not_k_inductive = bmc_if_not_k_inductive

        self._max_iterations = max_iterations

        logger.debug(
            "Program, Pre- and Postexpectations are %s" % ("linear" if self._characteristic_functional.is_linear
                                                           else "*NON*-linear"))
        if self._characteristic_functional.is_linear:
            self._solver = StatisticsSolver(statistics, name="z3", logic=QF_UFLIRA)
        else:
            self._solver = StatisticsSolver(statistics, name="z3")

        self._statistics = statistics

        self._assert_inductive = assert_inductive
        self._assert_refute = assert_refute

        self._prepare_for_k_induction()

    def apply_k_induction(self):

        for i in range(self._max_iterations):
            logger.debug("\n"*5)
            # print_all_formulae(self._solver, logger.debug)
            if self.is_k_inductive():
                self._statistics.total_time.stop_timer()
                print("Property is %s-inductive. (Number formulae on k-induction solver = %s)" % (self._formula_generator.get_unrolling_depth(), len(self._solver.assertions)))
                print(self._statistics)
                self._statistics.k = self._formula_generator.get_unrolling_depth()
                self._statistics.number_formulae = len(self._solver.assertions)
                if self._assert_inductive is not None:
                    assert self._assert_inductive == self._formula_generator.get_unrolling_depth(), "Unrolling depth does not match assertion"
                return True

            else:
                if self._bmc_if_not_k_inductive:
                    raise Exception("Not supported.")

                    if self._incremental_bmc.check_refute():
                        self._statistics.total_time.stop_timer()
                        print("Refute. (Unrolling_depth = %s. Number formulae on refutation solver = %s)" % (
                        self._formula_generator._bmc_formula_generator.get_unrolling_depth(), len(self._solver.assertions)))
                        print(self._statistics)
                        if self._assert_refute is not None:
                            assert self._assert_refute == self._formula_generator.get_unrolling_depth(), "Unrolling depth does not match assertion"
                        return False

            self._increment_unrolling_depth(True)

        self._statistics.total_time.stop_timer()
        print("Not k-inductive until k=%s." % self._max_iterations)
        if self._assert_inductive is not None:
            assert self._assert_inductive == self._formula_generator.get_unrolling_depth(), "Unrolling depth does not match assertion"
        return False

    def _increment_unrolling_depth(self, push_onto_solver):
        """
        Add all formulae for encoding Phi^(self._unrolling_depth + 1) onto the solver.
        :param push_onto_solver: Whether to add the zero_step_not_terminated formulae onto the solver or not.
        :return:
        """
        self._statistics.compute_formulae_time.start_timer()
        # Formula generator needs to generate formulae for next unrolling depth
        self._formula_generator.prepare_next_depth()

        # Pop the last loop_execute_formulae and continuation_formulae
        self._solver.pop()

        # Add substituted_loop_execute_formulae
        for formula in self._formula_generator.get_substituted_loop_execute_formulae():
            self._solver.add_assertion(formula)

        for formula in self._formula_generator.get_loop_terminate_formulae():
            self._solver.add_assertion(formula)

        for formula in self._formula_generator.get_monus_formulae():
            self._solver.add_assertion(formula)

        for formula in self._formula_generator.get_pointwise_minimum_formulae():
            self._solver.add_assertion(formula)

        self._solver.push()

        for formula in self._formula_generator.get_loop_execute_formulae():
            self._solver.add_assertion(formula)

        for formula in self._formula_generator.get_continuation_formulae():
            self._solver.add_assertion(formula)

        logger.info("New depth: %s. Number formulae: %s" % (
        self._formula_generator.get_unrolling_depth(), len(self._solver.assertions)))
        self._statistics.compute_formulae_time.stop_timer()

    def is_k_inductive(self):
        logger.debug("Query: %s" % self._formula_generator.get_k_inductive_query().serialize())
        if self._solver.is_sat(self._formula_generator.get_k_inductive_query()):
            logger.info("SAT. Model: \n %s" % self._solver.get_model())
            return False
        else:
            return True

    def _prepare_for_k_induction(self):

        self._statistics.compute_formulae_time.start_timer()
        # Assert that all program variables evaluate to some non_negative integer
        self._push_program_variables_non_negative_constraints()

        # Now push the loop_terminated constraints for Phi^(0). These will remain on the solver.
        for formula in self._formula_generator.get_loop_terminate_formulae():
            self._solver.add_assertion(formula)

        # Push the first monus formulae
        for formula in self._formula_generator.get_monus_formulae():
            self._solver.add_assertion(formula)

        for formula in self._formula_generator.get_rmonus_formulae():
            self._solver.add_assertion(formula)

        self._solver.push()

        #They will be popped
        for formula in self._formula_generator.get_continuation_formulae():
            self._solver.add_assertion(formula)

        # The loop execute formulae are popped because we will replace every occurrence of P_i by K_i
        for formula in self._formula_generator.get_loop_execute_formulae():
            self._solver.add_assertion(formula)

        self._statistics.compute_formulae_time.stop_timer()

    def _push_program_variables_non_negative_constraints(self):
        """
        For every program variable x, add a constraint x >= 0 to the solver and push.
        """

        for formula in self._formula_generator.get_program_variables_non_negative_constraints():
            self._solver.add_assertion(formula)
        self._solver.push()
