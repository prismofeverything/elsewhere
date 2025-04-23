
from typing import Any, Callable, Tuple, List

import pytest

from effectful.ops.syntax import Operation, Term
from effectful.ops.semantics import handler, typeof

from elsewhere.effects import EffectSignature
from elsewhere.runners import RunnerDict


# =============================================================================


@pytest.fixture(scope="session")
def sig_syntax() -> Callable:
  """
  Provides a function to test the syntactic consistency of an effect signature.
  """
  def test(sig: EffectSignature, num_ops: int) -> None:

    # check types
    assert issubclass(sig, EffectSignature)
    ops = sig.as_dict()
    assert all(isinstance(symb, str) and isinstance(op, Operation)
               for (symb, op) in ops.items())

    # check size
    assert num_ops == len(ops)

  return test


# =============================================================================


@pytest.fixture(scope="session")
def op_semantics() -> Callable:
  """
  Provides a function to test the intended semantics of an atomic effect.
  """
  def test(
    op_stx: Operation, op_sem: Callable, runner: RunnerDict, *,
    eq: Callable[[Any, Any], bool],
    args_stx: List[Tuple], args_sem: List[Tuple], args_fail: List[Tuple]
  ) -> None:

    # check types
    assert isinstance(op_stx, Operation)
    assert all(isinstance(eff, Operation) and isinstance(coeff, Callable)
               for (eff, coeff) in runner.items())

    tp_stx = []
    for a_stx in args_stx:
      r_stx = op_stx(*a_stx)
      # in absence of a runner, fall back to constructing an effect term
      assert isinstance(r_stx, Term)
      # compute static result type
      tp_stx.append(typeof(r_stx))

    with handler(runner):
      # when given invalid arguments, fall back to constructing an effect term
      for a_fail in args_fail:
        assert isinstance(op_stx(*a_fail), Term)

      # when given valid arguments, interpret effect
      for (a_stx, a_sem, t_stx) in zip(args_stx, args_sem, tp_stx):
        r_stx, r_sem = op_stx(*a_stx), op_sem(*a_sem)
        print(r_stx)
        # validate result against static type
        assert isinstance(r_stx, t_stx)
        # validate result against intended value
        assert eq(r_stx, r_sem)

  return test
