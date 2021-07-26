from kipro2.characteristic_functional import CharacteristicFunctional
from pysmt.shortcuts import get_env, Symbol, Implies, And, Not, Equals, Function, Or, GT, FunctionType
from kipro2.pysmt_extensions.simplifier import Simplifier
from kipro2.pysmt_extensions.euf_substituter import EUFMGSubstituter
from kipro2.utils.utils import *
import logging

logger = logging.getLogger("kipro2")

class FormulaGenerator():

    def __init__(self, characteristic_functional : CharacteristicFunctional, incremental_bmc, upper_bound_expectation, simplify_formulae, ert):

        self._characteristic_functional = characteristic_functional
        self._incremental_bmc = incremental_bmc
        self._bmc_formula_generator = incremental_bmc.get_formula_generator()
        self._upper_bound_dnf = self._characteristic_functional.probably_string_expectation_to_pysmt_dnf(upper_bound_expectation, ignore_conjuncts_with_infinity=False)
        self._simplify_formulae = simplify_formulae
        self._ert = ert

        # For the query, we can disregard arithmetic expressions that equal infinity since nothing is greater than infinity.
        self._upper_bound_dnf_for_k_inductive_query = self._characteristic_functional.probably_string_expectation_to_pysmt_dnf(upper_bound_expectation, ignore_conjuncts_with_infinity=True)

        self._euf_type = self._bmc_formula_generator.get_euf_type()

        # We have an uninterpreted function K_i for P_i (i=2,3,...) starting with K_2
        self._eufs = [Symbol("K_1", FunctionType(*self._euf_type))]
        self._euf_substituter = EUFMGSubstituter(get_env())
        self._simplifier = Simplifier(get_env())

        self._prepare_first_formulae()

        self._unrolling_depth = 1
        # Let I be the candidate upper bound.
        # Invariant: P_1 (from BMC) encodes Phi(Psi^{unrolling_depth -1} (I) .

    def _prepare_first_formulae(self):
        """
        Prepare formulae for checking 1-inductivity, i.e., whether Phi(I) <= I holds.
        """

        # Let I be the candidate upper bound.
        # The first goal is to generate formulae that encode P_1 = Phi(I)

        # Get P_1
        first_bmc_euf = self._bmc_formula_generator.get_eufs()[0]
        # K-inductive query involves P_1
        self._k_inductive_query = self._construct_k_inductive_query(first_bmc_euf)

        # Loop terminate formulae for P_1
        self._loop_terminated_formulae = self._bmc_formula_generator.get_loop_terminate_formulae().copy()

        # Loop execute formulae for P_2 are the same as for BMC
        self._loop_execute_formulae = self._bmc_formula_generator.get_loop_execute_formulae().copy()

        # Formulae ensuring that K_1 is the minimum of P_1 and I
        self._pointwise_minimum_formulae = set()

        arg = substitution_to_argument_tuple(self._characteristic_functional.get_pysmt_program_variables(), {})
        for (guard_P, prob_sub_tick_triple) in self._characteristic_functional.get_loop_execute_guard_and_prob_sub_pairs():
            for (guard_I, arith_I) in self._upper_bound_dnf:
                # guardP AND guard_I and P_1(sub) <= arithI   implies    K_1(sub) = P_1(sub)
                self._pointwise_minimum_formulae.add(self._simplifier.simplify(Implies(And([guard_P, guard_I, LE(Function(first_bmc_euf, arg), arith_I)]),
                                                            Equals(Function(self._eufs[0], arg), Function(first_bmc_euf, arg)))))

                self._pointwise_minimum_formulae.add(self._simplifier.simplify(
                    Implies(And([guard_P, guard_I, GT(Function(first_bmc_euf, arg), arith_I)]),
                            Equals(Function(self._eufs[0], arg), arith_I))))


        for (guard_P, arith_P) in self._characteristic_functional.get_loop_terminated_guard_and_arith_exp_pairs():
            for (guard_I, arith_I) in self._upper_bound_dnf:
                # guardP AND guard_I and P_1(sub) <= arithI   implies    K_1(sub) = P_1(sub)
                self._pointwise_minimum_formulae.add(self._simplifier.simplify(Implies(And([guard_P, guard_I, LE(arith_P, arith_I)]),
                                                            Equals(Function(self._eufs[0], arg), arith_P))))

                self._pointwise_minimum_formulae.add(
                    self._simplifier.simplify(Implies(And([guard_P, guard_I, GT(arith_P, arith_I)]),
                                                      Equals(Function(self._eufs[0], arg), arith_I))))


        # Next, wee need P_2 to encode the DNF of I ..
        second_bmc_euf = self._bmc_formula_generator.get_eufs()[1]
        self._continuation_formulae = { Implies(guard,
                           Equals(Function(second_bmc_euf, self._characteristic_functional.get_pysmt_program_variables_argument()), arith))
                           for (guard, arith) in self._upper_bound_dnf}

        # and to apply the loop_execute_substitutions
        new_continuation_formulae = set()

        for sub in self._characteristic_functional.get_loop_execute_substitutions():
             new_continuation_formulae.update(substitute_all_formulae(self._continuation_formulae, sub, self._euf_substituter, self._simplify_formulae, self._simplifier))

        self._continuation_formulae = new_continuation_formulae

        # Increment BMC unrolling depth for monus formulae
        # In contrast to BMC, we need the next level of monus/rmonus formulae since the 1-induction check already
        # involves loop execute formulae (for P_1 and P_2).
        self._first_monus_formulae = self._bmc_formula_generator.get_monus_formulae().copy()
        self._first_rmonus_formulae = self._bmc_formula_generator.get_rmonus_formulae().copy()
        self._incremental_bmc._increment_unrolling_depth(True)

        # Now P_1 (self._loop_execute_formulae + self._loop_terminated_formulae + self._continuation_formurlae) encodes Phi(I).
        # Recall that Psi_I(I) = Phi(I) min I

        logger.debug("\n" * 2)
        logger.debug("Loop terminated formulae: \n %s" % [form.serialize() for form in self._loop_terminated_formulae])
        logger.debug("Loop execute formulae: \n %s" % [form.serialize() for form in self._loop_execute_formulae])
        logger.debug("Continuation formulae: \n %s" % [form.serialize() for form in
                                                                   self._continuation_formulae])
        logger.debug("The pointwise minimum formulae are: \n %s" % [form.serialize() for form in
                                                       self._pointwise_minimum_formulae])


    def prepare_next_depth(self):
        """
        Compute formulae for checking (self._unrolling_depth + 1)-induction.
        """

        self._unrolling_depth += 1

        new_euf = Symbol("K_%s" % (len(self._eufs) + 1), FunctionType(*self._euf_type))
        self._eufs.append(new_euf)

        # Substitute the one but last BMC formula by the new K_
        sub = {self._bmc_formula_generator.get_eufs()[-2]: self._eufs[-1]}  # Do not simplify
        self._substituted_loop_execute_formulae = substitute_all_formulae(self._loop_execute_formulae, sub,
                                                                          self._euf_substituter)


        # New continuation_formulae are obtained by subsituting the one-but-last bmc euf by the last one
        # and by subsequently applying the loop execute substitutions
        new_continuation_formulae = set()
        for sub in self._characteristic_functional.get_loop_execute_substitutions():
            new_sub = sub.copy()
            new_sub[self._bmc_formula_generator.get_eufs()[-2]] = self._bmc_formula_generator.get_eufs()[-1]
            new_continuation_formulae.update(
                substitute_all_formulae(self._continuation_formulae, new_sub, self._euf_substituter,
                                        self._simplify_formulae, self._simplifier))

        self._continuation_formulae = new_continuation_formulae

        # The new continuation formulae are obtained from substituting the one-but-last-last bmc_euf by the one-but-last last bmc_euf
        # and by the one-but-last k_ind_euf by the last k_ind_euf
        new_pointwise_minimum_formulae = set()
        for sub in self._characteristic_functional.get_loop_execute_substitutions():
            new_sub = sub.copy()
            #print(self._bmc_formula_generator.get_eufs())
            new_sub[self._bmc_formula_generator.get_eufs()[-3]] = self._bmc_formula_generator.get_eufs()[-2]
            new_sub[self._eufs[-2]] = self._eufs[-1]
            #print(new_sub)
            new_pointwise_minimum_formulae.update(substitute_all_formulae(self._pointwise_minimum_formulae, new_sub, self._euf_substituter,
                                        self._simplify_formulae, self._simplifier))


        #print({form.serialize() for form in new_pointwise_minimum_formulae})

        self._pointwise_minimum_formulae = new_pointwise_minimum_formulae
        # The loop_terminate_formulae are those from BMC
        self._loop_terminated_formulae = self._bmc_formula_generator.get_loop_terminate_formulae()

        # Increment BMC unrolling depth for monus formulae and loop_execute
        self._incremental_bmc._increment_unrolling_depth(True)

        self._loop_execute_formulae = self._bmc_formula_generator.get_loop_execute_formulae()

    def get_loop_terminate_formulae(self):
        """
        Get formulae encoding Phi^..(0)[s] where s does not satisfy the loop guard.
        """
        return self._loop_terminated_formulae

    def get_loop_execute_formulae(self):
        """
        Get formulae encoding Phi^..(..)[s] where s does satisfy the loop guard.
        """
        return self._loop_execute_formulae

    def get_continuation_formulae(self):
        """
        Get formulae required for encoding the I in Phi^...(I)
        """
        return self._continuation_formulae

    def get_substituted_loop_execute_formulae(self):
        """
        Get formulae encoding Phi^..(0)[s] where s does satisfy the loop guard.
        """
        return self._substituted_loop_execute_formulae

    def get_monus_formulae(self):
        """
        Get the formulae encoding Monus.
        """
        result = self._bmc_formula_generator.get_monus_formulae().union(self._first_monus_formulae)
        self._first_monus_formulae = set()
        return result

    def get_rmonus_formulae(self):
        """
        Get the formulae encoding RMonus (for refutation/kinduction queries)
        """

        result = self._bmc_formula_generator.get_rmonus_formulae().union(self._first_rmonus_formulae)
        self._first_rmonus_formulae = set()
        return result

    def get_pointwise_minimum_formulae(self):
        """
        Get the formulae encoding I min Phi^..(I).
        """
        return self._pointwise_minimum_formulae

    def get_k_inductive_query(self):
        """
        Get the query for checking "exists s: Phi(Psi^..())[s] > I[s]"
        """
        return self._k_inductive_query

    def _construct_k_inductive_query(self, euf):
        return Or(
            [And(guard, GT(Function(euf, self._characteristic_functional._pysmt_program_variables_argument), arith))
             for (guard, arith) in self._upper_bound_dnf_for_k_inductive_query])

    def get_program_variables_non_negative_constraints(self):
        return self._bmc_formula_generator.get_program_variables_non_negative_constraints()

    def get_unrolling_depth(self):
        return self._unrolling_depth

