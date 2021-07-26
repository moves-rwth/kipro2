from pysmt.shortcuts import GE, GT, Symbol, FunctionType, REAL, INT, Equals, Ite
from kipro2.characteristic_functional import CharacteristicFunctional
from kipro2.utils.utils import *
from kipro2.pysmt_extensions.euf_substituter import EUFMGSubstituter
from kipro2.pysmt_extensions.simplifier import Simplifier
import logging

logger = logging.getLogger("kipro2")

class FormulaGenerator:
    """
    Class responsible for generating the (loop_terminate and loop_execute) formulae for incremental BMC.
    """

    def __init__(self, characteristic_functional : CharacteristicFunctional, upper_bound_expectation, simplify_formulae, ert):

        self._characteristic_functional = characteristic_functional
        self._pysmt_program_variables = self._characteristic_functional.get_pysmt_program_variables()
        self._pysmt_loop_execute_substitutions = self._characteristic_functional.get_pysmt_loop_execute_substitutions()
        self._upper_bound_dnf = self._characteristic_functional.probably_string_expectation_to_pysmt_dnf(upper_bound_expectation)
        self._simplify_formulae = simplify_formulae
        self._ert = ert

        # The uninterpreted functions are of type Int^(#program variables) -> Real

        self._euf_type = (REAL, [INT for var in self._characteristic_functional.get_pysmt_program_variables()])

        # Store the uninterpreted functions for the different unrolling depth in a list.
        # For unrolling_depth==0, we do not have an uninterpreted function
        self._eufs = []
        self._euf_substituter = EUFMGSubstituter(get_env())
        self._simplifier = Simplifier(get_env())
        # Store Real(0) for later use
        self._realzero = Real(0)
        self._new_loop_execute_formulae = None
        self._prepare_first_formulae()

    def _prepare_first_formulae(self):

        # Create the first uninterpreted function P_1.
        first_euf = Symbol("P_%s" % (len(self._eufs) + 1), FunctionType(*self._euf_type))
        self._eufs.append(first_euf)
        second_euf = Symbol("P_%s" % (len(self._eufs) + 1), FunctionType(*self._euf_type))
        self._eufs.append(second_euf)

        # P_1 is supposed to encode Phi^(unrolling_depth)(0).
        # Hence, the refutation query has to involve P_1.
        self._refute_query = self._construct_refute_query_for_euf(first_euf)

        # There are three kinds of formulae:
        # 1. loop_terminated formulae are of the form
        #           guard -> P_i(arguments) = arithmetic_expression in program variables .
        self._loop_terminated_formulae = {self._simplifier.simplify(Implies(guard, Equals(Function(first_euf, self._characteristic_functional.get_pysmt_program_variables_argument()), arith_exp)))
                        for (guard, arith_exp) in self._characteristic_functional.get_loop_terminated_guard_and_arith_exp_pairs()}

        # 2. zero_step_not_terminated_formulae are like loop_terminated formulae but they are treated separately as they
        #   need to be popped (and replaced by loop_execute formulae, see below) after every bmc iteration.
        #   Since they encode the "Phi(0)[s] = 0 if s satisfies the loop guard" case, we always have arith_exp = Real(0).
        self._zero_step_not_terminated_formulae = {self._simplifier.simplify(Implies(Not(self._characteristic_functional.get_pysmt_loop_done()),
                                                   Equals(Function(first_euf, self._characteristic_functional.get_pysmt_program_variables_argument()), self._realzero)))}

        # 3. loop_execute formulae are of the form
        #             guard -> P_i(arguments) = prob_1*P_{i-1}(arguments_1) + ... + prob_n*P_{i-1}(arguments_n)
        # We store them as triples (guard, [(prob_1, argument_1), ..., (prob_n, argument_n)], argument)
        if not self._ert:
            self._loop_execute_formulae = {self._simplifier.simplify(Implies(guard, Equals(Function(first_euf, self._characteristic_functional.get_pysmt_program_variables_argument()),
                                                                          Plus([Times(prob, Function(second_euf, substitution_to_argument_tuple(self._characteristic_functional.get_pysmt_program_variables(), sub)))
                                                                          for (prob, sub, tick) in prob_sub_pair]))))
                                           for (guard, prob_sub_pair) in self._characteristic_functional.get_loop_execute_guard_and_prob_sub_pairs()}
        else:
            self._loop_execute_formulae = {self._simplifier.simplify(Implies(guard, Equals(
                Function(first_euf, self._characteristic_functional.get_pysmt_program_variables_argument()),
                Plus([Times(prob, Plus([tick, Function(second_euf, substitution_to_argument_tuple(
                    self._characteristic_functional.get_pysmt_program_variables(), sub))]) )
                      for (prob, sub, tick) in prob_sub_pair]))))
                                           for (guard, prob_sub_pair) in
                                           self._characteristic_functional.get_loop_execute_guard_and_prob_sub_pairs()}

        # Finally, we create the formula for specifying Monus
        self._monus_formulae = {self._simplifier.simplify(Ite(LE(min_2, min_1), Equals(Function(self._characteristic_functional.monus_euf, (min_1, min_2)), Minus(min_1, min_2)),
                                    Equals(Function(self._characteristic_functional.monus_euf, (min_1, min_2)), Int(0))))
            for (min_1, min_2) in self._characteristic_functional.monus_pairs}

        self._rmonus_formulae = {self._simplifier.simplify(Ite(LE(min_2, min_1), Equals(Function(self._characteristic_functional.rmonus_euf, (min_1, min_2)), Minus(min_1, min_2)),
                                    Equals(Function(self._characteristic_functional.rmonus_euf, (min_1, min_2)), Real(0))))
            for (min_1, min_2) in self._characteristic_functional.rmonus_pairs}

        logger.debug("\n" * 2)
        logger.debug("Loop terminated formulae: \n %s" % [form.serialize() for form in self._loop_terminated_formulae])
        logger.debug("Zero step not terminated formulae: \n %s" % [form.serialize() for form in self._zero_step_not_terminated_formulae])
        logger.debug("Loop execute formulae: \n %s" % [form.serialize() for form in self._loop_execute_formulae])
        logger.debug("Monus Formulae: \n %s" % [form.serialize() for form in self._monus_formulae])

    def get_loop_terminate_formulae(self):
        """
        Get formulae encoding Phi^..(0)[s] where s does not satisfy the loop guard.
        """
        return self._loop_terminated_formulae

    def get_loop_execute_formulae(self):
        """
        Get formulae encoding Phi^..(0)[s] where s does satisfy the loop guard.
        """
        return self._loop_execute_formulae

    def get_zero_step_not_terminated_formulae(self):
        """
        Get the formula encoding that Phi(0)[s] = 0 if s satisifes the guard.
        """
        return self._zero_step_not_terminated_formulae

    def get_monus_formulae(self):
        """
        Get the formulae encoding Monus.
        """
        return self._monus_formulae

    def get_rmonus_formulae(self):
        """
        Get the formulae encoding RMonus (for refutation/kinduction queries)
        """
        return self._rmonus_formulae

    def prepare_next_depth(self):
        #print(self._simplifier.simplify(Plus(Plus(Symbol("bla", INT), Int(1)), Int(1))))
        if self._new_loop_execute_formulae != None:
            self._loop_execute_formulae = self._new_loop_execute_formulae

        old_euf = self._eufs[-2]
        new_euf = self._eufs[-1]

        new_loop_terminated_formulae = set()
        new_zero_step_not_terminated_formulae = set()
        new_monus_formulae = set()
        new_rmonus_formulae = set()

        for sub in self._characteristic_functional.get_loop_execute_substitutions():
            sub_copy = sub.copy()
            sub_copy[old_euf] = new_euf

            new_loop_terminated_formulae.update(substitute_all_formulae(self._loop_terminated_formulae, sub_copy,
                                                                   self._euf_substituter, self._simplify_formulae, self._simplifier))
            new_zero_step_not_terminated_formulae.update(substitute_all_formulae(self._zero_step_not_terminated_formulae,
                                                                            sub_copy, self._euf_substituter, self._simplify_formulae,
                                                                            self._simplifier))
            if len(self._monus_formulae) > 0:
                new_monus_formulae.update(substitute_all_formulae(self._monus_formulae, sub_copy, self._euf_substituter, self._simplify_formulae,
                                                         self._simplifier))
            if len(self._rmonus_formulae) > 0:
                new_rmonus_formulae.update(substitute_all_formulae(self._rmonus_formulae, sub_copy, self._euf_substituter, self._simplify_formulae,
                                                         self._simplifier))

        self._loop_terminated_formulae = new_loop_terminated_formulae
        self._zero_step_not_terminated_formulae = new_zero_step_not_terminated_formulae
        self._monus_formulae = new_monus_formulae
        self._rmonus_formulae = new_rmonus_formulae

        #TODO: Do we need to copy ?
        self._new_loop_execute_formulae = set()
        new_new_euf = Symbol("P_%s" % (len(self._eufs) + 1), FunctionType(*self._euf_type))
        self._eufs.append(new_new_euf)
        for sub in self._characteristic_functional.get_loop_execute_substitutions():
            intermediate_sub = {new_euf : new_new_euf}
            sub_copy = sub.copy()
            sub_copy[old_euf] = new_euf
            for formula in self._loop_execute_formulae:
                intermediate_formula = self._euf_substituter.substitute(formula, intermediate_sub)
                self._new_loop_execute_formulae.add(self._simplifier.simplify(self._euf_substituter.substitute(intermediate_formula, sub_copy))
                                                    if self._simplify_formulae else self._euf_substituter.substitute(intermediate_formula, sub_copy))

    def get_refute_query(self):
        return self._refute_query

    def _construct_refute_query_for_euf(self, euf):
        """
        Constructs a formula encoding the query
            exists s: Phi^(unrolling_depth)[s] > post_expectation[s]

        :param euf: The uninterpreted function encoding the current unrolling depth.
        :return: The formula encoding the query.
        """

        # TODO: Explain why this query is sound in case we encounter infinity? (unconstrained real,..)
        return Or([And(guard, GT(Function(euf, self._characteristic_functional._pysmt_program_variables_argument), arith))
                   for (guard, arith) in self._upper_bound_dnf])

    def get_program_variables_non_negative_constraints(self):
        formulae = set()
        for var in self._pysmt_program_variables:
            formulae.add(GE(var, Int(0)))
        return formulae

    def get_unrolling_depth(self):
        return len(self._eufs) - 2

    def get_euf_type(self):
        return self._euf_type

    def get_eufs(self):
        return self._eufs
