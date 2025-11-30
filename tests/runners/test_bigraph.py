
from copy import deepcopy
from operator import attrgetter, itemgetter

import pytest

import bigraph.bigraph as bg
from bigraph.parse import bigraph as big
from effectful.ops.syntax import Term, defop
from effectful.ops.semantics import coproduct, handler, evaluate

# pylint: disable=no-name-in-module
from elsewhere.effects import (
  SpacelikeLocal, CtxBigraph, BigraphInterface,
  merge, parallel, link, nest, compose, ground)
from elsewhere.runners.bigraph import (
  BigraphLocal, BigraphHorizontalLocal, BigraphVerticalLocal,
  BigraphGlobal, BigraphVerticalGlobal)


# =============================================================================


@pytest.mark.parametrize(
  "runner",
  # equivalent ways of constructing the same runner
  [BigraphLocal.as_dict(),
   coproduct(BigraphHorizontalLocal.as_dict(inheritance=False),
             BigraphVerticalLocal.as_dict(inheritance=False))],
  ids=["Spacelike", "Horizontal+Vertical"])
class TestBigraphLocal:
  """
  Check the interpretation of algebraic effects for bare bigraph combinators.
  """
  # pylint: disable=too-many-positional-arguments

  @staticmethod
  def test_signature(runner):
    """
    A runner should have the same signature as its effect algebra.
    """
    assert isinstance(runner, dict)
    ops_sig = SpacelikeLocal.as_dict().keys()
    ops_run = map(attrgetter("__name__"), runner.keys())
    assert set(ops_sig) == set(ops_run)

  # -----------------------------------------------------------

  @staticmethod
  @pytest.mark.parametrize(
    "x, y",
    [(1, 2)])
  @pytest.mark.parametrize(
    "a, b",
    [("A", "B")])
  @pytest.mark.parametrize(
    "op",
    [(merge, lambda p, q: bg.Merge([p, q])),
     (parallel, lambda p, q: bg.Parallel([p, q])),
     (nest, lambda p, q: p.nest(q))],
    ids=itemgetter(0))
  def test_op_untyped(op_semantics, runner, op, a, b, x, y):
    """
    Semantic checks for bigraph ops that do not explicitly depend on the
    `bigraph` types of their arguments.
    """
    op_stx, op_sem = op
    a_stx, b_stx = map(big, (a, b))
    a_sem, b_sem = map(deepcopy, (a_stx, b_stx))
    op_semantics(
      op_stx, op_sem, runner,
      eq=BigraphLocal.bare_equal,
      args_stx=[(a_stx, b_stx)],
      args_sem=[(a_sem, b_sem)],
      args_fail=[(a_stx, x), (y, b_stx), (x, y)])

  @staticmethod
  @pytest.mark.parametrize(
    "e, f",
    [("e", "f")])
  @pytest.mark.parametrize(
    "a, b",
    [("A", "B")])
  @pytest.mark.parametrize(
    "op",
    [(link, lambda p, q: [(p if r is None else r) for r in [p.link(q)]][0])],
    ids=itemgetter(0))
  def test_op_typed(op_semantics, runner, op, a, b, e, f):
    """
    Semantic checks for bigraph ops that do explicitly depend on the `bigraph`
    types of their arguments.
    """
    op_stx, op_sem = op
    (a_stx, b_stx), (e_stx, f_stx) = map(big, (a, b)), map(bg.Edge, (e, f))
    a_sem, b_sem, e_sem, f_sem = map(deepcopy, (a_stx, b_stx, e_stx, f_stx))
    op_semantics(
      op_stx, op_sem, runner,
      eq=BigraphLocal.bare_equal,
      args_stx=[(a_stx, e_stx), (f_stx, b_stx)],
      args_sem=[(a_sem, e_sem), (f_sem, b_sem)],
      args_fail=[(a_stx, b_stx), (b_stx, a_stx),
                 (e_stx, f_stx), (f_stx, e_stx)])


