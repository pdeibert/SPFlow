from typing import List, Tuple

import tensorly as tl
from spflow.tensorly.utils.helper_functions import T
from spflow.meta.data import FeatureContext
from spflow.meta.structure import MetaModule
from spflow.tensorly.structure.general.nodes.leaves import Gaussian as TensorlyGaussian
from spflow.torch.structure.general.nodes.leaves import Gaussian as TorchGaussian
from spflow.meta.data.scope import Scope


class GeneralGaussian(MetaModule): # ToDo: backend über tl.getBackend() abfragen
    def __new__(cls, scope: Scope,mean: float = 0.0,std: float = 1.0):
        """TODO"""
        backend = tl.get_backend()
        if backend == "numpy":
            return TensorlyGaussian(scope=scope, mean=mean, std=std)
        elif backend == "pytorch":
            return TorchGaussian(scope=scope, mean=mean, std=std)
        else:
            raise NotImplementedError("GeneralGaussian is not implemented for this backend")

    @classmethod
    def accepts(cls, signatures: List[FeatureContext]) -> bool:
        backend = tl.get_backend()
        if backend == "numpy":
            return TensorlyGaussian.accepts(signatures)
        elif backend == "pytorch":
            return TorchGaussian.accepts(signatures)
        else:
            raise NotImplementedError("GeneralGaussian is not implemented for this backend")

    @classmethod
    def from_signatures(cls, signatures: List[FeatureContext]):
        backend = tl.get_backend()
        if backend == "numpy":
            return TensorlyGaussian.from_signatures(signatures)
        elif backend == "pytorch":
            return TorchGaussian.from_signatures(signatures)
        else:
            raise NotImplementedError("GeneralGaussian is not implemented for this backend")

    @property
    def dist(self):
        backend = tl.get_backend()
        if backend == "numpy":
            return TensorlyGaussian.dist
        elif backend == "pytorch":
            return TorchGaussian.dist
        else:
            raise NotImplementedError("GeneralGaussian is not implemented for this backend")

    def set_params(self, mean: float, std: float) -> None:
        backend = tl.get_backend()
        if backend == "numpy":
            TensorlyGaussian.set_params(mean=mean, std=std)
        elif backend == "pytorch":
            return TorchGaussian.set_params(mean=mean, std=std)
        else:
            raise NotImplementedError("GeneralGaussian is not implemented for this backend")

    def get_params(self) -> Tuple[float, float]:
        backend = tl.get_backend()
        if backend == "numpy":
            return TensorlyGaussian.get_params()
        elif backend == "pytorch":
            return TorchGaussian.get_params()
        else:
            raise NotImplementedError("GeneralGaussian is not implemented for this backend")

    def check_support(self, data: T, is_scope_data: bool = False) -> T:
        backend = tl.get_backend()
        if backend == "numpy":
            return TensorlyGaussian.check_support(data=data, is_scope_data=is_scope_data)
        elif backend == "pytorch":
            return TorchGaussian.check_support(data=data, is_scope_data=is_scope_data)
        else:
            raise NotImplementedError("GeneralGaussian is not implemented for this backend")