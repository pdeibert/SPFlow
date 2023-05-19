import unittest

import tensorly as tl
from spflow.tensorly.utils.helper_functions import tl_allclose

from spflow.tensorly.inference import likelihood, log_likelihood
from spflow.tensorly.structure.spn import ProductNode, SumNode
from spflow.meta.data import Scope
from spflow.meta.dispatch import DispatchContext
from spflow.tensorly.structure.general.nodes.leaves import CondGamma
from spflow.tensorly.structure.general.layers.leaves import CondGammaLayer


class TestNode(unittest.TestCase):
    def test_likelihood_no_alpha(self):

        gamma = CondGammaLayer(Scope([0], [1]), cond_f=lambda data: {"beta": [1.0, 1.0]}, n_nodes=2)
        self.assertRaises(KeyError, log_likelihood, gamma, tl.tensor([[0], [1]]))

    def test_likelihood_no_beta(self):

        gamma = CondGammaLayer(
            Scope([0], [1]),
            cond_f=lambda data: {"alpha": [1.0, 1.0]},
            n_nodes=2,
        )
        self.assertRaises(KeyError, log_likelihood, gamma, tl.tensor([[0], [1]]))

    def test_likelihood_no_alpha_beta(self):

        gamma = CondGammaLayer(Scope([0], [1]), n_nodes=2)
        self.assertRaises(ValueError, log_likelihood, gamma, tl.tensor([[0], [1]]))

    def test_likelihood_module_cond_f(self):

        cond_f = lambda data: {"alpha": [1.0, 1.0], "beta": [1.0, 1.0]}

        gamma = CondGammaLayer(Scope([0], [1]), n_nodes=2, cond_f=cond_f)

        # create test inputs/outputs
        data = tl.tensor([[0.1, 0.1], [1.0, 1.0], [3.0, 3.0]])
        targets = tl.tensor([[0.904837, 0.904837], [0.367879, 0.367879], [0.0497871, 0.0497871]])

        probs = likelihood(gamma, data)
        log_probs = log_likelihood(gamma, data)

        self.assertTrue(tl_allclose(probs, tl.exp(log_probs)))
        self.assertTrue(tl_allclose(probs, targets))

    def test_likelihood_args(self):

        gamma = CondGammaLayer(Scope([0], [1]), n_nodes=2)

        dispatch_ctx = DispatchContext()
        dispatch_ctx.args[gamma] = {"alpha": [1.0, 1.0], "beta": [1.0, 1.0]}

        # create test inputs/outputs
        data = tl.tensor([[0.1, 0.1], [1.0, 1.0], [3.0, 3.0]])
        targets = tl.tensor([[0.904837, 0.904837], [0.367879, 0.367879], [0.0497871, 0.0497871]])

        probs = likelihood(gamma, data, dispatch_ctx=dispatch_ctx)
        log_probs = log_likelihood(gamma, data, dispatch_ctx=dispatch_ctx)

        self.assertTrue(tl_allclose(probs, tl.exp(log_probs)))
        self.assertTrue(tl_allclose(probs, targets))

    def test_likelihood_args_cond_f(self):

        gamma = CondGammaLayer(Scope([0], [1]), n_nodes=2)

        cond_f = lambda data: {"alpha": [1.0, 1.0], "beta": [1.0, 1.0]}

        dispatch_ctx = DispatchContext()
        dispatch_ctx.args[gamma] = {"cond_f": cond_f}

        # create test inputs/outputs
        data = tl.tensor([[0.1, 0.1], [1.0, 1.0], [3.0, 3.0]])
        targets = tl.tensor([[0.904837, 0.904837], [0.367879, 0.367879], [0.0497871, 0.0497871]])

        probs = likelihood(gamma, data, dispatch_ctx=dispatch_ctx)
        log_probs = log_likelihood(gamma, data, dispatch_ctx=dispatch_ctx)

        self.assertTrue(tl_allclose(probs, tl.exp(log_probs)))
        self.assertTrue(tl_allclose(probs, targets))

    def test_layer_likelihood_1(self):

        gamma_layer = CondGammaLayer(
            scope=Scope([0], [1]),
            cond_f=lambda data: {"alpha": [0.8, 0.3], "beta": [1.3, 0.4]},
            n_nodes=2,
        )
        s1 = SumNode(children=[gamma_layer], weights=[0.3, 0.7])

        gamma_nodes = [
            CondGamma(Scope([0], [1]), cond_f=lambda data: {"alpha": 0.8, "beta": 1.3}),
            CondGamma(Scope([0], [1]), cond_f=lambda data: {"alpha": 0.3, "beta": 0.4}),
        ]
        s2 = SumNode(children=gamma_nodes, weights=[0.3, 0.7])

        data = tl.tensor([[0.5], [1.5], [0.3]])

        self.assertTrue(tl_allclose(log_likelihood(s1, data), log_likelihood(s2, data)))

    def test_layer_likelihood_2(self):

        gamma_layer = CondGammaLayer(
            scope=[Scope([0], [2]), Scope([1], [2])],
            cond_f=lambda data: {"alpha": [0.8, 0.3], "beta": [1.3, 0.4]},
        )
        p1 = ProductNode(children=[gamma_layer])

        gamma_nodes = [
            CondGamma(Scope([0], [2]), cond_f=lambda data: {"alpha": 0.8, "beta": 1.3}),
            CondGamma(Scope([1], [2]), cond_f=lambda data: {"alpha": 0.3, "beta": 0.4}),
        ]
        p2 = ProductNode(children=gamma_nodes)

        data = tl.tensor([[0.5, 1.6], [0.1, 0.3], [0.47, 0.7]])

        self.assertTrue(tl_allclose(log_likelihood(p1, data), log_likelihood(p2, data)))


if __name__ == "__main__":
    unittest.main()