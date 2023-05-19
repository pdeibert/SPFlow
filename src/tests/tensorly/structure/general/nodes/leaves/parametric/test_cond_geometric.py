import unittest
from typing import Callable

import tensorly as tl

from spflow.tensorly.structure.autoleaf import AutoLeaf
from spflow.tensorly.structure.general.nodes.leaves import CondGeometric
from spflow.tensorly.structure.spn.nodes.product_node import marginalize
from spflow.meta.data import Scope
from spflow.meta.data.feature_context import FeatureContext
from spflow.meta.data.feature_types import FeatureTypes
from spflow.meta.dispatch.dispatch_context import DispatchContext


class TestGeometric(unittest.TestCase):
    def test_initialization(self):

        geometric = CondGeometric(Scope([0], [1]))
        self.assertTrue(geometric.cond_f is None)
        geometric = CondGeometric(Scope([0], [1]), lambda x: {"l": 0.5})
        self.assertTrue(isinstance(geometric.cond_f, Callable))

        # invalid scopes
        self.assertRaises(Exception, CondGeometric, Scope([]))
        self.assertRaises(Exception, CondGeometric, Scope([0]))
        self.assertRaises(Exception, CondGeometric, Scope([0, 1], [2]))

    def test_retrieve_params(self):

        # Valid parameters for Geometric distribution: p in (0,1]

        geometric = CondGeometric(Scope([0], [1]))

        # p = 0
        geometric.set_cond_f(lambda data: {"p": 0.0})
        self.assertRaises(
            ValueError,
            geometric.retrieve_params,
            tl.tensor([[1.0]]),
            DispatchContext(),
        )
        # p = inf and p = nan
        geometric.set_cond_f(lambda data: {"p": tl.inf})
        self.assertRaises(
            ValueError,
            geometric.retrieve_params,
            tl.tensor([[1.0]]),
            DispatchContext(),
        )
        geometric.set_cond_f(lambda data: {"p": -tl.inf})
        self.assertRaises(
            ValueError,
            geometric.retrieve_params,
            tl.tensor([[1.0]]),
            DispatchContext(),
        )
        geometric.set_cond_f(lambda data: {"p": tl.nan})
        self.assertRaises(
            ValueError,
            geometric.retrieve_params,
            tl.tensor([[1.0]]),
            DispatchContext(),
        )

    def test_accept(self):

        # discrete meta type
        self.assertTrue(CondGeometric.accepts([FeatureContext(Scope([0], [1]), [FeatureTypes.Discrete])]))

        # Geometric feature type class
        self.assertTrue(CondGeometric.accepts([FeatureContext(Scope([0], [1]), [FeatureTypes.Geometric])]))

        # Geometric feature type instance
        self.assertTrue(CondGeometric.accepts([FeatureContext(Scope([0], [1]), [FeatureTypes.Geometric(0.5)])]))

        # invalid feature type
        self.assertFalse(CondGeometric.accepts([FeatureContext(Scope([0], [1]), [FeatureTypes.Continuous])]))

        # non-conditional scope
        self.assertFalse(CondGeometric.accepts([FeatureContext(Scope([0]), [FeatureTypes.Discrete])]))

        # multivariate signature
        self.assertFalse(
            CondGeometric.accepts(
                [
                    FeatureContext(
                        Scope([0, 1], [2]),
                        [FeatureTypes.Discrete, FeatureTypes.Discrete],
                    )
                ]
            )
        )

    def test_initialization_from_signatures(self):

        CondGeometric.from_signatures([FeatureContext(Scope([0], [1]), [FeatureTypes.Discrete])])
        CondGeometric.from_signatures([FeatureContext(Scope([0], [1]), [FeatureTypes.Geometric])])
        CondGeometric.from_signatures([FeatureContext(Scope([0], [1]), [FeatureTypes.Geometric(p=0.75)])])

        # ----- invalid arguments -----

        # invalid feature type
        self.assertRaises(
            ValueError,
            CondGeometric.from_signatures,
            [FeatureContext(Scope([0], [1]), [FeatureTypes.Continuous])],
        )

        # non-conditional scope
        self.assertRaises(
            ValueError,
            CondGeometric.from_signatures,
            [FeatureContext(Scope([0]), [FeatureTypes.Discrete])],
        )

        # multivariate signature
        self.assertRaises(
            ValueError,
            CondGeometric.from_signatures,
            [
                FeatureContext(
                    Scope([0, 1], [2]),
                    [FeatureTypes.Discrete, FeatureTypes.Discrete],
                )
            ],
        )

    def test_autoleaf(self):

        # make sure leaf is registered
        self.assertTrue(AutoLeaf.is_registered(CondGeometric))

        # make sure leaf is correctly inferred
        self.assertEqual(
            CondGeometric,
            AutoLeaf.infer([FeatureContext(Scope([0], [1]), [FeatureTypes.Geometric])]),
        )

        # make sure AutoLeaf can return correctly instantiated object
        geometric = AutoLeaf([FeatureContext(Scope([0], [1]), [FeatureTypes.Geometric])])
        self.assertTrue(isinstance(geometric, CondGeometric))

    def test_structural_marginalization(self):

        geometric = CondGeometric(Scope([0], [2]), 0.5)

        self.assertTrue(marginalize(geometric, [1]) is not None)
        self.assertTrue(marginalize(geometric, [0]) is None)


if __name__ == "__main__":
    unittest.main()