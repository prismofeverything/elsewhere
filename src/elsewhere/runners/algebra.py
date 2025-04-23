
"""
Abstract types for runners of effect signatures.
"""

from typing import Callable, Dict, TypeVar
from importlib import import_module

from effectful.ops.syntax import Operation, Term, deffn

from ..effects import EffectSignature


# =============================================================================


T = TypeVar("T")


@staticmethod
def substitute(
  prog: Dict[Operation, Term],
  args: Dict[str, Operation], vals: Dict[str, T],
  env: Dict[Operation, T] | None = None
) -> Dict[Operation, T]:
  """
  For each `Operation` in `prog`, substitute free variables in its associated
  `Term` with arguments defined by the mappings `(args, vals)` or `env`.
  """
  if env is None:
    _args, _vals = args, vals
  else:
    _args = args | {v.__name__: v for v in env.keys()}
    _vals = vals | {v.__name__: e for (v, e) in env.items()}
  return {v: deffn(trm, **_args)(**_vals) for (v, trm) in prog.items()}


# =============================================================================


RunnerDict = Dict[Operation, Callable]


class Runner:
  """
  A runner (affine handler) for an `EffectSignature`.

  More precisely, this class is a mixin for a namespace of co-operations
  (interpretations of atomic effects), each represented as a static method.
  Subrunners can be factored out into subclasses, creating a partial order of
  runners.
  """

  signature = EffectSignature

  @classmethod
  def as_dict(cls, inheritance: bool = True) -> RunnerDict:
    """
    View this runner as a mapping from `Operation` instances to functions.

    Arguments:
    ----------
    inheritance: bool
      This argument is forwarded to `EffectSignature.as_dict()`.
    """
    assert issubclass(cls.signature, EffectSignature)
    assert cls.signature is not EffectSignature
    coops = {}
    for (symb, op) in cls.signature.as_dict(inheritance).items():
      op_func = op.__wrapped__
      sig = getattr(import_module(op_func.__module__),
                    op_func.__qualname__.split('.')[0])
      runners = [c for c in [cls] + cls.__subclasses__() if c.signature == sig]
      assert len(runners) == 1
      coops[op] = getattr(runners[0], symb)
    return coops
