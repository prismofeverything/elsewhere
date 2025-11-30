
from elsewhere.effects.spacelike import (
  SpacelikeLocal, HorizontalLocal, VerticalLocal)


class TestSpaceLikeLocal:

  signature = SpacelikeLocal
  num_ops = 4

  @classmethod
  def test_signature(cls, sig_syntax):
    sig_syntax(cls.signature, cls.num_ops)


class TestHorizontalLocal(TestSpaceLikeLocal):

  signature = HorizontalLocal
  num_ops = 3


class TestVerticalLocal(TestSpaceLikeLocal):

  signature = VerticalLocal
  num_ops = 1
