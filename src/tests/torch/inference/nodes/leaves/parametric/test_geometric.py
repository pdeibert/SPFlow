#from spflow.base.sampling.sampling_context import SamplingContext
from spflow.meta.scope.scope import Scope
from spflow.base.structure.nodes.leaves.parametric.geometric import Geometric as BaseGeometric
from spflow.base.inference.nodes.leaves.parametric.geometric import log_likelihood
from spflow.torch.structure.nodes.leaves.parametric.geometric import Geometric, toBase, toTorch
from spflow.torch.inference.nodes.leaves.parametric.geometric import log_likelihood
from spflow.torch.inference.module import likelihood
#from spflow.torch.sampling import sample

import torch
import numpy as np

import random
import unittest


class TestGeometric(unittest.TestCase):
    @classmethod
    def setup_class(cls):
        torch.set_default_dtype(torch.float64)

    @classmethod
    def teardown_class(cls):
        torch.set_default_dtype(torch.float32)

    def test_inference(self):

        p = random.random()

        torch_geometric = Geometric(Scope([0]), p)
        node_geometric = BaseGeometric(Scope([0]), p)

        # create dummy input data (batch size x random variables)
        data = np.random.randint(1, 10, (3, 1))

        log_probs = log_likelihood(node_geometric, data)
        log_probs_torch = log_likelihood(torch_geometric, torch.tensor(data))

        # make sure that probabilities match python backend probabilities
        self.assertTrue(np.allclose(log_probs, log_probs_torch.detach().cpu().numpy()))

    def test_gradient_computation(self):

        p = random.random()

        torch_geometric = Geometric(Scope([0]), p)

        # create dummy input data (batch size x random variables)
        data = np.random.randint(1, 10, (3, 1))

        log_probs_torch = log_likelihood(torch_geometric, torch.tensor(data))

        # create dummy targets
        targets_torch = torch.ones(3, 1)

        loss = torch.nn.MSELoss()(log_probs_torch, targets_torch)
        loss.backward()

        self.assertTrue(torch_geometric.p_aux.grad is not None)

        p_aux_orig = torch_geometric.p_aux.detach().clone()

        optimizer = torch.optim.SGD(torch_geometric.parameters(), lr=1)
        optimizer.step()

        # make sure that parameters are correctly updated
        self.assertTrue(
            torch.allclose(p_aux_orig - torch_geometric.p_aux.grad, torch_geometric.p_aux)
        )

        # verify that distribution parameters match parameters
        self.assertTrue(torch.allclose(torch_geometric.p, torch_geometric.dist.probs))

    def test_gradient_optimization(self):

        torch.manual_seed(0)

        # initialize distribution
        torch_geometric = Geometric(Scope([0]), 0.3)

        # create dummy data
        p_target = 0.8
        data = torch.distributions.Geometric(p_target).sample((100000, 1)) + 1

        # initialize gradient optimizer
        optimizer = torch.optim.SGD(torch_geometric.parameters(), lr=0.9, momentum=0.6)

        # perform optimization (possibly overfitting)
        for i in range(40):

            # clear gradients
            optimizer.zero_grad()

            # compute negative log-likelihood
            nll = -log_likelihood(torch_geometric, data).mean()
            nll.backward()

            # update parameters
            optimizer.step()

        self.assertTrue(
            torch.allclose(torch_geometric.p, torch.tensor(p_target), atol=1e-3, rtol=1e-3)
        )
    
    def test_likelihood_marginalization(self):

        geometric = Geometric(Scope([0]), 0.5)
        data = torch.tensor([[float("nan")]])

        # should not raise and error and should return 1
        probs = likelihood(geometric, data)

        self.assertTrue(torch.allclose(probs, torch.tensor(1.0)))

    def test_support(self):

        # Support for Geometric distribution: integers N\{0}

        geometric = Geometric(Scope([0]), 0.5)

        # check infinite values
        self.assertRaises(ValueError, log_likelihood, geometric, torch.tensor([[float("inf")]]))
        self.assertRaises(ValueError, log_likelihood, geometric, torch.tensor([[-float("inf")]]))

        # valid integers, but outside valid range
        self.assertRaises(ValueError, log_likelihood, geometric, torch.tensor([[0.0]]))

        # valid integers within valid range
        data = torch.tensor([[1], [10]])

        probs = likelihood(geometric, data)
        log_probs = log_likelihood(geometric, data)

        self.assertTrue(all(probs != 0.0))
        self.assertTrue(torch.allclose(probs, torch.exp(log_probs)))

        # invalid floats
        self.assertRaises(
            ValueError,
            log_likelihood,
            geometric,
            torch.tensor([[torch.nextafter(torch.tensor(1.0), torch.tensor(0.0))]]),
        )
        self.assertRaises(
            ValueError,
            log_likelihood,
            geometric,
            torch.tensor([[torch.nextafter(torch.tensor(1.0), torch.tensor(2.0))]]),
        )
        self.assertRaises(ValueError, log_likelihood, geometric, torch.tensor([[1.5]]))

"""
    def test_sampling(self):

        # ----- p = 1.0 -----

        geometric = Geometric(Scope([0]), 1.0)

        data = torch.tensor([[float("nan")], [float("nan")], [float("nan")]])

        samples = sample(geometric, data, ll_cache={}, sampling_ctx=SamplingContext([0, 2]))

        self.assertTrue(all(samples.isnan() == torch.tensor([[False], [True], [False]])))
        self.assertTrue(all(samples[~samples.isnan()] == 0.0))

        # ----- p = 0.5 -----

        geometric = Geometric(Scope([0]), 0.5)

        samples = sample(geometric, 1000)
        self.assertTrue(torch.isclose(samples.mean(), torch.tensor((1.0 - 0.5) / 0.5), rtol=0.1))

        # ----- p = 0.8 -----

        geometric = Geometric(Scope([0]), 0.8)

        samples = sample(geometric, 1000)
        self.assertTrue(torch.isclose(samples.mean(), torch.tensor((1.0 - 0.8) / 0.8), rtol=0.1))
"""

if __name__ == "__main__":
    torch.set_default_dtype(torch.float64)
    unittest.main()