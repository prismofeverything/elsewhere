
elsewhere
=========

This package explores a re-interpretation of the [`process-bigraph`](
https://github.com/vivarium-collective/process-bigraph) software framework,
namely as an interpreter for a dynamically typed [algebraic effect system](
https://www.youtube.com/watch?v=3CcAxhMw0-c) over an algebraic model of
dynamical causality.


Background
----------

`process-bigraph` is a redesign of the [`Vivarium`](
https://www.youtube.com/watch?v=UGi4WBH1cv4) software framework, improving on it
in terms of compositionality and reproducibility, with an architecture that is
more explicitly an extension of Robin Milner's [bigraph](
https://www.youtube.com/watch?v=Jg5VCLb2cMo) model. Both libraries are motivated
by applications in systems biology, and facilitate the simulation of
hierarchical and heterogeneous dynamical system models that can be composed out
of equation-based and agent-based components.

This prototype implementation is based on the algebraic effect system
[`effectful`]( https://github.com/BasisResearch/effectful), and roughly follows
the terminology of [_"Runners in Action"_](
https://www.youtube.com/watch?v=1mJhiV-yGj4) (Ahman, Bauer 2020). The project
name is motivated by an analogy to [spacetime theory](
https://en.wikipedia.org/wiki/Causal_structure).
