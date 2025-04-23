
import io
from contextlib import redirect_stdout
from importlib import import_module
import pydoc


# =============================================================================


def test_imports():
  """
  Check that all submodules can be imported, and that their use of
  metaprogramming is sane enough to not interfere with automatic generation of
  module documentation.
  """
  paths = ["effects", "effects.algebra", "effects.spacelike",
           "runners", "runners.algebra", "runners.bigraph"]
  with redirect_stdout(io.StringIO()):
    for p in paths:
      m = import_module(f"elsewhere.{p}")
      pydoc.help(m)
