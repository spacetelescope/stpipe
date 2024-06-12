import json
import os
from contextlib import nullcontext

import asdf
import pytest

from stpipe.library import BorrowError, ClosedLibraryError, AbstractModelLibrary

_GROUP_IDS = ["1", "1", "2"]
_N_MODELS = len(_GROUP_IDS)
_N_GROUPS = len(set(_GROUP_IDS))
_PRODUCT_NAME = "foo_out"


def _load_asn(filename):
    with open(filename, "r") as f:
        asn_data = json.load(f)
    return asn_data


def _write_asn(asn_data, filename):
    with open(filename, "w") as f:
        json.dump(asn_data, f)


class _Meta:
    pass


class DataModel:
    def __init__(self, **kwargs):
        self.meta = _Meta()
        self.meta.__dict__.update(kwargs)

    @property
    def crds_observatory(self):
        return "test"

    def get_crds_parameters(self):
        return {"crds": "parameters"}

    def save(self, path, **kwargs):
        data = self.meta.__dict__
        asdf.AsdfFile(data).write_to(path)


def _load_model(filename):
    with asdf.open(filename) as af:
        model = DataModel(**af.tree)
    return model


class ModelLibrary(AbstractModelLibrary):
    @property
    def crds_observatory(self):
        return "test"

    def _datamodels_open(self, filename, **kwargs):
        return _load_model(filename)

    def _load_asn(self, filename):
        return _load_asn(filename)

    def _filename_to_group_id(self, filename):
        with asdf.open(filename) as af:
            group_id = af['group_id']
        return group_id

    def _model_to_group_id(self, model):
        return model.meta.group_id


@pytest.fixture
def example_asn_path(tmp_path):
    """
    Fixture that creates a simple association, saves it (and the models)
    to disk, and returns the path of the saved association
    """
    fns = []
    for i in range(_N_MODELS):
        m = DataModel(group_id=_GROUP_IDS[i], index=i)
        base_fn = f"{i}.asdf"
        # TODO meta.filename?
        m.meta.filename = base_fn
        m.save(str(tmp_path / base_fn))
        fns.append(base_fn)
    asn = {
        "asn_pool": "pool",
        "asn_id": "a0001",
        "products": [
            {
                "name": _PRODUCT_NAME,
                "members": [{"expname": fn, "exptype": "science"} for fn in fns],
            },
        ],
    }
    asn_filename = tmp_path / (asn["asn_id"] + ".json")
    _write_asn(asn, asn_filename)
    return asn_filename


@pytest.fixture
def example_library(example_asn_path):
    """
    Fixture that builds off of `example_asn_path` and returns a
    library created from the association with default options
    """
    return ModelLibrary(example_asn_path)


def _set_custom_member_attr(example_asn_path, member_index, attr, value):
    """
    Helper function to modify the association at `example_asn_path`
    by adding an attribute `attr` to the member list (at index
    `member_index`) with value `value`. This is used to modify
    the `group_id` or `exptype` of a certain member for some tests.
    """
    asn_data = _load_asn(example_asn_path)
    asn_data["products"][0]["members"][member_index][attr] = value
    _write_asn(asn_data, example_asn_path)


def test_load_asn(example_library):
    """
    Test that __len__ returns the number of models/members loaded
    from the association (and does not require opening the library)
    """
    assert len(example_library) == _N_MODELS


def test_init_from_asn(example_asn_path):
    asn = _load_asn(example_asn_path)
    # as association filenames are local we must be in the same directory
    os.chdir(example_asn_path.parent)
    lib = ModelLibrary(asn)
    assert len(lib) == _N_MODELS


@pytest.mark.parametrize("asn_n_members", range(_N_MODELS))
def test_asn_n_members(example_asn_path, asn_n_members):
    """
    Test that creating a library with a `asn_n_members` filter
    includes only the first N members
    """
    library = ModelLibrary(example_asn_path, asn_n_members=asn_n_members)
    assert len(library) == asn_n_members


def test_asn_exptypes(example_asn_path):
    """
    Test that creating a library with a `asn_exptypes` filter
    includes only the members with a matching `exptype`
    """
    _set_custom_member_attr(example_asn_path, 0, "exptype", "background")
    library = ModelLibrary(example_asn_path, asn_exptypes="science")
    assert len(library) == _N_MODELS - 1
    library = ModelLibrary(example_asn_path, asn_exptypes="background")
    assert len(library) == 1


