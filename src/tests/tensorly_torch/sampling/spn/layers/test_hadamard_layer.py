import random
import unittest

import numpy as np
import torch

from spflow.meta.data import Scope
from spflow.meta.dispatch import SamplingContext
from spflow.torch.inference import log_likelihood
from spflow.tensorly.sampling import sample
from spflow.torch.structure.spn import Gaussian
from spflow.tensorly.structure.spn import HadamardLayer, ProductNode, SumNode

class TestNode(unittest.TestCase):
    @classmethod
    def setup_class(cls):
        torch.set_default_dtype(torch.float64)

    @classmethod
    def teardown_class(cls):
        torch.set_default_dtype(torch.float32)

    def test_hadamard_layer_sampling(self):

        # set seed
        torch.manual_seed(0)
        np.random.seed(0)
        random.seed(0)

        input_partitions = [
            [
                Gaussian(Scope([0]), mean=3.0, std=0.01),
                Gaussian(Scope([0]), mean=1.0, std=0.01),
            ],
            [
                Gaussian(Scope([1]), mean=1.0, std=0.01),
                Gaussian(Scope([1]), mean=-5.0, std=0.01),
            ],
            [Gaussian(Scope([2]), mean=10.0, std=0.01)],
        ]

        layer_spn = SumNode(
            children=[HadamardLayer(child_partitions=input_partitions)],
            weights=[0.3, 0.7],
        )

        nodes_spn = SumNode(
            children=[
                ProductNode(
                    children=[
                        input_partitions[0][i],
                        input_partitions[1][j],
                        input_partitions[2][k],
                    ]
                )
                for (i, j, k) in [[0, 0, 0], [1, 1, 0]]
            ],
            weights=[0.3, 0.7],
        )

        expected_mean = 0.3 * torch.tensor([3.0, 1.0, 10.0]) + 0.7 * torch.tensor([1.0, -5.0, 10.0])

        layer_samples = sample(layer_spn, 10000)
        nodes_samples = sample(nodes_spn, 10000)

        self.assertTrue(torch.allclose(nodes_samples.mean(axis=0), expected_mean, atol=0.01, rtol=0.1))
        self.assertTrue(
            torch.allclose(
                layer_samples.mean(axis=0),
                nodes_samples.mean(axis=0),
                atol=0.01,
                rtol=0.1,
            )
        )

        # sample from multiple outputs (with same scope)
        self.assertRaises(
            ValueError,
            sample,
            list(layer_spn.children)[0],
            1,
            sampling_ctx=SamplingContext([0], [[0, 1]]),
        )


if __name__ == "__main__":
    torch.set_default_dtype(torch.float64)
    unittest.main()