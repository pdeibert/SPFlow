from typing import Optional, Iterable, Union
from spflow.torch.structure.spn.nodes.node import LeafNode
from spflow.meta.data.scope import Scope
from spflow.meta.dispatch.dispatch import dispatch
from spflow.meta.dispatch.dispatch_context import (
    DispatchContext,
    init_default_dispatch_context,
)
import torch
from copy import deepcopy


class DummyNode(LeafNode):
    """Dummy node class without children."""

    def __init__(self, scope: Optional[Scope] = None, loc=0.0):

        if scope is None:
            scope = Scope([0])

        self.loc = torch.tensor(loc)

        super(DummyNode, self).__init__(scope=scope)


@dispatch(memoize=True)
def marginalize(
    node: DummyNode,
    marg_rvs: Iterable[int],
    prune: bool = True,
    dispatch_ctx: Optional[DispatchContext] = None,
) -> Union[None, DummyNode]:

    # initialize dispatch context
    dispatch_ctx = init_default_dispatch_context(dispatch_ctx)

    # compute node scope (node only has single output)
    node_scope = node.scope

    mutual_rvs = set(node_scope.query).intersection(set(marg_rvs))

    # node scope is being fully marginalized
    if len(mutual_rvs) == len(node_scope.query):
        return None
    # node scope is being partially marginalized
    elif mutual_rvs:
        return DummyNode(
            Scope(
                [rv for rv in node.scope.query if rv not in marg_rvs],
                node.scope.evidence,
            )
        )
    else:
        return deepcopy(node)


class DummyLeaf(LeafNode):
    def __init__(self, scope: Optional[Scope] = None, loc=0.0):

        if scope is None:
            scope = Scope([0])

        self.loc = torch.tensor(loc)

        super(DummyLeaf, self).__init__(scope=scope)


@dispatch(memoize=True)
def log_likelihood(
    node: DummyLeaf,
    data: torch.Tensor,
    check_support: bool = True,
    dispatch_ctx: Optional[DispatchContext] = None,
) -> torch.Tensor:

    scope_data = data[:, node.scope.query]

    dist = torch.cdist(scope_data, node.loc.reshape(1, 1), p=2)

    dist[dist <= 1.0] = 1.0
    dist[dist > 1.0] = 0.0

    return dist.log()


@dispatch(memoize=True)
def em(
    node: DummyLeaf,
    data: torch.Tensor,
    check_support: bool = True,
    dispatch_ctx: Optional[DispatchContext] = None,
) -> None:

    pass