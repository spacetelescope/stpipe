import pytest

from stpipe.container import AbstractModelContainer
from stpipe.datamodel import AbstractDataModel


def test_roman_datamodel():
    mod = pytest.importorskip("roman_datamodels")

    assert issubclass(mod.DataModel, AbstractDataModel)


def test_roman_model_container():
    mod = pytest.importorskip("romancal.datamodels.container")

    assert issubclass(mod.ModelContainer, AbstractModelContainer)
