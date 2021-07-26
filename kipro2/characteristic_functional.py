"""
   Represents the wp-characteristic functional  for a given linear pgcl program while (b) { c }
   and a given linear postexpectation X.
"""

from itertools import product
from probably.pgcl.parser import parse_pgcl, parse_expectation
from probably.pgcl.wp import one_loop_wp_transformer, general_wp_transformer
from probably.pgcl.check import CheckFail
from probably.pgcl.simplify import normalize_expectation_transformer, normalize_expectation
from probably.pgcl.syntax import check_is_linear_program, check_is_one_big_loop, check_is_linear_expr
from pysmt.shortcuts import Symbol, GE, simplify, Function, Implies, Equals, ToReal, substitute, FunctionType, Solver
from pysmt.typing import BOOL, INT, REAL
from kipro2.utils.utils import *
from kipro2.utils.probably import SnfLoopExpectationTransformer, normalize_expectation_simple
from kipro2.utils.statistics import Statistics, StatisticsSolver
import logging

logger = logging.getLogger("kipro2")

class CharacteristicFunctional:


    def __init__(self, program, post_expectation, statistics: Statistics):
        """
        :param program: The program text.
        :param post_expectation: The postexpectation
        """

        logger.info("Program: \n  %s \n" % program)

        self.program = parse_pgcl(program)

        self._apply_general_wp = False
        if check_is_one_big_loop(instrs = self.program.instructions, allow_init=False) != None:
            print("The program is not one loop with loop-free body. Do you want to apply a one-big-loop transformation and proceed? [Y/N]")
            if input() == "N":
                raise Exception("The program is not one big loop with loop-free body.")

            else:
                raise Exception("Not supported.")
                self._apply_general_wp = True


        self.is_linear = check_is_linear_program(self.program) == None # During preprocessing, we invoke further
        # probably methods to check whether all expectations occurring are linear.

        # create a cached sat solver to use in the initialization
        self._sat_solver = StatisticsSolver(statistics, name="z3")

        self.declarations = self.program.variables.copy()

        # The euf for Monus is of type Int x Int -> Int
        # And casted to a real whenever necessary (see utils.probably_expr_to_pysmt)
        self.monus_euf = Symbol("Monus", FunctionType(INT, [INT, INT]))

        # We need an additional euf RMonus in case Monus occurs in an arithmetic expression outside of iverson bracket such as
        # [bla] * (a-b). Both a and b will be converted to reals such that monus_euf(to_real(a), to_real(b)) would not be well-formed.
        # However, during bmc/kinduction we do not need to generate copies f rmonus formulae since refutation/kinduction queries do not change.
        self.rmonus_euf = Symbol("RMonus", FunctionType(REAL, [REAL, REAL]))

        # Compute loop_execute and loop_terminated DNFs)
        (self._pysmt_loop_execute_dnf, self._pysmt_loop_terminated_dnf) \
            = self._summation_snf_to_pysmt_dnf(post_expectation)

        # Store all possible substitutions in a list
        # (We cannot use a set since dicts are not hashable)
        self._pysmt_loop_execute_substitutions = []
        for (_, prob_subs_ticks) in self._pysmt_loop_execute_dnf:
            for (prob, sub, tick) in prob_subs_ticks:
                self._pysmt_loop_execute_substitutions.append(sub) if sub not in self._pysmt_loop_execute_substitutions \
                    else self._pysmt_loop_execute_substitutions

        # Store encountered monus expressions Monus(a,b) as pairs (a,b) to build the corrsponding formula
        # if b <=a then Monus(a,b) = a -b else Monus(a,b) = 0
        self.monus_pairs = encountered_monus_pairs
        self.rmonus_pairs = encountered_real_monus_pairs
        logger.debug("The encountered monus (rmonus) expressions are: %s   (%s)" % (self.monus_pairs, self.rmonus_pairs))

    def get_loop_execute_substitutions(self):
        """

        :return: All pairs of the form (prob, sub), where sub is a substitution corresponding to an update of the program
        variables in the wp-characteristic functional.
        """

        return self._pysmt_loop_execute_substitutions

    def get_pysmt_loop_done(self):
        return self._pysmt_loop_done

    def _setup_variables(self):
        """
        For every program variable, add one smt variable to the pysmt environment.
        We support NatType only.
        Furthermore, we add a real-valued variable "infinity" which will be unconstrained in order to represent infinity.

        :return: A list of SMT Variables.
        """

        # We use the pysmt formula manager that keeps track of the previously created variables.
        smt_variables = list()
        for name, type in self.declarations.items():
            if type == BoolType():
                raise Exception("Variable %s is of type Bool, but <we support type Nat only.")

            elif type == NatType(bounds=None):
                smt_variables.append(Symbol(name, typename=INT))

            elif type == FloatType():
                raise Exception("Variable %s is of type Float, but we support type Nat only." % name)

            else:
                raise Exception("Unsupported Variable Type")

        self._pysmt_infinity_variable = Symbol("infinity", typename=REAL)


        return smt_variables

    def _get_pysmt_subs(self, probably_subs):
        """
        Translates a list of probably substitutions, i.e. dicts from variables to variable substitutions, to
        a list of the correpsonding PySMT variable substitutions.

        :param probably_subs: The probably variable substitutions.
        :return: The PySMT variable substitutions.
        """

        env = get_env()
        pysmt_subs = []
        for probably_sub in probably_subs:
            pysmt_sub = {}
            for var_name, key in probably_sub.items():
                # print(var_name,':', key)
                pysmt_sub[env.formula_manager.get_symbol(var_name)] = probably_expr_to_pysmt(key, self._pysmt_infinity_variable, True, self.monus_euf)
            # print()
            pysmt_subs.append(pysmt_sub)

        return pysmt_subs

    def _get_id_substitution(self):
        """

        :return: The variable substitution that maps every variable to itself.
        """
        return {var: var for var in self._pysmt_program_variables}

    def get_pysmt_program_variables(self):
        """

        :return: Returns a list of the PySMT program variables.
        """
        return self._pysmt_program_variables

    def get_pysmt_loop_execute_substitutions(self):
        return self._pysmt_loop_execute_substitutions

    def get_loop_execute_guard_and_prob_sub_pairs(self):
        return self._pysmt_loop_execute_dnf

    def get_loop_terminated_guard_and_arith_exp_pairs(self):
        return self._pysmt_loop_terminated_dnf

    def get_pysmt_program_variables_argument(self):
        return self._pysmt_program_variables_argument

    def _summation_snf_to_pysmt_dnf(self, post_expectation):
        """

        Computes and returns a PySMT representation of the disjunctive normal form of the wp-characteristic functional
        of program w.r.t. post_expectation

        :param program: The program text.
        :param post_expectation: The postexpectation.
        :return: The PySMT representation of the disjunctive normal form (pysmt_dnf_loop_execute, pysmt_dnf_loop_terminate), where:
         pysmt_dnf_loop_execute is
         a list of pairs
         (guard, prob_sub_pairs), where prob_sub_pairs is a list of pairs (prob, variable_substitutions). Every two guards guard and guard' in this dnf
         are mutually exclusive, i.e. guard AND guard' is unsatisfiable

         pysmt_dnf_loop_terminate is
         a list of pairs
         (guard, arithmetic_expression). Every two guards guard and guard' in this dnf are mutually exclusive, i.e.
         guard AND guard' is unsatisfiable.
        """

        # parse program and variable initializations using probably

        # retrieve the wp-characteristic functional of the loop (not containing the post-expectation) from probably

        if self._apply_general_wp:
            probably_wp_transformer = general_wp_transformer(self.program)
        else:
            probably_wp_transformer = one_loop_wp_transformer(self.program, self.program.instructions)
        probably_summation_nf = SnfLoopExpectationTransformer(self.program, probably_wp_transformer)

        #logger.info("Program weakest pre-expectation transformer: \n %s \n" % probably_wp_transformer)

        # Set-Up PySMT Variables: For every program variable, we have a corresponding pysmt variable.
        self._pysmt_program_variables = self._setup_variables()
        self._pysmt_program_variables_argument = tuple(self._pysmt_program_variables)

        # Get (guard, probability, substitution, ticks) quadruples
        probably_guards, probably_probs, probably_subs, probably_ticks = zip(*probably_summation_nf.body_tuples())

        # Convert guards and probabilities to pysmt formulae
        # Notice: We simplify the guards here as this reduces trivial conjuncts such as 2=2 that resulting from substitutions.
        # We also simplify the probabilities, e.g. 1 - 4/5   ->   1/5.
        pysmt_guards = list(map(simplify, map(lambda guard:probably_expr_to_pysmt(guard, None, True, self.monus_euf), probably_guards)))
        pysmt_probs = list(map(simplify, map(probably_expr_to_pysmt, probably_probs)))

        # A sub is a list of dicts, where every dict is a map from variables to substitutions
        pysmt_subs = self._get_pysmt_subs(probably_subs)

        pysmt_ticks = list(map(simplify, map(lambda guard:probably_expr_to_pysmt(guard, None, True, self.rmonus_euf, True), probably_ticks)))

        pysmt_summation_nf = list()
        for i in range(0, len(pysmt_guards)):
            pysmt_summation_nf.append((pysmt_guards[i], pysmt_probs[i], pysmt_subs[i], pysmt_ticks[i]))

        logger.debug("PySMT Summmation Normal Form Objects *before* preprocessing (length = %s): \n %s \n" % (
            len(pysmt_summation_nf), pysmt_summation_nf))

        pysmt_summation_nf = self._remove_unsatisfiable_guards(pysmt_summation_nf)

        logger.debug("PySMT Summmation Normal Form Objects *after* preprocessing (length = %s): \n %s \n" % (
            len(pysmt_summation_nf), pysmt_summation_nf))

        # Constraint asserting that all program variables are non-negative
        self.non_negative_constraint = And(GE(var, Int(0)) for var in self._pysmt_program_variables)

        pysmt_dnf_loop_execute = self._get_pysmt_dnf_loop_execute(pysmt_summation_nf)

        # Now deal with (not guard)-part and postexpectation
        pysmt_dnf_loop_terminated \
            = self._get_pysmt_loop_terminated_dnf(probably_wp_transformer, post_expectation)

        return (pysmt_dnf_loop_execute, pysmt_dnf_loop_terminated)

    def _get_pysmt_dnf_loop_execute(self, pysmt_summation_nf):
        """
        Computes the execute-loop-part of the wp-characteristic functional in PySMT disjunctive normal form

        :param pysmt_summation_nf: The wp-characteristic functional in summation normal form.
        :return: The PySMT dnf of the execute-loop-part.
        """

        pysmt_dnf_loop_execute = []

        for bin_seq in product([True, False], repeat=len(pysmt_summation_nf)):
            guard_seq, prob_seq, sub_seq, tick_seq = zip(*list(map(self._construct_guard_prob_tick_triple, bin_seq, pysmt_summation_nf)))
            conjuncted_B = And(guard_seq)
            to_test = And(guard_seq + (self.non_negative_constraint,))
            # We only want to add them, if they are satisfiable
            if self._sat_solver.is_sat(to_test):
                prob_sub_tick_list = [(prob_seq[i], sub_seq[i], tick_seq[i]) for i in range(0, len(prob_seq)) if
                                 not prob_seq[i] == Real(0)]

                # if the prob_sub_list is empty, then this entry of the dnf corresponds to the (not guard) part of
                # the wp-characteristic functional. Omit this part in the loop_execute part.
                if len(prob_sub_tick_list) != 0:
                    pysmt_dnf_loop_execute.append((simplify(conjuncted_B),
                                                   prob_sub_tick_list))

        logger.info("PySMT Disjunctive NF (length = %s): \n %s \n" % (
            len(pysmt_dnf_loop_execute),
            [(guard.serialize(), prob_subs_ticks) for (guard, prob_subs_ticks) in pysmt_dnf_loop_execute]))

        return pysmt_dnf_loop_execute

    def _get_pysmt_loop_terminated_dnf(self, probably_summation_nf: SnfLoopExpectationTransformer, post_expectation):
        """
        Computes the loop-terminated-part of the wp-characteristic functional in PySMT disjunctive normal form.

        :param initialization: The parsed variable declarations of the program.
        :param probably_summation_nf: The probably summation normal form of the wp-characteristic functional.
        :param post_expectation: The postexpectation that is to be parsed and processed.
        :return: The PySMT dnf of the execute-loop-part.
        """

        logger.info(probably_summation_nf.done)
        pysmt_loop_done = probably_expr_to_pysmt(probably_summation_nf.done, self._pysmt_infinity_variable, True, self.monus_euf)

        probably_postexpectation = parse_expectation(post_expectation)

        self.is_linear = self.is_linear and check_is_linear_expr(probably_postexpectation)==None

        flattened_postexpectation = normalize_expectation_simple(self.program, probably_postexpectation)
        if type(flattened_postexpectation) == CheckFail:
            print(flattened_postexpectation)
            raise Exception("CheckFail.")


        logger.info("Flattened Postexpectation: %s \n Loop Done Expression: %s"
                    % (flattened_postexpectation, pysmt_loop_done))

        pysmt_postexpectation_snf = [(probably_expr_to_pysmt(bool_exp, self._pysmt_infinity_variable, True, self.monus_euf),
                                      probably_expr_to_pysmt(arith_exp, self._pysmt_infinity_variable, True, self.rmonus_euf, True))
                                     for bool_exp, arith_exp in flattened_postexpectation]

        pysmt_loop_terminated_dnf = []

        for bin_seq in product([True, False], repeat=len(pysmt_postexpectation_snf)):
            guard_seq, arith_seq = zip(
                *list(map(self._construct_boolexp_arithexp_par, bin_seq, pysmt_postexpectation_snf)))
            to_test = And(guard_seq + (pysmt_loop_done, self.non_negative_constraint,))
            if self._sat_solver.is_sat(to_test):
                resulting_arith = simplify(Plus(arith_seq))
                pysmt_loop_terminated_dnf.append(
                    (simplify(And(guard_seq + (pysmt_loop_done,))), resulting_arith))

        self._pysmt_loop_done = pysmt_loop_done

        logger.info("PySMT Loop-Terminated DNF: \n %s" % (pysmt_loop_terminated_dnf))

        logger.debug("Checking that the conjunction of all guards is equivalent to True")

        return pysmt_loop_terminated_dnf

    def probably_string_expectation_to_pysmt_dnf(self, upper_bound_expectation, ignore_conjuncts_with_infinity = True):
        """
        Takes an expectation (as a String as accepted by probably) and returns its DNF, i.e. a list of the form
        [(guard_1, arith_1, ..., guard_n, arith_n)]. If ignore_conjuncts_with_infinity = False, then
        the following holds

        (1)   for all i != j, the formula guard_i AND guard_j is UNSAT, and
        (2)   guard_1 OR ... OR guard_n is equivalent to TRUE.

        :param upper_bound_expectation: The expectation whose dnf is to be computed.
        :param ignore_conjuncts_with_infinity: For the refute-queries, conjuncts with arith_exp = infinity can be ignored since nothing is greater than infinity.
        """

        probably_expectation_unnormalized = parse_expectation(upper_bound_expectation)
        if type(probably_expectation_unnormalized) == CheckFail:
            print(probably_expectation_unnormalized)
            raise Exception("CheckFail. There is a problem with the provided expectation.")

        self.is_linear = self.is_linear and check_is_linear_expr(probably_expectation_unnormalized) == None

        # Convert the expectation to summation normal form (like dnf but it is not required that the Boolean expressions partition the state space)
        probably_expectation_snf = normalize_expectation_simple(self.program, probably_expectation_unnormalized)

        logger.info(
            "Flattened Upper Bound Expectation: %s" % probably_expectation_snf)

        # Convert everything to pysmt objects. A probably expectation in snf of the form "[g_1]*a_1 + ... + [g_n]*a_n" is
        # now represented as [(g_1,a_1), ..., (g_n,a_n)]
        pysmt_expectation_snf = [(probably_expr_to_pysmt(bool_exp, self._pysmt_infinity_variable, True, self.monus_euf, False),
                                  probably_expr_to_pysmt(arith_exp, self._pysmt_infinity_variable, True, self.rmonus_euf, True))
                                     for bool_exp, arith_exp in probably_expectation_snf]


        #------------ DNF Computation ------------
        # As described in the paper: Go through all possible assignments from occurring Boolean expressions to truth values.
        pysmt_upper_bound_dnf = []

        for bin_seq in product([True, False], repeat=len(pysmt_expectation_snf)):
            guard_seq, arith_seq = zip(
                *list(map(self._construct_boolexp_arithexp_par, bin_seq, pysmt_expectation_snf)))
            to_test = And(guard_seq + (self.non_negative_constraint,))
            if self._sat_solver.is_sat(to_test):
                # If arith_seq contains infinity, then the whole arithmetic expression is to be interpreted as infinity
                # Since nothing is greater than infinity, states satisfying And(guard_seq) can be disregarded when checking ... > "given expectation".
                if not self._pysmt_infinity_variable in arith_seq or not ignore_conjuncts_with_infinity:
                    resulting_arith = simplify(Plus(arith_seq))
                    pysmt_upper_bound_dnf.append(
                        (simplify(And(guard_seq)), resulting_arith))
        # ----------------------------------------


        logger.info("Upper Bound DNF (ignore_conjuncts_with_infinity = %s): %s" % (ignore_conjuncts_with_infinity, ["(%s,%s)" % (guard.serialize(), arith.serialize()) for (guard, arith) in pysmt_upper_bound_dnf]))

        if not ignore_conjuncts_with_infinity:
            logger.debug("Checking whether the Boolean expressions occurring in the DNF partition the state space if all variables are non-negative.")
            # If this expectation is part of a pointwise-minimum-computation, then the Boolean expressions must partition the state space.
            assert(not self._sat_solver.is_sat(And([self.non_negative_constraint, Not(Or([guard for (guard, arith) in pysmt_upper_bound_dnf]))])))

        return pysmt_upper_bound_dnf

    def _construct_guard_prob_tick_triple(self, bin_val, pysmt_summation_nf_triple):
        """
        Construct the (b_i, prob_i) (resp. (not b_i, 0)) pairs.

        :param pysmt_summation_nf_triple: A triple (guard, prob, subs)
        :return: If bin_val == True, then return (guard, prob, subs). If bin_val == false, then return (not guard, 0, subs)
        """
        # might be more efficient to already simplify here, esp. if used with parallelizing
        # g = guard.substitute(sub)

        guard, prob, subs, tick = pysmt_summation_nf_triple
        return (guard, prob, subs, tick) if bin_val else (Not(guard), Real(0), subs, Real(0))

    def _construct_boolexp_arithexp_par(self, bin_val, pysmt_summation_nf_pair):
        """
        Construct the (b_i, a_i) (resp. (not b_i, 0)) pairs.

        :param pysmt_summation_nf_pair: A pair (bool_exp, arith_exp)
        :return: If bin_val == True, then return (guard, prob, subs). If bin_val == false, then return (not guard, 0, subs)
        """
        # might be more efficient to already simplify here, esp. if used with parallelizing
        # g = guard.substitute(sub)

        bool_exp, arith_exp = pysmt_summation_nf_pair
        return (bool_exp, arith_exp) if bin_val else (Not(bool_exp), Real(0))

    def _remove_unsatisfiable_guards(self, pysmt_summation_nf):
        """
        Removes all unsatisfiable guards in the summation normal form of the wp-characteristic functional.

        :param pysmt_summation_nf: The list of triples (guard, probabilities, substitions).
        :return: The list of triples (guard, probabilities, substitions) where no guard is unsatisiable.
        """

        result = list()
        for (guard, prob, subs, ticks) in pysmt_summation_nf:
            if self._sat_solver.is_sat(guard):
                result.append((guard, prob, subs, ticks))

        return result
