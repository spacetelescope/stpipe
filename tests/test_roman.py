"""
Integration tests with ROMAN pipeline
"""

from inspect import getmembers, isclass

import pytest

from stpipe.protocols import DataModel, ModelContainer

datamodels = pytest.importorskip("roman_datamodels.datamodels")


@pytest.mark.parametrize(
    "model",
    [
        model[1]
        for model in getmembers(datamodels, isclass)
        if model[1] != datamodels.DataModel
        and issubclass(model[1], datamodels.DataModel)
    ],
)
def test_datamodel(model):
    assert isinstance(model(), DataModel)


def test_model_container():
    romancal = pytest.importorskip("romancal.datamodels")
    assert isinstance(romancal.ModelContainer(), ModelContainer)
