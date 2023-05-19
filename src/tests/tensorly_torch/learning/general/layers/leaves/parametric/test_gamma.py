import random
import unittest

import numpy as np
import torch

from spflow.meta.data import Scope
from spflow.meta.dispatch import DispatchContext
from spflow.torch.inference import log_likelihood
from spflow.torch.learning import (
    em,
    expectation_maximization,
    maximum_likelihood_estimation,
)
from spflow.torch.structure.spn import GammaLayer, ProductNode, SumNode


class TestNode(unittest.TestCase):
    @classmethod
    def setup_class(cls):
        torch.set_default_dtype(torch.float64)

    @classmethod
    def teardown_class(cls):
        torch.set_default_dtype(torch.float32)

    def test_mle(self):

        # set seed
        np.random.seed(0)
        random.seed(0)

        layer = GammaLayer(scope=[Scope([0]), Scope([1])])

        # simulate data
        data = np.hstack(
            [
                np.random.gamma(shape=0.3, scale=1.0 / 1.7, size=(50000, 1)),
                np.random.gamma(shape=1.9, scale=1.0 / 0.7, size=(50000, 1)),
            ]
        )

        # perform MLE
        maximum_likelihood_estimation(layer, torch.tensor(data), bias_correction=True)

        self.assertTrue(torch.allclose(layer.alpha, torch.tensor([0.3, 1.9]), atol=1e-3, rtol=1e-2))
        self.assertTrue(torch.allclose(layer.beta, torch.tensor([1.7, 0.7]), atol=1e-3, rtol=1e-2))

    def test_mle_only_nans(self):

        layer = GammaLayer(scope=[Scope([0]), Scope([1])])

        # simulate data
        data = torch.tensor([[float("nan"), float("nan")], [float("nan"), 0.5]])

        # check if exception is raised
        self.assertRaises(
            ValueError,
            maximum_likelihood_estimation,
            layer,
            data,
            nan_strategy="ignore",
        )

    def test_mle_invalid_support(self):

        layer = GammaLayer(Scope([0]))

        # perform MLE (should raise exceptions)
        self.assertRaises(
            ValueError,
            maximum_likelihood_estimation,
            layer,
            torch.tensor([[float("inf")]]),
            bias_correction=True,
        )
        self.assertRaises(
            ValueError,
            maximum_likelihood_estimation,
            layer,
            torch.tensor([[-0.1]]),
            bias_correction=True,
        )

    def test_mle_nan_strategy_none(self):

        layer = GammaLayer(Scope([0]))
        self.assertRaises(
            ValueError,
            maximum_likelihood_estimation,
            layer,
            torch.tensor([[float("nan")], [0.1], [1.9], [0.7]]),
            nan_strategy=None,
        )

    def test_mle_nan_strategy_ignore(self):

        layer = GammaLayer(Scope([0]))
        maximum_likelihood_estimation(
            layer,
            torch.tensor([[float("nan")], [0.1], [1.9], [0.7]]),
            nan_strategy="ignore",
            bias_correction=False,
        )
        alpha_ignore, beta_ignore = layer.alpha, layer.beta

        # since gamma is estimated iteratively by scipy, just make sure it matches the estimate without nan value
        maximum_likelihood_estimation(
            layer,
            torch.tensor([[0.1], [1.9], [0.7]]),
            nan_strategy=None,
            bias_correction=False,
        )
        alpha_none, beta_none = layer.alpha, layer.beta

        self.assertTrue(torch.allclose(alpha_ignore, alpha_none))
        self.assertTrue(torch.allclose(beta_ignore, beta_none))

    def test_mle_nan_strategy_callable(self):

        layer = GammaLayer(Scope([0]))
        # should not raise an issue
        maximum_likelihood_estimation(layer, torch.tensor([[0.5], [1]]), nan_strategy=lambda x: x)

    def test_mle_nan_strategy_invalid(self):

        layer = GammaLayer(Scope([0]))
        self.assertRaises(
            ValueError,
            maximum_likelihood_estimation,
            layer,
            torch.tensor([[float("nan")], [0.1], [1.9], [0.7]]),
            nan_strategy="invalid_string",
        )
        self.assertRaises(
            ValueError,
            maximum_likelihood_estimation,
            layer,
            torch.tensor([[float("nan")], [1], [0], [1]]),
            nan_strategy=1,
        )

    def test_weighted_mle(self):

        leaf = GammaLayer([Scope([0]), Scope([1])])

        data = torch.tensor(
            np.hstack(
                [
                    np.vstack(
                        [
                            np.random.gamma(shape=1.7, scale=1.0 / 0.8, size=(10000, 1)),
                            np.random.gamma(shape=0.5, scale=1.0 / 1.4, size=(10000, 1)),
                        ]
                    ),
                    np.vstack(
                        [
                            np.random.gamma(shape=0.9, scale=1.0 / 0.3, size=(10000, 1)),
                            np.random.gamma(shape=1.3, scale=1.0 / 1.7, size=(10000, 1)),
                        ]
                    ),
                ]
            )
        )
        weights = torch.concat([torch.zeros(10000), torch.ones(10000)])

        maximum_likelihood_estimation(leaf, data, weights)

        self.assertTrue(torch.allclose(leaf.alpha, torch.tensor([0.5, 1.3]), atol=1e-3, rtol=1e-2))
        self.assertTrue(torch.allclose(leaf.beta, torch.tensor([1.4, 1.7]), atol=1e-2, rtol=1e-2))

    def test_em_step(self):

        # set seed
        torch.manual_seed(0)
        np.random.seed(0)
        random.seed(0)

        layer = GammaLayer([Scope([0]), Scope([1])])
        data = torch.tensor(
            np.hstack(
                [
                    np.random.gamma(shape=0.3, scale=1.0 / 1.7, size=(10000, 1)),
                    np.random.gamma(shape=1.4, scale=1.0 / 0.8, size=(10000, 1)),
                ]
            )
        )
        dispatch_ctx = DispatchContext()

        # compute gradients of log-likelihoods w.r.t. module log-likelihoods
        ll = log_likelihood(layer, data, dispatch_ctx=dispatch_ctx)
        ll.retain_grad()
        ll.sum().backward()

        # perform an em step
        em(layer, data, dispatch_ctx=dispatch_ctx)

        self.assertTrue(torch.allclose(layer.alpha, torch.tensor([0.3, 1.4]), atol=1e-2, rtol=1e-1))
        self.assertTrue(torch.allclose(layer.beta, torch.tensor([1.7, 0.8]), atol=1e-2, rtol=1e-1))

    def test_em_product_of_gammas(self):

        # set seed
        torch.manual_seed(0)
        np.random.seed(0)
        random.seed(0)

        layer = GammaLayer([Scope([0]), Scope([1])])
        prod_node = ProductNode([layer])

        data = torch.tensor(
            np.hstack(
                [
                    np.random.gamma(shape=0.3, scale=1.0 / 1.7, size=(15000, 1)),
                    np.random.gamma(shape=1.4, scale=1.0 / 0.8, size=(15000, 1)),
                ]
            )
        )

        expectation_maximization(prod_node, data, max_steps=10)

        self.assertTrue(torch.allclose(layer.alpha, torch.tensor([0.3, 1.4]), atol=1e-2, rtol=1e-1))
        self.assertTrue(torch.allclose(layer.beta, torch.tensor([1.7, 0.8]), atol=1e-2, rtol=1e-1))

    def test_em_sum_of_gammas(self):

        # set seed
        torch.manual_seed(0)
        np.random.seed(0)
        random.seed(0)

        layer = GammaLayer([Scope([0]), Scope([0])], alpha=[1.2, 0.6], beta=[0.5, 1.9])
        sum_node = SumNode([layer], weights=[0.5, 0.5])

        data = torch.tensor(
            np.vstack(
                [
                    np.random.gamma(shape=0.9, scale=1.0 / 1.9, size=(20000, 1)),
                    np.random.gamma(shape=1.4, scale=1.0 / 0.8, size=(20000, 1)),
                ]
            )
        )

        expectation_maximization(sum_node, data, max_steps=10)

        self.assertTrue(torch.allclose(layer.alpha, torch.tensor([1.4, 0.9]), atol=1e-2, rtol=1e-1))
        self.assertTrue(torch.allclose(layer.beta, torch.tensor([0.8, 1.9]), atol=1e-2, rtol=1e-1))


if __name__ == "__main__":
    unittest.main()