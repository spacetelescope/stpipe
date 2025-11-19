"""
Test that the AbstractDataModel interface works properly
"""

import pytest

from stpipe.datamodel import AbstractDataModel


def test_roman_datamodel():
    roman_datamodels = pytest.importorskip("roman_datamodels.datamodels")
    image_model = roman_datamodels.ImageModel().create_fake_data()
    assert isinstance(image_model, AbstractDataModel)


def test_jwst_datamodel():
    jwst_datamodel = pytest.importorskip("stdatamodels.jwst.datamodels")
    image_model = jwst_datamodel.ImageModel()
    assert isinstance(image_model, AbstractDataModel)


class GoodDataModel:
    def __init__(self):
        pass

    def crds_observatory(self):
        pass

    def get_crds_parameters(self):
        pass

    def save(self):
        pass


class BadDataModel:
    def __init__(self):
        pass

    def crds_observatory(self):
        pass

    def get_crds_parameters(self):
        pass


def test_good_datamodel():
    gdm = GoodDataModel()
    assert isinstance(gdm, AbstractDataModel)


def test_bad_datamodel():
    gdm = BadDataModel()
    assert not isinstance(gdm, AbstractDataModel)
