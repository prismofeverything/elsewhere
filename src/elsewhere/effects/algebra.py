
"""
Abstract types for value and effect syntax.
"""

from itertools import chain
from operator import itemgetter
from dataclasses import fields
from inspect import getmembers_static
from typing import _GenericAlias, Any, List, Dict, Mapping, Type

from effectful.ops.syntax import Operation, Term


# =============================================================================


class ValueSyntax:
  """
  Syntax for a user value type that is not provided by a backend.

  More precisely, this class is a mixin for a `dataclass` which will be
  instantiated by user code and dispatched on by runners.
  """

  @staticmethod
  def is_generic_type(tp: Type, orig: Type) -> bool:
    return isinstance(tp, _GenericAlias) and tp.__origin__ is orig

  # ---------------------------------------------------------------------------

  @property
  def name_fields(self) -> List[str]:
    return [f.name for f in fields(self)
            if f.type is str]

  @property
  def binding_fields(self) -> List[str]:
    return [
      f.name for f in fields(self)
      if self.is_generic_type(f.type, dict)
      or (self.is_generic_type(f.type, list)
          and self.is_generic_type(f.type.__args__[0], dict))]

  @property
  def term_fields(self) -> List[str]:
    return [f.name for f in fields(self)
            if f.type is Term]

  def __str__(self) -> str:
    i1, i2 = " " * 2, " " * 4
    descr = [f"{self.__class__.__name__}:"]
    for f in self.name_fields:
      descr.append(f"{i1}{f}: {getattr(self, f)}")
    for f in self.binding_fields:
      fd = getattr(self, f)
      if isinstance(fd, dict) and fd:
        descr.append(f"{i1}{f}:")
        descr.extend([f"{i2}{f"'{n}'" if isinstance(n, str) else n}: {v}"
                      for (n, v) in fd.items()])
      else:
        for (j, g) in enumerate(fd):
          descr.append(f"{i1}{f}[{j}]:")
          descr.extend([f"{i2}{f"'{n}'" if isinstance(n, str) else n}: {v}"
                        for (n, v) in g.items()])
    for f in self.term_fields:
      descr.extend([f"{i1}{f}:", f"{i2}{getattr(self, f)}"])
    return '\n'.join(descr)


# =============================================================================


EffectSignatureDict = Dict[str, Operation]


class EffectSignature:
  """
  Signature for an effect algebra that can be interpreted by `effectful`.

  More precisely, this class is a mixin for a namespace of operations (syntax
  for atomic effects), each represented as an `effectful.ops.syntax.Operation`
  instance. Subsignatures can be factored out into subclasses, creating a
  partial order of signatures.
  """

  @classmethod
  def as_dict(
    cls, inheritance: bool = True, ignore: List[str] | None = None
  ) -> EffectSignatureDict:
    """
    View this signature as a mapping from symbols to `Operation` instances.

    Arguments:
    ----------
    inheritance: bool
      If `True` (default), then the result includes operations in subclasses
      accessible via introspection, which represent predefined subsignatures.
      If `False`, then the result only contains operations defined locally to
      this class, which represent residual signatures.
    ignore: List[str] | None
      Optionally filter out some symbols.
    """
    assert ignore is None or all(isinstance(symb, str) for symb in ignore)

    own = getmembers_static(cls, predicate=lambda v: isinstance(v, Operation))
    if inheritance:
      ign = list(map(itemgetter(0), own)) + ([] if ignore is None else ignore)
      return dict(chain(
        own, *(c.as_dict(True, ign).items() for c in cls.__subclasses__())))
    if ignore is None:
      return dict(own)
    return {symb: op for (symb, op) in own if symb not in ignore}

  @classmethod
  def export_ops(cls, env: Mapping[str, Any]) -> None:
    """
    Export this signature to some external namespace.
    """
    env.update(cls.as_dict())
