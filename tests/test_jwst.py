"""
Integration tests with JWST pipeline
"""

from inspect import getmembers, isclass

import pytest

from stpipe.protocols import DataModel

datamodels = pytest.importorskip("stdatamodels.jwst.datamodels")


def test_jwst_datamodel():
    """Smoke test to ensure the JWST datamodels work with the DataModel protocol."""
    jwst_datamodel = pytest.importorskip("stdatamodels.jwst.datamodels")
    image_model = jwst_datamodel.ImageModel()
    assert isinstance(image_model, DataModel)


@pytest.mark.parametrize(
    "model",
    [
        model[1]
        for model in getmembers(datamodels, isclass)
        if issubclass(model[1], datamodels.JwstDataModel)
    ],
)
def test_datamodel(model):
    """Test that all JWST datamodels work with the DataModel protocol."""
    assert isinstance(model(), DataModel)
