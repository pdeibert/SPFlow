import unittest

import tensorly as tl
from spflow.tensorly.utils.helper_functions import tl_allclose
from spflow.tensorly.inference import log_likelihood
from spflow.tensorly.structure.spn import ProductNode, SumNode
from spflow.meta.data import Scope
from spflow.tensorly.structure.general.nodes.leaves import Poisson
from spflow.tensorly.structure.general.layers.leaves import PoissonLayer


class TestNode(unittest.TestCase):
    def test_layer_likelihood_1(self):

        poisson_layer = PoissonLayer(scope=Scope([0]), l=[0.8, 0.3], n_nodes=2)
        s1 = SumNode(children=[poisson_layer], weights=[0.3, 0.7])

        poisson_nodes = [Poisson(Scope([0]), l=0.8), Poisson(Scope([0]), l=0.3)]
        s2 = SumNode(children=poisson_nodes, weights=[0.3, 0.7])

        data = tl.tensor([[1], [5], [3]])

        self.assertTrue(tl_allclose(log_likelihood(s1, data), log_likelihood(s2, data)))

    def test_layer_likelihood_2(self):

        poisson_layer = PoissonLayer(scope=[Scope([0]), Scope([1])], l=[0.8, 0.3])
        p1 = ProductNode(children=[poisson_layer])

        poisson_nodes = [Poisson(Scope([0]), l=0.8), Poisson(Scope([1]), l=0.3)]
        p2 = ProductNode(children=poisson_nodes)

        data = tl.tensor([[1, 6], [5, 3], [3, 7]])

        self.assertTrue(tl_allclose(log_likelihood(p1, data), log_likelihood(p2, data)))


if __name__ == "__main__":
    unittest.main()