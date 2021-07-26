from fractions import Fraction
from probably.pgcl.ast import *
from pysmt.shortcuts import Int, Real, TRUE, And, Not, Or, LE, LT, Plus, Minus, Times, FALSE, EqualsOrIff, Implies, ToReal, substitute, Function
from pysmt.environment import get_env
import logging
import signal
import os

try:
    import resource
except ImportError:
    print ("importing 'resource' not possible on windows. set_max_memory will fail. ")

import pickle

logger = logging.getLogger("kipro2")

# Store encountered monus expressions Monus(a,b) as pairs (a,b) to build the corrsponding formula
# if b <=a then Monus(a,b) = a -b else Monus(a,b) = 0
encountered_monus_pairs = set()
encountered_real_monus_pairs = set()


def parse_fraction(val):
    """
    If val is a string, parse it as a Fraction.
    If val is an int, parse it as a Fraction.
    If val is a Fraction, return it.
    If val is something else, throw an error.
    """
    if isinstance(val, Fraction):
        return val
    elif isinstance(val, (int, str)):
        return Fraction(val)
    else:
        raise Exception(
            'Value must be either a string, int, or Fraction. E.g. floats are not allowed to avoid precision loss.'
        )


def probably_expr_to_pysmt(expr,
                           pysmt_infinity_variable=None,
                           treat_minus_as_monus=False,
                           monus_euf=None,
                           toReal=False):
    """
    Convert a Probably expression to a pysmt expression.
    Infinity must not occur in a composed arithmetic expression.

    :param expr: The Propbably expression that is to be converted.
    :param pysmt_infinity_variable: The pysmt variable used to represent infinity.
    :param toReal: Whether variables and NatLitExpr shall be cast to Real or not.
    :param treat_minus_as_monus: Whether to repalace every expression of the form a - b by monus_euf(a,b)
    :param monus_euf: The uninterpreted function that is to be used for monus.
    :return: The resulting PySMT expression.
    """

    env = get_env()
    if isinstance(expr, BoolLitExpr):
        if expr.value == True:
            return TRUE()

        elif expr.value == False:
            return FALSE()

        else:
            raise Exception("Unkown expression value.")

    elif isinstance(expr, NatLitExpr):
        return Int(expr.value) if not toReal else Real(expr.value)

    elif isinstance(expr, FloatLitExpr):
        # This value might be infinity
        if expr.is_infinite():
            if pysmt_infinity_variable == None:
                raise Exception(
                    "If infinity occurs in an arithmetic expression, then pysmt_infinity_variable must not be none."
                )
            return pysmt_infinity_variable

        else:
            return Real(expr.to_fraction())

    elif isinstance(expr, VarExpr):
        return env.formula_manager.get_symbol(
            expr.var) if not toReal else ToReal(
                env.formula_manager.get_symbol(expr.var))

    elif isinstance(expr, TickExpr):
        if not isinstance(expr.expr, NatLitExpr):
            raise Exception(
                "Currently we allow for constants in tick(..) expressions only."
            )
        else:
            return probably_expr_to_pysmt(expr.expr, pysmt_infinity_variable,
                                          treat_minus_as_monus, monus_euf,
                                          toReal)

    elif isinstance(expr, BinopExpr):
        if expr.operator == Binop.OR:
            return Or(
                probably_expr_to_pysmt(expr.lhs, pysmt_infinity_variable,
                                       treat_minus_as_monus, monus_euf,
                                       toReal),
                probably_expr_to_pysmt(expr.rhs, pysmt_infinity_variable,
                                       treat_minus_as_monus, monus_euf,
                                       toReal))

        if expr.operator == Binop.AND:
            return And(
                probably_expr_to_pysmt(expr.lhs, pysmt_infinity_variable,
                                       treat_minus_as_monus, monus_euf,
                                       toReal),
                probably_expr_to_pysmt(expr.rhs, pysmt_infinity_variable,
                                       treat_minus_as_monus, monus_euf,
                                       toReal))

        if expr.operator == Binop.LEQ:
            return LE(
                probably_expr_to_pysmt(expr.lhs, pysmt_infinity_variable,
                                       treat_minus_as_monus, monus_euf,
                                       toReal),
                probably_expr_to_pysmt(expr.rhs, pysmt_infinity_variable,
                                       treat_minus_as_monus, monus_euf,
                                       toReal))

        if expr.operator == Binop.LE:
            return LT(
                probably_expr_to_pysmt(expr.lhs, pysmt_infinity_variable,
                                       treat_minus_as_monus, monus_euf,
                                       toReal),
                probably_expr_to_pysmt(expr.rhs, pysmt_infinity_variable,
                                       treat_minus_as_monus, monus_euf,
                                       toReal))

        if expr.operator == Binop.EQ:
            lhs = probably_expr_to_pysmt(expr.lhs, pysmt_infinity_variable,
                                         treat_minus_as_monus, monus_euf,
                                         toReal)
            rhs = probably_expr_to_pysmt(expr.rhs, pysmt_infinity_variable,
                                         treat_minus_as_monus, monus_euf,
                                         toReal)
            return EqualsOrIff(lhs, rhs)

        if expr.operator == Binop.PLUS:
            summand_1 = probably_expr_to_pysmt(expr.lhs,
                                               pysmt_infinity_variable,
                                               treat_minus_as_monus, monus_euf,
                                               toReal)
            summand_2 = probably_expr_to_pysmt(expr.rhs,
                                               pysmt_infinity_variable,
                                               treat_minus_as_monus, monus_euf,
                                               toReal)

            if summand_1 == pysmt_infinity_variable or summand_2 == pysmt_infinity_variable:
                raise Exception(
                    "Infinity must not occur in a composed arithmetic expression."
                )

            return Plus(summand_1, summand_2)

        if expr.operator == Binop.MINUS:
            min_1 = probably_expr_to_pysmt(expr.lhs, pysmt_infinity_variable,
                                           treat_minus_as_monus, monus_euf,
                                           toReal)
            min_2 = probably_expr_to_pysmt(expr.rhs, pysmt_infinity_variable,
                                           treat_minus_as_monus, monus_euf,
                                           toReal)

            if min_1 == pysmt_infinity_variable or min_2 == pysmt_infinity_variable:
                raise Exception(
                    "Infinity must not occur in a composed arithmetic expression."
                )

            # Do we have to treat minus as monus?
            if treat_minus_as_monus:
                if monus_euf == None:
                    raise Exception(
                        "If minus is to be treated as monus, then a monus_euf has to be provided."
                    )

                monus_expr = Function(monus_euf, (min_1, min_2))

                if toReal:
                    encountered_real_monus_pairs.add((min_1, min_2))
                else:
                    encountered_monus_pairs.add((min_1, min_2))

                return monus_expr
            else:
                return Minus(min_1, min_2)

        if expr.operator == Binop.TIMES:
            fac_1 = probably_expr_to_pysmt(expr.lhs, pysmt_infinity_variable,
                                           treat_minus_as_monus, monus_euf,
                                           toReal)
            fac_2 = probably_expr_to_pysmt(expr.rhs, pysmt_infinity_variable,
                                           treat_minus_as_monus, monus_euf,
                                           toReal)

            if fac_1 == pysmt_infinity_variable or fac_2 == pysmt_infinity_variable:
                raise Exception(
                    "Infinity must not occur in a composed arithmetic expression."
                )

            return Times(fac_1, fac_2)

    elif isinstance(expr, UnopExpr):
        if expr.operator == Unop.NEG:
            return Not(
                probably_expr_to_pysmt(expr.expr, pysmt_infinity_variable,
                                       treat_minus_as_monus, monus_euf,
                                       toReal))

        elif expr.operator == Unop.IVERSON:
            return probably_expr_to_pysmt(expr.expr, pysmt_infinity_variable,
                                          treat_minus_as_monus, monus_euf,
                                          toReal)

        else:
            raise Exception("Unsupported Unop Operator")

    else:
        raise Exception("Invalid expression {expr}")


