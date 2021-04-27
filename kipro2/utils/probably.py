"""
Wraps some of Probably's APIs for ease of use.
"""
import attr
from probably.pgcl.wp import LoopExpectationTransformer
from probably.pgcl.simplify import SnfExpectationTransformer, normalize_expectation_transformer, normalize_expectation, SnfExpectationTransformerProduct
from probably.pgcl.ast import Expr, Program, TickExpr, Var, expr_str_parens
from probably.pgcl.check import CheckFail
from typing import List, Tuple, Union, Dict


@attr.s(init=False)
class SnfLoopExpectationTransformer:
    """Wrap probably's loop expectation transformer with a normalized expectation in the body."""

    body: SnfExpectationTransformer = attr.ib()
    done: Expr = attr.ib()

    def __init__(self, program: Program,
                 transformer: LoopExpectationTransformer):
        assert len(
            transformer.init) == 0, "initial assignments are not allowed"
        self.body = normalize_expectation_transformer(program,
                                                      transformer.body)
        self.done = transformer.done

    def body_tuples(
            self) -> List[Tuple[Expr, Expr, Dict[Var, Expr], TickExpr]]:
        return [(value.guard, value.prob, value.subst, value.ticks)
                for value in self.body]

    def __str__(self) -> str:
        return f"lam 𝐹. lfp 𝑋. {self.body} + {self.done} * 𝐹"


@attr.s
class SimpleNormalizedExpectation:

    _pairs: List[Tuple[Expr, Expr]] = attr.ib()

    def __repr__(self) -> str:
        return repr(self._pairs)

    def __str__(self) -> str:
        pairs = (f'[{guard}] * {expr_str_parens(prob)}'
                 for guard, prob in self._pairs)
        return f'{" + ".join(pairs)}'

    def __iter__(self):
        return iter(self._pairs)

    def __getitem__(self, index):
        return self._pairs[index]


def normalize_expectation_simple(
        program: Program,
        expr: Expr) -> Union[SimpleNormalizedExpectation, CheckFail]:
    """
    Returns the normalized expectation consisting of a guard and a probability expression.
    It is assumed no tick expressions occur in ``expr``.
    """
    normalized = normalize_expectation(program, expr)
    if isinstance(normalized, CheckFail):
        return normalized

    def unwrap_value(
            value: SnfExpectationTransformerProduct) -> Tuple[Expr, Expr]:
        assert value.subst is None
        assert value.ticks.is_zero()
        return (value.guard, value.prob)

    return SimpleNormalizedExpectation(list(map(unwrap_value, normalized)))
