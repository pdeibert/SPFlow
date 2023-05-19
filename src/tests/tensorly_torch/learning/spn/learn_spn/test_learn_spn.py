import random
import unittest

import numpy as np
import torch

from spflow.meta.data import FeatureContext, FeatureTypes, Scope
from spflow.tensorly.learning.spn.learn_spn import (
    cluster_by_kmeans,
    learn_spn,
    partition_by_rdc,
)
from spflow.tensorly.structure.spn import (
    #CondGaussian,
    CondSumNode,
    #Gaussian,
    ProductNode,
    SumNode,
)
from spflow.torch.structure.spn import Gaussian, CondGaussian


# dummy clustering and partition methods
def clustering_fn(x):
    # split into two approximately equal sized clusters
    mask = torch.zeros(x.shape[0])
    mask[int(x.shape[0] / 2) :] = 1
    return mask


def partitioning_fn(x):
    ids = torch.zeros(x.shape[1])

    if not partitioning_fn.alternate or partitioning_fn.partition:
        # split into two approximately equal sized partitions
        partitioning_fn.partition = False
        ids[: int(x.shape[1] / 2)] = 1
    else:
        partitioning_fn.partition = True
    return ids


class TestNode(unittest.TestCase):
    @classmethod
    def setup_class(cls):
        torch.set_default_dtype(torch.float64)

    @classmethod
    def teardown_class(cls):
        torch.set_default_dtype(torch.float32)

    def test_kmeans_clustering_1(self):

        # set seed
        torch.manual_seed(0)
        np.random.seed(0)
        random.seed(0)

        # simulate cluster data
        cluster_1 = torch.randn((100, 1)) - 5.0
        cluster_2 = torch.randn((100, 1)) + 5.0

        # compute clusters using k-means
        cluster_mask = cluster_by_kmeans(torch.vstack([cluster_1, cluster_2]), n_clusters=2)

        # cluster id can either be 0 or 1
        cluster_id = cluster_mask[0]
        # make sure all first 100 entries have the same cluster id
        self.assertTrue(torch.all(cluster_mask[:100] == cluster_id))

        # second cluster id should be different from first
        cluster_id = (cluster_id + 1) % 2
        self.assertTrue(torch.all(cluster_mask[100:] == cluster_id))

    def test_kmeans_clustering_2(self):

        # set seed
        torch.manual_seed(0)
        np.random.seed(0)
        random.seed(0)

        # simulate cluster data
        cluster_1 = torch.randn((100, 1)) - 10.0
        cluster_2 = torch.randn((100, 1)) + 10.0
        cluster_3 = torch.randn((100, 1))

        # compute clusters using k-means
        cluster_mask = cluster_by_kmeans(torch.vstack([cluster_1, cluster_2, cluster_3]), n_clusters=3)

        cluster_ids = [0, 1, 2]

        # cluster id can either be 0,1 or 2
        cluster_id = cluster_mask[0]
        cluster_ids.remove(cluster_id)

        # make sure all first 100 entries have the same cluster id
        self.assertTrue(torch.all(cluster_mask[:100] == cluster_id))

        # second cluster id should be different from first
        cluster_id = cluster_mask[100]
        self.assertTrue(cluster_id in cluster_ids)
        cluster_ids.remove(cluster_id)

        self.assertTrue(torch.all(cluster_mask[100:200] == cluster_id))

        # third cluster id should be different from first two
        cluster_id = cluster_mask[200]
        self.assertTrue(cluster_id in cluster_ids)
        cluster_ids.remove(cluster_id)

        self.assertTrue(torch.all(cluster_mask[200:] == cluster_id))

    def test_rdc_partitioning_1(self):

        # set seed
        torch.manual_seed(0)
        np.random.seed(0)
        random.seed(0)

        # simulate partition data
        data_partition_1 = torch.randn(100, 1) + 10.0
        data_partition_2 = torch.randn(100, 1) - 10.0

        # compute clusters using k-means
        partition_mask = partition_by_rdc(torch.hstack([data_partition_1, data_partition_2]), threshold=0.5)

        # should be two partitions
        self.assertTrue(len(torch.unique(partition_mask)) == 2)

    def test_rdc_partitioning_2(self):

        # set seed
        torch.manual_seed(0)
        np.random.seed(0)
        random.seed(0)

        # simulate partition data
        data_partition_1 = np.random.multivariate_normal(np.zeros(2), np.array([[1, 0.5], [0.5, 1]]), size=(100,))
        data_partition_2 = np.random.randn(100, 1) + 10.0

        # compute clusters using k-means
        partition_mask = partition_by_rdc(
            torch.tensor(np.hstack([data_partition_1, data_partition_2])),
            threshold=0.5,
        )

        # should be two partitions
        self.assertTrue(len(torch.unique(partition_mask)) == 2)

        # check if partitions are correct (order is irrelevant)
        partition_1 = torch.where(partition_mask == 0)[0]
        self.assertTrue(torch.all(partition_1 == torch.tensor([0, 1])) or torch.all(partition_1 == torch.tensor([2])))

    def test_rdc_partitioning_nan(self):

        # set seed
        torch.manual_seed(0)
        np.random.seed(0)
        random.seed(0)

        # simulate partition data
        data_partition_1 = torch.randn((100, 1)) + 10.0
        data_partition_2 = torch.randn((100, 1)) - 10.0

        # insert invalid value
        data_partition_2[0] = float("nan")

        self.assertRaises(
            ValueError,
            partition_by_rdc,
            torch.hstack([data_partition_1, data_partition_2]),
            threshold=0.5,
        )

    def test_learn_1(self):

        # set seed
        torch.manual_seed(0)
        np.random.seed(0)
        random.seed(0)

        data = torch.randn((100, 3))
        feature_ctx = FeatureContext(Scope([0, 1, 2]), {k: FeatureTypes.Gaussian for k in range(3)})

        # ----- min_features_slice > scope size (no splitting or clustering) -----

        partitioning_fn.alternate = True
        partitioning_fn.partition = True

        spn = learn_spn(
            data,
            feature_ctx=feature_ctx,
            partitioning_method=partitioning_fn,
            clustering_method=clustering_fn,
            fit_params=False,
            min_features_slice=4,
        )

        # check resulting graph
        self.assertTrue(isinstance(spn, ProductNode))
        # children of product node should be leaves since scope is originally multivariate and no partitioning/clustering occurs
        self.assertTrue(all([isinstance(child, Gaussian) for child in spn.children]))

    def test_learn_spn_2(self):

        # set seed
        torch.manual_seed(0)
        np.random.seed(0)
        random.seed(0)

        data = torch.randn((100, 3))
        feature_ctx = FeatureContext(Scope([0, 1, 2]), {k: FeatureTypes.Gaussian for k in range(3)})

        # ----- min_instances_slice_100, alternate partitioning -----

        partitioning_fn.alternate = True
        partitioning_fn.partition = True

        spn = learn_spn(
            data,
            feature_ctx=feature_ctx,
            partitioning_method=partitioning_fn,
            clustering_method=clustering_fn,
            fit_params=False,
            min_instances_slice=51,
        )

        # check resulting graph
        self.assertTrue(isinstance(spn, ProductNode))
        partition_1, partition_2 = list(spn.children)
        # partition 1
        self.assertTrue(isinstance(partition_1, SumNode))
        partition_1_clustering_1, partition_1_clustering_2 = list(partition_1.children)
        # children of both clusterings should be product nodes since this partition is originally multivariate
        self.assertTrue(isinstance(partition_1_clustering_1, ProductNode))
        self.assertTrue(all([isinstance(child, Gaussian) for child in partition_1_clustering_1.children]))
        self.assertTrue(isinstance(partition_1_clustering_1, ProductNode))
        self.assertTrue(all([isinstance(child, Gaussian) for child in partition_1_clustering_2.children]))
        # partition 2
        self.assertTrue(isinstance(partition_2, Gaussian))

    def test_learn_spn_3(self):

        # set seed
        torch.manual_seed(0)
        np.random.seed(0)
        random.seed(0)

        data = torch.randn((100, 3))
        feature_ctx = FeatureContext(Scope([0, 1, 2]), {k: FeatureTypes.Gaussian for k in range(3)})

        # ----- successive partitioning -----

        partitioning_fn.alternate = False

        spn = learn_spn(
            data,
            feature_ctx=feature_ctx,
            partitioning_method=partitioning_fn,
            clustering_method=clustering_fn,
            fit_params=False,
            min_instances_slice=101,
        )

        # check resulting graph
        self.assertTrue(isinstance(spn, ProductNode))
        partition_1, partition_2 = list(spn.children)
        # partition 1
        self.assertTrue(isinstance(partition_1, ProductNode))
        self.assertTrue(all([isinstance(child, Gaussian) for child in partition_1.children]))
        # partition 2
        self.assertTrue(isinstance(partition_2, Gaussian))

    def test_conditional_spn(self):

        # set seed
        np.random.seed(0)
        random.seed(0)

        data = torch.randn(100, 3)
        feature_ctx = FeatureContext(Scope([0, 1, 2], [3]), {k: FeatureTypes.Gaussian for k in range(3)})

        # ----- min_instances_slice_100, alternate partitioning -----

        partitioning_fn.alternate = True
        partitioning_fn.partition = True

        spn = learn_spn(
            data,
            feature_ctx,
            partitioning_method=partitioning_fn,
            clustering_method=clustering_fn,
            fit_params=False,
            min_instances_slice=51,
        )

        # check resulting graph
        self.assertTrue(isinstance(spn, ProductNode))
        partition_1, partition_2 = list(spn.children)
        # partition 1
        self.assertTrue(isinstance(partition_1, CondSumNode))
        (
            partition_1_clustering_1,
            partition_1_clustering_2,
        ) = partition_1.children
        # children of both clusterings should be product nodes since this partition is originally multivariate
        self.assertTrue(isinstance(partition_1_clustering_1, ProductNode))
        self.assertTrue(all([isinstance(child, CondGaussian) for child in partition_1_clustering_1.children]))
        self.assertTrue(isinstance(partition_1_clustering_1, ProductNode))
        self.assertTrue(all([isinstance(child, CondGaussian) for child in partition_1_clustering_2.children]))
        # partition 2
        self.assertTrue(isinstance(partition_2, CondGaussian))

    def test_learn_spn_invalid_arguments(self):

        # scope length does not match data shape
        self.assertRaises(
            ValueError,
            learn_spn,
            torch.randn((1, 3)),
            FeatureContext(Scope([0, 1]), {k: FeatureTypes.Gaussian for k in range(2)}),
        )
        # invalid clustering method
        self.assertRaises(
            ValueError,
            learn_spn,
            torch.randn((1, 3)),
            FeatureContext(Scope([0, 1]), {k: FeatureTypes.Gaussian for k in range(2)}),
            clustering_method="invalid_option",
            partitioning_method="rdc",
        )
        # invalid partitioning method
        self.assertRaises(
            ValueError,
            learn_spn,
            torch.randn((1, 3)),
            FeatureContext(Scope([0, 1]), {k: FeatureTypes.Gaussian for k in range(2)}),
            clustering_method="kmeans",
            partitioning_method="invalid_option",
        )
        # invalid min number of instances for slicing
        self.assertRaises(
            ValueError,
            learn_spn,
            torch.randn((1, 3)),
            FeatureContext(Scope([0, 1]), {k: FeatureTypes.Gaussian for k in range(2)}),
            min_instances_slice=1,
        )
        # invalid min number of features for slicing
        self.assertRaises(
            ValueError,
            learn_spn,
            torch.randn((1, 3)),
            FeatureContext(Scope([0, 1]), {k: FeatureTypes.Gaussian for k in range(2)}),
            min_features_slice=1,
        )
        # conditional scope with enabled 'fit_params' option
        self.assertRaises(
            ValueError,
            learn_spn,
            torch.randn(1, 3),
            FeatureContext(
                Scope([0, 1, 2], [3]),
                {k: FeatureTypes.Gaussian for k in range(3)},
            ),
        )


if __name__ == "__main__":
    unittest.main()