# =============================================================================


@pytest.mark.parametrize(
  "runner",
  [BigraphGlobal, BigraphVerticalGlobal])
class TestBigraphGlobal:
  """
  Check the hierarchical (categorical) composition of contextual bigraphs. This
  test case corresponds to the example `H * F = G` in [1; pp.7,8].

  [1] https://www.cl.cam.ac.uk/archive/rm135/Bigraphs-Lectures.pdf
  """
  # pylint: disable=invalid-name

  @staticmethod
  def H() -> CtxBigraph:
    """
    Outer contextual bigraph.
    """
    # nodes & edges (bigraph values)
    v0, v2, v4 = [big(f"v{i}") for i in [0, 2, 4]]
    e0, e2 = [bg.Edge(f"e{i}") for i in [0, 2]]
    # inner sites & links
    p = {n: defop(bg.Base, name=n) for n in [f"p{i}" for i in range(3)]}
    x = {n: defop(bg.Edge, name=n) for n in [f"x{i}" for i in range(2)]}
    # outer sites
    q = {n: defop(bg.Base, name=n) for n in [f"q{i}" for i in range(2)]}
    # bound sites & links
    s = {q["q0"]: nest(link(v0, e0),
                       merge(p["p0"](), nest(v2, p["p1"]()))),
         q["q1"]: nest(link(link(v4, e0), e2), p["p2"]())}
    e = {x["x0"]: lambda: e0, x["x1"]: lambda: e2}
    # root
    r = parallel(q["q0"](), q["q1"]())
    # syntax
    H = CtxBigraph("H", p, x, q, {}, r, s, e)
    print("H ="); print(H); print()
    return H

  @staticmethod
  def I() -> BigraphInterface:  # noqa: E743
    """
    Interface between F and H.
    """
    I = BigraphInterface(  # noqa: E741
      # sites: H.inner -> F.outer
      {f"p{i}": f"q{i}" for i in range(3)},
      # links: F.outer -> H.inner
      {f"y{i}": f"x{i}" for i in range(2)})
    print("I ="); print(I); print()
    return I

  @staticmethod
  def F() -> CtxBigraph:
    """
    Inner contextual bigraph.
    """
    # nodes & edges (bigraph values)
    v1, v3, v5 = [big(f"v{i}") for i in [1, 3, 5]]
    e1 = bg.Edge("e1")
    # outer sites & links
    q = {n: defop(bg.Base, name=n) for n in [f"q{i}" for i in range(3)]}
    y = {n: defop(bg.Edge, name=n) for n in [f"y{i}" for i in range(2)]}
    # bound sites
    s = {q["q0"]: link(link(v1, y["y0"]()), e1),
         q["q1"]: link(link(v3, e1), y["y1"]()),
         q["q2"]: link(v5, y["y1"]())}
    # root
    r = parallel(q["q0"](), parallel(q["q1"](), q["q2"]()))
    # syntax
    F = CtxBigraph("F", {}, {}, q, y, r, s, {})
    print("F ="); print(F); print()
    return F

  @staticmethod
  def g() -> bg.Base:
    """
    Expected composite ground bigraph.
    """
    g = big("v0{e0}.(v1{e0,e1} | v2.v3{e1,e2}) || v4{e0,e2}.v5{e2}")
    print("g ="); print(g); print()
    return g

  @classmethod
  def test_composition(cls, runner):
    # construct thunk
    hif = compose(cls.H(), cls.I(), cls.F())
    assert isinstance(hif, Term)

    with handler(runner.as_dict()):
      # execute composition of contextual bigraphs
      HIF = evaluate(hif)
      assert isinstance(HIF, CtxBigraph)
      print("HIF ="); print(HIF); print()

      # evaluate into bare bigraph
      G = ground(HIF, {})
      assert BigraphLocal.bare_equal(G, cls.g())