def test_group_names(example_library):
    """
    Test that `group_names` returns appropriate names
    based on the inferred group ids and that these names match
    the `model.meta.group_id` values
    """
    assert len(example_library.group_names) == _N_GROUPS
    group_names = set()
    with example_library:
        for index, model in enumerate(example_library):
            group_names.add(model.meta.group_id)
            example_library.shelve(model, index, modify=False)
    assert group_names == set(example_library.group_names)


def test_group_indices(example_library):
    """
    Test that `group_indices` returns appropriate model indices
    based on the inferred group ids
    """
    group_indices = example_library.group_indices
    assert len(group_indices) == _N_GROUPS
    with example_library:
        for group_name in group_indices:
            indices = group_indices[group_name]
            for index in indices:
                model = example_library.borrow(index)
                assert model.meta.group_id == group_name
                example_library.shelve(model, index, modify=False)


@pytest.mark.parametrize("attr", ["group_names", "group_indices"])
def test_group_with_no_datamodels_open(example_asn_path, attr):
    """
    Test that the "grouping" methods do not call datamodels.open
    """

    # patch _datamodels_open to always raise an exception
    # this will serve as a smoke test to see if any of the attribute
    # accesses (or instance creation) attempts to open models
    def no_open(*args, **kwargs):
        raise Exception()

    # use example_asn_path here to make the instance after we've patched
    # datamodels.open
    library = ModelLibrary(example_asn_path)
    library._datamodels_open = no_open
    getattr(library, attr)


# @pytest.mark.parametrize(
#     "asn_group_id, meta_group_id, expected_group_id", [
#         ('42', None, '42'),
#         (None, '42', '42'),
#         ('42', '26', '42'),
#     ])
# def test_group_id_override(example_asn_path, asn_group_id, meta_group_id, expected_group_id):
#     """
#     Test that overriding a models group_id via:
#         - the association member entry
#         - the model.meta.group_id
#     overwrites the automatically calculated group_id (with the asn taking precedence)
#     """
#     if asn_group_id:
#         _set_custom_member_attr(example_asn_path, 0, 'group_id', asn_group_id)
#     if meta_group_id:
#         model_filename = example_asn_path.parent / '0.fits'
#         with dm.open(model_filename) as model:
#             model.meta.group_id = meta_group_id
#             model.save(model_filename)
#     library = ModelLibrary(example_asn_path)
#     group_names = library.group_names
#     assert len(group_names) == 3
#     assert expected_group_id in group_names
#     with library:
#         model = library[0]
#         assert model.meta.group_id == expected_group_id
#         library.discard(0, model)


@pytest.mark.parametrize("modify", (True, False))
def test_model_iteration(example_library, modify):
    """
    Test that iteration through models and shelving models
    returns the appropriate models
    """
    with example_library:
        for i, model in enumerate(example_library):
            assert model.meta.index == i
            example_library.shelve(model, i, modify=modify)


@pytest.mark.parametrize("modify", (True, False))
def test_model_indexing(example_library, modify):
    """
    Test that borrowing models (using __getitem__)  and returning (or discarding)
    models returns the appropriate models
    """
    with example_library:
        for i in range(_N_MODELS):
            model = example_library.borrow(i)
            assert model.meta.index == i
            example_library.shelve(model, i, modify=modify)


def test_closed_library_model_getitem(example_library):
    """
    Test that indexing a library when it is not open triggers an error
    """
    with pytest.raises(ClosedLibraryError, match="ModelLibrary is not open"):
        example_library.borrow(0)


def test_closed_library_model_iter(example_library):
    """
    Test that attempting to iterate a library that is not open triggers an error
    """
    with pytest.raises(ClosedLibraryError, match="ModelLibrary is not open"):
        for model in example_library:
            pass


def test_double_borrow_by_index(example_library):
    """
    Test that double-borrowing a model (using __getitem__) results in an error
    """
    with pytest.raises(BorrowError, match="1 un-returned models"):
        with example_library:
            model0 = example_library.borrow(0)  # noqa: F841
            with pytest.raises(BorrowError, match="Attempt to double-borrow model"):
                model1 = example_library.borrow(0)  # noqa: F841