def print_all_formulae(solver, where_to_print):
    for formula in solver.assertions:
        where_to_print(formula.serialize())


def substitution_to_argument_tuple(pysmt_program_variables: List, sub: Dict):
    return tuple([substitute(var, sub) for var in pysmt_program_variables])


def apply_substitution_to_argument_tuple(argument, sub):
    return tuple([substitute(arg, sub) for arg in argument])


def substitute_all_formulae(formulae,
                            sub,
                            euf_substituter,
                            simplify=False,
                            simplifier=None):
    """
    Apply the substitution sub to every formula in formulae using the euf_substituter.

    :param formulae: The set of formulae that is to be substituted.
    :param sub: The substitution that is to be applied.
    :param euf_substituter:
    :param simplify: Whether to simplify the resulting formulae using simplifier.
    """
    result = set()
    for formula in formulae:
        new_formula = simplifier.simplify(
            euf_substituter.substitute(formula, sub)) if simplify \
            else euf_substituter.substitute(formula, sub)
        result.add(new_formula)
    return result


def setup_sigint_handler():
    # When interrupted, Python handles SIGINT with a KeyboardInterruptException.
    # However, this prevents proper detection of terminated processes
    # by shells that invoked this program.
    # A shell script that invokes e.g. this program in a loop would continue
    # with the next command even though a SIGINT to this program should result
    # in termination of the shell script as well.
    #
    # One may consider this as a design flaw in Python.
    #
    # References:
    #   * https://github.com/fish-shell/fish-shell/issues/3104
    #   * https://stackoverflow.com/a/47900396
    def handle_int(signum, frame):
        signal.signal(signum, signal.SIG_DFL)
        os.kill(os.getpid(), signum)

    signal.signal(signal.SIGINT, handle_int)


def set_max_memory(memory_mb: int):
    try:
        _soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        resource.setrlimit(resource.RLIMIT_AS, (memory_mb * 1024 * 1024, hard))
    except:
        print("set_max_memory not possible on windows")


def _is_picklable(obj) -> bool:
    try:
        serialized = pickle.dumps(obj)
        pickle.loads(serialized)
    except Exception:
        return False
    return True


def picklable_exceptions(func):
    """
    If exceptions raised by this function are not picklable, wrap them safely.
    This is because otherwise the multiprocessing module crashes when not
    picklable exceptions are re-raised to the parent process.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if not _is_picklable(e):
                raise Exception(
                    f"Exception in subprocess (and the exception is not picklable):\n{e}"
                )
            else:
                raise e

    return wrapper
