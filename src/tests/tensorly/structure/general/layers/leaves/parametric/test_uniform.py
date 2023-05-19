import unittest

import tensorly as tl

from spflow.tensorly.structure import AutoLeaf
from spflow.tensorly.structure.spn import marginalize
from spflow.tensorly.structure.general.nodes.leaves import Uniform
from spflow.tensorly.structure.general.layers.leaves import UniformLayer
from spflow.tensorly.utils.helper_functions import tl_allclose
from spflow.meta.data import FeatureContext, FeatureTypes, Scope


class TestLayer(unittest.TestCase):
    def test_layer_initialization_1(self):

        # ----- check attributes after correct initialization -----

        l = UniformLayer(scope=Scope([1]), n_nodes=3, start=0.0, end=1.0)
        # make sure number of creates nodes is correct
        self.assertEqual(len(l.nodes), 3)
        # make sure scopes are correct
        self.assertTrue(tl.all(l.scopes_out == [Scope([1]), Scope([1]), Scope([1])]))
        # make sure parameter properties works correctly
        start = l.start
        for node, node_start in zip(l.nodes, start):
            self.assertTrue(tl.all(node.start == node_start))
        end = l.end
        for node, node_end in zip(l.nodes, end):
            self.assertTrue(tl.all(node.end == node_end))

        # ----- float/int parameter values -----
        start = -1.0
        end = 2

        l = UniformLayer(scope=Scope([1]), n_nodes=3, start=start, end=end)

        for node in l.nodes:
            self.assertTrue(tl.all(node.start == start))
            self.assertTrue(tl.all(node.end == end))

        # ----- list parameter values -----
        start = [-1.0, -2.0, 3.0]
        end = [2.0, -1.5, 4.0]

        l = UniformLayer(scope=Scope([1]), n_nodes=3, start=start, end=end)

        for node, node_start, node_end in zip(l.nodes, start, end):
            self.assertTrue(tl.all(node.start == node_start))
            self.assertTrue(tl.all(node.end == node_end))

        # wrong number of values
        self.assertRaises(ValueError, UniformLayer, Scope([0]), start, end[:-1], n_nodes=3)
        self.assertRaises(ValueError, UniformLayer, Scope([0]), start[:-1], end, n_nodes=3)
        # wrong number of dimensions (nested list)
        self.assertRaises(
            ValueError,
            UniformLayer,
            Scope([0]),
            [start for _ in range(3)],
            end,
            n_nodes=3,
        )
        self.assertRaises(
            ValueError,
            UniformLayer,
            Scope([0]),
            start,
            [end for _ in range(3)],
            n_nodes=3,
        )

        # ----- numpy parameter values -----

        l = UniformLayer(
            scope=Scope([1]),
            n_nodes=3,
            start=tl.tensor(start),
            end=tl.tensor(end),
        )

        for node, node_start, node_end in zip(l.nodes, start, end):
            self.assertTrue(tl.all(node.start == node_start))
            self.assertTrue(tl.all(node.end == node_end))

        # wrong number of values
        self.assertRaises(
            ValueError,
            UniformLayer,
            Scope([0]),
            tl.tensor(start[:-1]),
            tl.tensor(end),
            n_nodes=3,
        )
        self.assertRaises(
            ValueError,
            UniformLayer,
            Scope([0]),
            tl.tensor(start),
            tl.tensor(end[:-1]),
            n_nodes=3,
        )
        # wrong number of dimensions (nested list)
        self.assertRaises(
            ValueError,
            UniformLayer,
            Scope([0]),
            tl.tensor([start for _ in range(3)]),
            end,
            n_nodes=3,
        )
        self.assertRaises(
            ValueError,
            UniformLayer,
            Scope([0]),
            start,
            tl.tensor([end for _ in range(3)]),
            n_nodes=3,
        )

        # ---- different scopes -----
        l = UniformLayer(scope=Scope([1]), start=0.0, end=1.0, n_nodes=3)
        for node, node_scope in zip(l.nodes, l.scopes_out):
            self.assertEqual(node.scope, node_scope)

        # ----- invalid number of nodes -----
        self.assertRaises(ValueError, UniformLayer, Scope([0]), 0.0, 1.0, n_nodes=0)

        # ----- invalid scope -----
        self.assertRaises(ValueError, UniformLayer, Scope([]), 0.0, 1.0, n_nodes=3)
        self.assertRaises(ValueError, UniformLayer, [], 0.0, 1.0, n_nodes=3)

        # ----- individual scopes and parameters -----
        scopes = [Scope([1]), Scope([0]), Scope([0])]
        l = UniformLayer(scope=[Scope([1]), Scope([0])], start=0.0, end=1.0, n_nodes=3)
        for node, node_scope in zip(l.nodes, scopes):
            self.assertEqual(node.scope, node_scope)

    def test_accept(self):

        # discrete meta type (should reject)
        self.assertFalse(
            UniformLayer.accepts(
                [
                    FeatureContext(Scope([0]), [FeatureTypes.Continuous]),
                    FeatureContext(Scope([1]), [FeatureTypes.Continuous]),
                ]
            )
        )

        # Uniform feature type instance
        self.assertTrue(
            UniformLayer.accepts(
                [
                    FeatureContext(Scope([0]), [FeatureTypes.Uniform(start=-1.0, end=2.0)]),
                    FeatureContext(Scope([1]), [FeatureTypes.Uniform(start=1.0, end=3.0)]),
                ]
            )
        )

        # invalid feature type
        self.assertFalse(
            UniformLayer.accepts(
                [
                    FeatureContext(Scope([0]), [FeatureTypes.Discrete]),
                    FeatureContext(Scope([1]), [FeatureTypes.Uniform(-1.0, 2.0)]),
                ]
            )
        )

        # conditional scope
        self.assertFalse(
            UniformLayer.accepts(
                [
                    FeatureContext(
                        Scope([0], [1]),
                        [FeatureTypes.Uniform(start=-1.0, end=2.0)],
                    )
                ]
            )
        )

        # multivariate signature
        self.assertFalse(
            UniformLayer.accepts(
                [
                    FeatureContext(
                        Scope([0, 1]),
                        [
                            FeatureTypes.Uniform(start=-1.0, end=2.0),
                            FeatureTypes.Uniform(start=-1.0, end=2.0),
                        ],
                    )
                ]
            )
        )

    def test_initialization_from_signatures(self):

        uniform = UniformLayer.from_signatures(
            [
                FeatureContext(Scope([0]), [FeatureTypes.Uniform(start=-1.0, end=2.0)]),
                FeatureContext(Scope([1]), [FeatureTypes.Uniform(start=1.0, end=3.0)]),
            ]
        )
        self.assertTrue(tl.all(uniform.start == tl.tensor([-1.0, 1.0])))
        self.assertTrue(tl.all(uniform.end == tl.tensor([2.0, 3.0])))
        self.assertTrue(uniform.scopes_out == [Scope([0]), Scope([1])])

        # ----- invalid arguments -----

        # discrete meta type
        self.assertRaises(
            ValueError,
            UniformLayer.from_signatures,
            [FeatureContext(Scope([0]), [FeatureTypes.Continuous])],
        )

        # invalid feature type
        self.assertRaises(
            ValueError,
            UniformLayer.from_signatures,
            [FeatureContext(Scope([0]), [FeatureTypes.Discrete])],
        )

        # conditional scope
        self.assertRaises(
            ValueError,
            UniformLayer.from_signatures,
            [FeatureContext(Scope([0], [1]), [FeatureTypes.Continuous])],
        )

        # multivariate signature
        self.assertRaises(
            ValueError,
            UniformLayer.from_signatures,
            [
                FeatureContext(
                    Scope([0, 1]),
                    [FeatureTypes.Continuous, FeatureTypes.Continuous],
                )
            ],
        )

    def test_autoleaf(self):

        # make sure leaf is registered
        self.assertTrue(AutoLeaf.is_registered(UniformLayer))

        # make sure leaf is correctly inferred
        self.assertEqual(
            UniformLayer,
            AutoLeaf.infer(
                [
                    FeatureContext(Scope([0]), [FeatureTypes.Uniform(start=-1.0, end=2.0)]),
                    FeatureContext(Scope([1]), [FeatureTypes.Uniform(start=1.0, end=3.0)]),
                ]
            ),
        )

        # make sure AutoLeaf can return correctly instantiated object
        uniform = AutoLeaf(
            [
                FeatureContext(Scope([0]), [FeatureTypes.Uniform(start=-1.0, end=2.0)]),
                FeatureContext(Scope([1]), [FeatureTypes.Uniform(start=1.0, end=3.0)]),
            ]
        )
        self.assertTrue(tl.all(uniform.start == tl.tensor([-1.0, 1.0])))
        self.assertTrue(tl.all(uniform.end == tl.tensor([2.0, 3.0])))
        self.assertTrue(uniform.scopes_out == [Scope([0]), Scope([1])])

    def test_layer_structural_marginalization(self):

        # ---------- same scopes -----------

        l = UniformLayer(scope=Scope([1]), start=[-1.0, 2.0], end=[1.0, 2.5], n_nodes=2)

        # ----- marginalize over entire scope -----
        self.assertTrue(marginalize(l, [1]) == None)

        # ----- marginalize over non-scope rvs -----
        l_marg = marginalize(l, [2])

        self.assertTrue(l_marg.scopes_out == [Scope([1]), Scope([1])])
        self.assertTrue(tl.all(l.start == l_marg.start))
        self.assertTrue(tl.all(l.end == l_marg.end))

        # ---------- different scopes -----------

        l = UniformLayer(scope=[Scope([1]), Scope([0])], start=[-1.0, 2.0], end=[1.0, 2.5])

        # ----- marginalize over entire scope -----
        self.assertTrue(marginalize(l, [0, 1]) == None)

        # ----- partially marginalize -----
        l_marg = marginalize(l, [1], prune=True)
        self.assertTrue(isinstance(l_marg, Uniform))
        self.assertEqual(l_marg.scope, Scope([0]))
        self.assertEqual(l_marg.start, 2.0)
        self.assertEqual(l_marg.end, 2.5)

        l_marg = marginalize(l, [1], prune=False)
        self.assertTrue(isinstance(l_marg, UniformLayer))
        self.assertEqual(len(l_marg.nodes), 1)
        self.assertEqual(l_marg.start, tl.tensor([2.0]))
        self.assertEqual(l_marg.end, tl.tensor([2.5]))

        # ----- marginalize over non-scope rvs -----
        l_marg = marginalize(l, [2])

        self.assertTrue(l_marg.scopes_out == [Scope([1]), Scope([0])])
        self.assertTrue(tl.all(l.start == l_marg.start))
        self.assertTrue(tl.all(l.end == l_marg.end))

    def test_get_params(self):

        layer = UniformLayer(
            scope=Scope([1]),
            start=[-0.73, 0.29],
            end=[0.5, 1.3],
            support_outside=[True, False],
            n_nodes=2,
        )

        start, end, support_outside, *others = layer.get_params()

        self.assertTrue(len(others) == 0)
        self.assertTrue(tl_allclose(start, tl.tensor([-0.73, 0.29])))
        self.assertTrue(tl_allclose(end, tl.tensor([0.5, 1.3])))
        self.assertTrue(tl_allclose(support_outside, tl.tensor([True, False])))


if __name__ == "__main__":
    unittest.main()