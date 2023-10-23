"""
Test that the Protocols work correctly
"""
from itertools import chain, combinations

import pytest

from stpipe.protocols import DataModel, ModelContainer


def test_roman_datamodel():
    roman_datamodels = pytest.importorskip("roman_datamodels.datamodels")
    import roman_datamodels.maker_utils as rutil

    roman_image_tree = rutil.mk_level2_image()
    image_model = roman_datamodels.ImageModel(roman_image_tree)
    assert isinstance(image_model, DataModel)


def test_jwst_datamodel():
    jwst_datamodel = pytest.importorskip("stdatamodels.jwst.datamodels")
    image_model = jwst_datamodel.ImageModel()
    assert isinstance(image_model, DataModel)


def _base_methods():
    def crds_observatory(self):
        pass

    def save(self):
        pass

    return crds_observatory, save


def _datamodel_methods():
    def get_crds_parameters(self):
        pass

    return get_crds_parameters, *_base_methods()


def _modelcontainer_methods():
    def __iter__(self):
        pass

    def read_asn(self):
        pass

    def from_asn(self):
        pass

    return __iter__, read_asn, from_asn, *_base_methods()


def _powerset(iterable):
    return [
        [this]
        for this in chain.from_iterable(
            list(combinations(iterable, r)) for r in range(len(iterable))
        )
    ]


@pytest.fixture()
def data_object(request):
    print(request.param)
    return type(
        "DataObject",
        (object,),
        {method.__name__: method for method in request.param[0]},
    )


@pytest.mark.parametrize("data_object", [[_datamodel_methods()]], indirect=True)
def test_good_datamodel(data_object):
    """Test that an object with all methods is a DataModel"""
    assert isinstance(data_object(), DataModel)


@pytest.mark.parametrize("data_object", _powerset(_datamodel_methods()), indirect=True)
def test_bad_datamodel(data_object):
    """Test that any object missing at any of the methods is not a DataModel"""
    assert not isinstance(data_object(), DataModel)


@pytest.mark.parametrize("data_object", [[_modelcontainer_methods()]], indirect=True)
def test_good_modelcontainer(data_object):
    """Test that an object with all methods is a ModelContainer"""
    assert isinstance(data_object(), ModelContainer)


@pytest.mark.parametrize(
    "data_object", _powerset(_modelcontainer_methods()), indirect=True
)
def test_bad_modelcontainer(data_object):
    """Test that any object missing at any of the methods is not a ModelContainer"""
    assert not isinstance(data_object(), ModelContainer)
