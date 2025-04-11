from effectful.ops.syntax import defop, defdata


@defop
def nest(outer: bigraph, inner: bigraph) -> bigraph:
    raise NotImplementedError(f'nest not implemented')

@defop
def merge(left: bigraph, right: bigraph) -> bigraph:
    raise NotImplementedError(f'merge not implemented')

@defop
def parallel(left: bigraph, right: bigraph) -> bigraph:
    raise NotImplementedError(f'parallel not implemented')

@defop
def link(node: bigraph, edge: edge) -> bigraph:
    raise NotImplementedError(f'link not implemented')