def test_double_borrow_during_iter(example_library):
    """
    Test that double-borrowing a model (once via iter and once via __getitem__)
    results in an error
    """
    with pytest.raises(BorrowError, match="1 un-returned models"):
        with example_library:
            for index, model in enumerate(example_library):
                with pytest.raises(BorrowError, match="Attempt to double-borrow model"):
                    model1 = example_library.borrow(index)  # noqa: F841
                break


@pytest.mark.parametrize("modify", (True, False))
def test_non_borrowed(example_library, modify):
    """
    Test that attempting to shelve a non-borrowed item results in an error
    """
    with example_library:
        with pytest.raises(BorrowError, match="Attempt to shelve non-borrowed model"):
            example_library.shelve(None, 0, modify=modify)


@pytest.mark.parametrize("n_borrowed", (1, 2))
def test_no_return_getitem(example_library, n_borrowed):
    """
    Test that borrowing and not returning models results in an
    error noting the number of un-returned models.
    """
    with pytest.raises(
        BorrowError, match=f"ModelLibrary has {n_borrowed} un-returned models"
    ):
        with example_library:
            for i in range(n_borrowed):
                example_library.borrow(i)


def test_exception_while_open(example_library):
    """
    Test that the __exit__ implementation for the library
    passes exceptions that occur in the context
    """
    with pytest.raises(Exception, match="test"):
        with example_library:
            raise Exception("test")


def test_exception_with_borrow(example_library):
    """
    Test that an exception while the library is open and has a borrowed
    model results in the exception being raised (and not an exception
    about a borrowed model not being returned).
    """
    with pytest.raises(Exception, match="test"):
        with example_library:
            model = example_library.borrow(0)  # noqa: F841
            raise Exception("test")


def test_asn_data(example_library):
    """
    Test that `asn` returns the association information
    """
    assert example_library.asn["products"][0]["name"] == _PRODUCT_NAME


def test_asn_readonly(example_library):
    """
    Test that modifying the product (dict) in the `asn` result triggers an exception
    """
    with pytest.raises(TypeError, match="object does not support item assignment"):
        example_library.asn["products"][0]["name"] = f"{_PRODUCT_NAME}_new"


def test_asn_members_readonly(example_library):
    """
    Test that modifying members (list) in the `asn` result triggers an exception
    """
    with pytest.raises(TypeError, match="object does not support item assignment"):
        example_library.asn["products"][0]["members"][0]["group_id"] = "42"


def test_asn_members_tuple(example_library):
    """
    Test that even nested items in `asn` (like `members`) are immutable
    """
    assert isinstance(example_library.asn["products"][0]["members"], tuple)


@pytest.mark.parametrize("modify", [True, False])
def test_on_disk_model_modification(example_asn_path, modify):
    """
    Test that modifying a model in a library that is on_disk
    does not persist if the model is shelved with modify=False
    """
    library = ModelLibrary(example_asn_path, on_disk=True)
    with library:
        model = library.borrow(0)
        model.meta.foo = "bar"
        library.shelve(model, 0, modify=modify)
        model = library.borrow(0)
        if modify:
            assert getattr(model.meta, "foo") == "bar"
        else:
            assert getattr(model.meta, "foo", None) is None
        # shelve the model so the test doesn't fail because of an un-returned
        # model
        library.shelve(0, model, modify=False)


@pytest.mark.parametrize("on_disk", [True, False])
def test_on_disk_no_overwrite(example_asn_path, on_disk):
    """
    Test that modifying a model in a library does not overwrite
    the input file (even if on_disk==True)
    """
    library = ModelLibrary(example_asn_path, on_disk=on_disk)
    with library:
        model = library.borrow(0)
        model.meta.foo = "bar"
        library.shelve(model, 0)

    library2 = ModelLibrary(example_asn_path, on_disk=on_disk)
    with library2:
        model = library2.borrow(0)
        assert getattr(model.meta, "foo", None) is None
        library2.shelve(model, 0)


# TODO container conversion
# TODO index
# TODO memmap?
