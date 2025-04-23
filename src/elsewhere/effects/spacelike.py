
"""
Value and effect syntax for bigraph combinators.

Currently, the `bigraph` library serves as a provider for both:

- the value syntax for bare bigraphs,
- the carrier for bigraph runners.

This module adds:

- effect syntax for bare bigraph combinators,
- value syntax for contextual bigraphs and their interfaces,
- effect syntax for contextual bigraph combinators.
"""

from dataclasses import dataclass, field
from itertools import chain
from typing import Callable, Dict, List

import bigraph.bigraph as bg
from effectful.ops.syntax import Operation, Term, defop
from effectful.ops.semantics import fvsof

from .algebra import ValueSyntax, EffectSignature, EffectSignatureDict


# =============================================================================


class SpacelikeLocal(EffectSignature):
  """
  Effect syntax for bare bigraph combinators.
  """
  # pylint: disable=no-self-argument


class HorizontalLocal(SpacelikeLocal):

  @defop
  def merge(left: bg.Base, right: bg.Base) -> bg.Base:
    raise NotImplementedError()

  @defop
  def parallel(left: bg.Base, right: bg.Base) -> bg.Base:
    raise NotImplementedError()

  @defop
  def link(fro: bg.Node | bg.Edge, to: bg.Edge | bg.Node) -> bg.Base:
    raise NotImplementedError()


class VerticalLocal(SpacelikeLocal):

  @defop
  def nest(outer: bg.Node, inner: bg.Base) -> bg.Node:
    raise NotImplementedError()


# =============================================================================


BigraphBinding = Dict[Operation, Term[bg.Base]]


@dataclass(eq=False, slots=True)
class CtxBigraph(ValueSyntax):
  """
  Value syntax for contextual bigraphs (morphisms), which can be composed via
  bigraph interfaces (objects).

  Attributes
  ----------

  {inner,outer}_{sites,links}: EffectSignatureDict
    Internal interfaces, i.e., the loci of potential bindings between
    `CtxBigraph` and `BigraphInterface` objects, are represented as named free
    variables. This allows contextual bigraphs to be composed using variable
    substitution.

  root: Term
    This effect term represents the top-level combinator structure of a
    contextual bigraph, and uses `bound_sites` as free variables.

  bound_sites: BigraphBinding
    The content of each outer site is represented by an effect term, using as
    free variables only `inner_sites` and `{inner,outer}_links`. The term is
    associated with (but not yet bound to) the corresponding free variable in
    `outer_sites`. This representation allows bigraph interfaces to be defined
    purely in terms of effect syntax, rather than by destructuring the
    evaluation result of `root`, which would have to rely on implementation
    details of the bigraph backend.

  bound_edges: Dict[Operation, Callable[[], bg.Edge]]
    This mapping allows `{inner,outer}_links` to be linked to concrete internal
    edges, even when the former are not directly linked to a node. This
    argument will be obsolete once a local effect syntax for linking edges to
    edges is introduced.

  bound_terms: List[BigraphBinding]
    Internal effect terms of the same type as `bound_sites`, accumulated upon
    composition of `CtxBigraph` values. When grounding to a bare bigraph, such
    effect terms need to be evaluated sequentially before evaluating
    `bound_sites` and `root`.
  """
  # pylint: disable=not-an-iterable

  name: str
  inner_sites: EffectSignatureDict
  inner_links: EffectSignatureDict
  outer_sites: EffectSignatureDict
  outer_links: EffectSignatureDict
  root: Term
  bound_sites: BigraphBinding
  bound_edges: Dict[Operation, Callable[[], bg.Edge]]
  bound_terms: List[BigraphBinding] = field(default_factory=list)

  @property
  def interface_binding_fields(self) -> List[str]:
    return [f for f in self.binding_fields
            if f.startswith("inner_") or f.startswith("outer_")]

  @property
  def internal_binding_fields(self) -> List[str]:
    return [f for f in self.binding_fields
            if f.startswith("bound_")]

  @property
  def layers(self) -> List[BigraphBinding]:
    return self.bound_terms + [self.bound_sites]

  @property
  def closed(self) -> bool:
    return not self.outer_links

  def __post_init__(self):
    # check types
    for f in self.name_fields:
      assert isinstance(getattr(self, f), str)
    for f in self.interface_binding_fields:
      assert all(isinstance(k, str) and isinstance(v, Operation)
                 for (k, v) in getattr(self, f).items())
    for (b, t) in [(self.bound_sites, Term), (self.bound_edges, Callable)]:
      assert all(isinstance(k, Operation) and isinstance(v, t)
                 for (k, v) in b.items())
    for f in self.term_fields:
      assert isinstance(getattr(self, f), Term)

    # check unique names
    names = list(chain(*(getattr(self, f).keys() for f in
                         self.interface_binding_fields)))
    assert len(set(names)) == len(names)

    # check free variables
    sig = set(SpacelikeLocal.as_dict().values())
    assert set(self.outer_sites.values()).issubset(self.bound_sites.keys())
    assert (fvsof(self.root) - sig).issubset(self.bound_sites.keys())
    intf_args = set(chain(*(getattr(self, f).values()
                            for f in self.interface_binding_fields)))
    bound_args = set()
    for terms in self.layers:
      assert (fvsof(terms.values()) - sig).issubset(intf_args | bound_args)
      bound_args = set(terms.keys())


@dataclass(slots=True)
class BigraphInterface(ValueSyntax):
  """
  Value syntax for interfaces (objects) between contextual bigraphs
  (morphisms). Both the sites and the links of compatible contextual bigraphs
  are coupled by mapping between names, analogously to a module system.

  This representation is more modular than the original formalisation of
  bigraphs, where the ordering of sites and the naming of links must match
  prior to composition. Equivalently, this syntax can be seen as a compressed
  representation for compositions of permutations (bijective placings) and
  renamings (bijective substitutions).

  Attributes
  ----------

  sites, links: Dict[str, str]
    To match the implementation of composition, the site interface maps from
    outer to inner, and the link interface from inner to outer bigraphs.
  """
  sites: Dict[str, str]
  links: Dict[str, str]

  def __post_init__(self):
    # check types
    for d in [self.sites, self.links]:
      assert all(isinstance(k, str) and isinstance(v, str)
                 for (k, v) in d.items())


# =============================================================================


class SpacelikeGlobal(EffectSignature):
  """
  Effect syntax for bigraph combinators operating on entire bigraph terms.
  """


class VerticalGlobal(SpacelikeGlobal):
  # pylint: disable=no-self-argument

  @defop
  def ground(prog: CtxBigraph, args: Dict[str, bg.Base]) -> bg.Base:
    """
    Simplify a contextual bigraph to a bare bigraph, after substituting its
    inner interface with a bare bigraph.
    """
    raise NotImplementedError()

  @defop
  def compose(
    outer: CtxBigraph, interface: BigraphInterface, inner: CtxBigraph
  ) -> CtxBigraph:
    """
    Hierarchical (categorical) composition of contextual bigraphs (morphisms)
    along interfaces (objects).
    """
    raise NotImplementedError()
