import crds
import pytest
from crds.core.exceptions import CrdsError

import stpipe.crds_client


def test_get_multiple_reference_paths_empty_reference_file_types():
    assert stpipe.crds_client.get_multiple_reference_paths({}, [], "jwst") == {}


def test_get_multiple_reference_paths_invalid_parameters():
    with pytest.raises(TypeError, match="must be a dict"):
        stpipe.crds_client.get_multiple_reference_paths(None, [], "jwst")


@pytest.mark.parametrize(
    "name, override",
    [
        ("dark", "override_dark"),
        ("read_noise", "override_read_noise"),
        ("Mask", "override_Mask"),
    ],
)
def test_get_override_name(name, override):
    assert stpipe.crds_client.get_override_name(name) == override


def test_invalid_get_override_name():
    with pytest.raises(ValueError, match="not a valid reference"):
        stpipe.crds_client.get_override_name("1mask")


def test_crds_version():
    assert stpipe.crds_client.get_svn_version() == crds.__version__


def test_reference_uri_to_cache_path(monkeypatch):
    monkeypatch.setattr(crds, "locate_file", lambda basename, observatory: basename)
    assert (
        stpipe.crds_client.reference_uri_to_cache_path("crds://foo.fits", "")
        == "foo.fits"
    )


def test_invalid_reference_uri_to_cache_path():
    with pytest.raises(CrdsError, match="should start with"):
        stpipe.crds_client.reference_uri_to_cache_path("foo.fits", "")
