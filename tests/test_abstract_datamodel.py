"""
Test that the AbstractDataModel interface works properly
"""

from stpipe.datamodel import AbstractDataModel


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
