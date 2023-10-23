"""
Integration tests with JWST pipeline
"""

from inspect import getmembers, isclass

import pytest

from stpipe.protocols import DataModel, ModelContainer

datamodels = pytest.importorskip("stdatamodels.jwst.datamodels")


@pytest.mark.parametrize(
    "model",
    [
        model[1]
        for model in getmembers(datamodels, isclass)
        if issubclass(model[1], datamodels.JwstDataModel)
    ],
)
def test_datamodel(model):
    assert isinstance(model(), DataModel)


def test_model_container():
    jwst = pytest.importorskip("jwst.datamodels")
    assert isinstance(jwst.ModelContainer(), ModelContainer)
