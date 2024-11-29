"""
Integration tests with Roman pipeline
"""

from inspect import getmembers, isclass

import pytest

from stpipe.protocols import DataModel

datamodels = pytest.importorskip("roman_datamodels.datamodels")


def test_roman_datamodel():
    """Smoke test to ensure the Roman datamodels work with the DataModel protocol."""
    roman_datamodels = pytest.importorskip("roman_datamodels.datamodels")

    image_model = roman_datamodels.ImageModel.create_fake_data()
    assert isinstance(image_model, DataModel)


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
    """Test that all Roman datamodels work with the DataModel protocol."""
    assert isinstance(model(), DataModel)
