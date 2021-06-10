"""
Created on May 05, 2021

@authors: Kevin Huy Nguyen, Bennet Wittelsbach

This file provides the basic components to build abstract probabilistic circuits, like SumNode, ProductNode, and LeafNode.
"""
from typing import List, Optional, Tuple, cast
from multimethod import multimethod


class Node:
    """Base class for all types of nodes in an SPN

    Attributes:
        children:
            A list of Nodes containing the children of this Node, or None.
        scope:
            A list of integers containing the scopes of this Node, or None.
    """

    scope: List[int]

    def __init__(self, children: List["Node"], scope: List[int]) -> None:
        # TODO: sollten Nodes auch IDs haben? (siehe SPFlow, z.B. fuer SPN-Ausgabe/Viz noetig)
        self.children = children
        self.scope = scope

    def __str__(self) -> str:
        return f"{type(self).__name__}: {self.scope}"

    def __repr__(self) -> str:
        return self.__str__()

    def print_treelike(self, prefix: str="") -> None:
        """
        Ad-hoc method to print structure of node and children (for debugging purposes)
        """
        print(prefix + f"{self.__class__.__name__}: {self.scope}")

        for child in self.children:
            child.print_treelike(prefix=prefix + "    ")

    def equals(self, other: "Node") -> bool:
        """
        Checks whether two objects are identical by comparing their class, scope and children (recursively).
        """
        return (
            type(self) is type(other)
            and self.scope == other.scope
            and all(map(lambda x, y: x.equals(y), self.children, other.children))
        )


class ProductNode(Node):
    """A ProductNode provides a factorization of its children, i.e. ProductNodes in SPNs have children with distinct scopes"""

    def __init__(self, children: List[Node], scope: List[int]) -> None:
        super().__init__(children=children, scope=scope)


class SumNode(Node):
    """A SumNode provides a weighted mixture of its children, i.e. SumNodes in SPNs have children with identical scopes

    Attributes:
        weights:
            A list of floats assigning a weight value to each of the SumNode's children.

    """

    def __init__(
        self, children: List[Node], scope: List[int], weights: List[float]
    ) -> None:
        super().__init__(children=children, scope=scope)
        self.weights = weights

    def equals(self, other: Node) -> bool:
        """
        Checks whether two objects are identical by comparing their class, scope, children (recursively) and weights.
        Note that weight comparison is done approximately due to numerical issues when conversion between graph representations.
        """
        from math import isclose

        if type(other) is SumNode:
            other = cast(SumNode, other)
            return (
                super().equals(other)
                and all(
                    map(
                        lambda x, y: isclose(x, y, rel_tol=1.0e-5),
                        self.weights,
                        other.weights,
                    )
                )
                and len(self.weights) == len(other.weights)
            )
        else:
            return False


class LeafNode(Node):
    """A LeafNode provides a probability distribution over the random variables in its scope"""

    def __init__(self, scope: List[int]) -> None:
        super().__init__(children=[], scope=scope)


@multimethod
def _print_node_graph(root_nodes: List[Node]) -> None:
    """Prints all unique nodes of a node graph in BFS fashion.

    Args:
        root_nodes:
            A list of Nodes that are the roots/outputs of the (perhaps multi-class) SPN.
    """
    nodes: List[Node] = list(root_nodes)
    while nodes:
        node: Node = nodes.pop(0)
        print(node)
        nodes.extend(list(set(node.children) - set(nodes)))


@multimethod  # type: ignore[no-redef]
def _print_node_graph(root_node: Node) -> None:
    """Wrapper for SPNs with single root node"""
    _print_node_graph([root_node])


@multimethod
def _get_node_counts(root_nodes: List[Node]) -> Tuple[int, int, int]:
    """Count the # of unique SumNodes, ProductNodes, LeafNodes in an SPN with arbitrarily many root nodes.

    Args:
        root_nodes:
            A list of Nodes that are the roots/outputs of the (perhaps multi-class) SPN.
    """
    nodes: List[Node] = root_nodes
    n_sumnodes = 0
    n_productnodes = 0
    n_leaves = 0

    while nodes:
        node: Node = nodes.pop(0)
        if type(node) is SumNode:
            n_sumnodes += 1
        elif type(node) is ProductNode:
            n_productnodes += 1
        elif type(node) is LeafNode:
            n_leaves += 1
        else:
            raise ValueError("Node must be SumNode, ProductNode, or LeafNode")
        nodes.extend(list(set(node.children) - set(nodes)))

    return (n_sumnodes, n_productnodes, n_leaves)


@multimethod  # type: ignore[no-redef]
def _get_node_counts(root_node: Node) -> Tuple[int, int, int]:
    """Wrapper for SPNs with single root node"""
    return _get_node_counts([root_node])