import os
from pathlib import Path

import pytest

import stpipe.crds_client


@pytest.fixture()
def tmp_cwd(tmp_path):
    """Perform test in a pristine temporary working directory."""
    old_dir = Path.cwd()
    os.chdir(tmp_path)
    try:
        yield tmp_path
    finally:
        os.chdir(old_dir)


@pytest.fixture()
def disable_crds_steppars(monkeypatch):
    """
    Disable crds steppars (by setting the environment variable)
    """
    monkeypatch.setitem(os.environ, "STPIPE_DISABLE_CRDS_STEPPARS", "True")
    yield


@pytest.fixture()
def mock_crds(monkeypatch, tmp_path):
    crds_path = tmp_path / "crds"
    crds_path.mkdir()

    class MockCRDSClient:
        def __init__(self, path):
            self.path = path

        def _reftype_to_fn(self, reftype):
            return self.path / reftype

        def add_config(self, reftype, config):
            fn = self._reftype_to_fn(reftype)
            config.to_asdf().write_to(fn)

        def _get_refpaths(self, data_dict, reference_file_types, observatory):
            paths = {}
            for reftype in reference_file_types:
                fn = self._reftype_to_fn(reftype)
                paths[reftype] = fn if fn.exists() else "N/A"
            return paths

    mock = MockCRDSClient(crds_path)

    monkeypatch.setattr(stpipe.crds_client, "_get_refpaths", mock._get_refpaths)
    yield mock
