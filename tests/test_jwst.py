import pytest

from stpipe.container import AbstractModelContainer
from stpipe.datamodel import AbstractDataModel


def test_jwst_datamodel():
    mod = pytest.importorskip("jwst.datamodels")

    assert issubclass(mod.DataModel, AbstractDataModel)


def test_jwst_model_conainer():
    mod = pytest.importorskip("jwst.datamodels")

    assert issubclass(mod.ModelContainer, AbstractModelContainer)
