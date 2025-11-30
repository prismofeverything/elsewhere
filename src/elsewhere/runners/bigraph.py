
"""
Runners for bigraph combinator effects using the `bigraph` backend.
"""

from functools import partial

import bigraph.bigraph as bg
from effectful.ops.syntax import Operation, Term
from effectful.ops.semantics import handler, evaluate
from multipledispatch import dispatch

from ..effects.spacelike import (
  SpacelikeLocal, HorizontalLocal, VerticalLocal,
  SpacelikeGlobal, VerticalGlobal, CtxBigraph, BigraphInterface)
from .algebra import Runner, substitute


_namespace = {}
dispatch = partial(dispatch, namespace=_namespace)


# =============================================================================


class BigraphLocal(Runner):
  """
  Evaluate bare bigraph combinators.
  """

  signature = SpacelikeLocal

  @staticmethod
  def bare_equal(a: bg.Base, b: bg.Base) -> bool:
    """
    Compare two bare bigraphs, i.e., fully evaluated bigraph effects.
    """
    assert isinstance(a, bg.Base) and isinstance(b, bg.Base)
    return a.unfold() == b.unfold()


class BigraphHorizontalLocal(BigraphLocal):
  # pylint: disable=function-redefined

  signature = HorizontalLocal

  @staticmethod
  @dispatch(bg.Base, bg.Base)
  def merge(left, right) -> bg.Base:
    return bg.Merge([left, right])

  @staticmethod
  @dispatch(bg.Base, bg.Base)
  def parallel(left, right) -> bg.Base:
    return bg.Parallel([left, right])

  @staticmethod
  @dispatch(bg.Node, bg.Edge)
  def link(node, edge) -> bg.Node:
    return node.link(edge)

  @staticmethod
  @dispatch(bg.Edge, bg.Node)
  def link(edge, node) -> bg.Edge:  # noqa: F811
    edge.link(node)
    return edge


class BigraphVerticalLocal(BigraphLocal):

  signature = VerticalLocal

  @staticmethod
  @dispatch(bg.Node, bg.Base)
  def nest(node, inner) -> bg.Node:
    return node.nest(inner)


# =============================================================================


class BigraphGlobal(Runner):

  signature = SpacelikeGlobal


class BigraphVerticalGlobal(BigraphGlobal):

  signature = VerticalGlobal

  @staticmethod
  @dispatch(CtxBigraph, dict)
  def ground(prog, vals) -> bg.Base:
    # check types
    assert all(isinstance(k, str) and isinstance(v, bg.Base)
               for (k, v) in vals.items())
    # check interface arguments
    assert prog.closed
    args = prog.inner_sites | prog.inner_links
    assert set(args.keys()).issubset(vals.keys())

    with handler(BigraphLocal.as_dict()):
      # sequentially evaluate layers of bigraph terms
      env = {}
      for layer in prog.layers:
        env = substitute(layer, args, vals, env)
      return substitute({None: prog.root}, args, vals, env)[None]

  @staticmethod
  @dispatch(CtxBigraph, BigraphInterface, CtxBigraph)
  def compose(outer, interface, inner) -> CtxBigraph:
    # couple names of interfacing links (outside-in)
    def match_link(e: str) -> Operation:
      return outer.inner_links[interface.links[e]]

    # couple names of interfacing sites (inside-out)
    def match_site(s: str) -> Operation:
      return inner.outer_sites[interface.sites[s]]

    # substitute variables of interfacing links
    bound_links = {e: match_link(e)() for e in inner.outer_links.keys()}

    # substitute variables of interfacing sites
    def bind_site(s: str) -> Term[bg.Base]:
      return substitute({None: inner.bound_sites[match_site(s)]},
                        inner.outer_links, bound_links)[None]

    # evaluate linking of (internal) edges
    bound_edges = inner.bound_edges | outer.bound_edges
    bind_edges = partial(evaluate, intp=bound_edges)

    # construct composite syntax
    return CtxBigraph(
      # compose names
      f"{outer.name}*{inner.name}",
      # preserve (external) interfaces, using relative names
      {f"{inner.name}.{n}": v for (n, v) in inner.inner_sites.items()},
      {f"{inner.name}.{n}": v for (n, v) in inner.inner_links.items()},
      {f"{outer.name}.{n}": v for (n, v) in outer.outer_sites.items()},
      {f"{outer.name}.{n}": v for (n, v) in outer.outer_links.items()},
      # preserve outer effect terms
      outer.root,
      outer.bound_sites,
      # preserve linking of (internal) edges
      bound_edges,
      # preserve (internal) effect terms, binding them across interface
      [{v: bind_edges(t) for (v, t) in terms.items()}
       for terms in
       (inner.bound_terms
        + [{sv: bind_site(s) for (s, sv) in outer.inner_sites.items()}]
        + outer.bound_terms)])
