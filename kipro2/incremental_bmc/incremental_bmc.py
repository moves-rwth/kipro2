from kipro2.characteristic_functional import CharacteristicFunctional
from pysmt.shortcuts import Solver
from kipro2.incremental_bmc.formula_generator import FormulaGenerator
from pysmt.logics import QF_UFLIRA
import logging
from copy import copy
from kipro2.utils.utils import *
from kipro2.utils.statistics import *
from typing import Optional

logger = logging.getLogger("kipro2")

class IncrementalBMC:

    def __init__(self, program, post_expectation, upper_bound_expectation, statistics: Statistics, max_iterations = 500, unrollings_between_sat_checks = 1 , simplify_formulae = True, assert_refute: Optional[int] = None, ert:Optional[bool] = False):
        """

        :param var_decl: The variable declarations of the pGCL program.
        :param program: The pGCL program.
        :param post_expectation: The postexpectation.
        :param upper_bound_expectation: The candidate upper bound expectation that is to be verified or refuted.
        :param max_iterations: Maximum number of BMC iterations.
        :param unrollings_between_sat_checks: Number of unrollings between SAT checks.
        :param simplify_formulae: Whether to simplify the formulae or not. Simplification seems to speed things up.
        """

        _setup_logger("log.txt", logging.DEBUG, logging.DEBUG)
        self._max_iterations = max_iterations
        self._ert = ert

        if ert:
            logger.debug("Checking ERT ...")
        else:
            logger.debug("Checking WP ...")

        self._characteristic_functional = CharacteristicFunctional(program, post_expectation, statistics)

        self._formula_generator = FormulaGenerator(self._characteristic_functional, upper_bound_expectation, simplify_formulae, ert)

        self._statistics = statistics
        self._assert_refute = assert_refute

        logger.debug("Program, Pre- and Postexpectations are %s" % ("linear" if self._characteristic_functional.is_linear
                                                                    else "*NON*-linear"))
        if self._characteristic_functional.is_linear:
            self._solver = StatisticsSolver(statistics, name="z3", logic=QF_UFLIRA)
        else:
            self._solver = StatisticsSolver(statistics, name="z3")

        self._prepare_for_bmc()

        if unrollings_between_sat_checks < 1:
            raise Exception("There has to be at least one unrolling between two SAT checks.")
        self._unrollings_between_sat_checks = unrollings_between_sat_checks - 1
        self._unrollings_until_next_check = unrollings_between_sat_checks

    def _prepare_for_bmc(self):
        """
        Create first uninterpreted function, construct refutation query, and push first formulae.
        """
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
        # We need to push since the zero_step_not_terminated formulae will be popped in the next iteration
        # and replaced by loop_execute formulae.
        for formula in self._formula_generator.get_zero_step_not_terminated_formulae():
            self._solver.add_assertion(formula)
        self._statistics.compute_formulae_time.stop_timer()

    def apply_bmc(self) -> bool:
        """
        Run bounded model checking.

        Returns `False` for refutations, `True` otherwise.
        """

        for i in range(self._max_iterations):
            #logger.debug("\n"*5)
            #print_all_formulae(self._solver, logger.debug)
            if self._unrollings_until_next_check == 0:
                self._unrollings_until_next_check = self._unrollings_between_sat_checks
                if self.check_refute():
                    self._statistics.total_time.stop_timer()
                    print("Refute. (Unrolling_depth = %s. Number formulae = %s)" % (self._formula_generator.get_unrolling_depth(), len(self._solver.assertions)))
                    print(self._statistics)
                    self._statistics.k = self._formula_generator.get_unrolling_depth()
                    self._statistics.number_formulae = len(self._solver.assertions)
                    if self._assert_refute is not None:
                        assert self._assert_refute == self._formula_generator.get_unrolling_depth(), "Unrolling depth does not match assertion"
                    return False
            else:
                self._unrollings_until_next_check -= 1

            # add zero_step_not_terminated formulae only if we perform a sat check in the next iteration
            self._increment_unrolling_depth(True if self._unrollings_until_next_check == 0 else False)

        self._statistics.total_time.stop_timer()
        print("No refute after max_iterations = %s." % self._max_iterations)
        print(self._statistics)
        if self._assert_refute is not None:
            assert self._assert_refute == self._formula_generator.get_unrolling_depth(), "Unrolling depth does not match assertion"
        return True

    def check_refute(self):
        """
        Checks whether there is a program state s such that
                Phi^(unrolling_depth)[s] > post_expectation[s].
        :return: True iff there is a state s with Phi^(unrolling_depth)[s] > post_expectation[s].
        """
        #print_all_formulae(self._solver, logger.debug)
        logger.debug("Refutation Check. Current number of formulas: %s" % len(self._solver.assertions))
        logger.debug("Query: %s" % self._formula_generator.get_refute_query().serialize())

        # Create a new solver just for refutation checking. This avoids the use of the incremental solver
        # for the hard problem of the full refutation query, speeding up the runtime overall.
        if self._solver.is_sat(self._formula_generator.get_refute_query()):
            logger.info("SAT. Model: \n %s" % self._solver.get_model())
            return True
        else:
            return False

    def _increment_unrolling_depth(self, push_onto_solver = True):
        """
        Add all formulae for encoding Phi^(self._unrolling_depth + 1) onto the solver.
        :param push_onto_solver: Whether to add the zero_step_not_terminated formulae onto the solver or not.
        :return:
        """
        self._statistics.compute_formulae_time.start_timer()
        # Formula generator needs to generate formulae for next unrolling depth
        self._formula_generator.prepare_next_depth()

        # First pop the last zero_step_not_terminated_formula ..
        self._solver.pop()

        # now add the new loop_execute- and terminate formulae
        for formula in self._formula_generator.get_loop_execute_formulae():
            self._solver.add_assertion(formula)
        for formula in self._formula_generator.get_loop_terminate_formulae():
            self._solver.add_assertion(formula)
        for formula in self._formula_generator.get_monus_formulae():
            self._solver.add_assertion(formula)

        self._solver.push()

        if push_onto_solver:
            for formula in self._formula_generator.get_zero_step_not_terminated_formulae():
                self._solver.add_assertion(formula)

        logger.info("New depth: %s. Number formulae: %s" % (self._formula_generator.get_unrolling_depth(), len(self._solver.assertions)))
        self._statistics.compute_formulae_time.stop_timer()

    def _push_program_variables_non_negative_constraints(self):
        """
        For every program variable x, add a constraint x >= 0 to the solver and push.

        """

        for formula in self._formula_generator.get_program_variables_non_negative_constraints():
            self._solver.add_assertion(formula)
        self._solver.push()

    def get_formula_generator(self):
        return self._formula_generator

    def get_characteristic_functional(self):
        return self._characteristic_functional

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
