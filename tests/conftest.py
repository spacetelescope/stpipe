import os
from contextlib import nullcontext
from pathlib import Path

import crds
import pytest
from crds.core import crds_cache_locking


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
    """
    Mock the used portion of the crds client so tests can be run without a crds server.
    """
    crds_path = tmp_path / "crds"
    crds_path.mkdir()

    class MockCRDSClient:
        def __init__(self, path):
            self.path = path
            self.mappings = {}

        def add_mapping(self, reftype, match=None, filename=None, observatory="jwst"):
            """
            Add a mapping to a reference in the mock crds.

            Parameters
            ---------
            reftype : str
                Reference type name.

            match : callable
                An optional callable with crds parameters as an argument and
                returning True/False if the parameters should return the filename
                for the added mapping.

            filename : str
                An optional filename to use for the reference. If not provided
                reftype will be used as the filename.

            observatory : str
                An optional observatory for the reference mapping.

            Returns
            -------
            path
                Path to the reference (created as an empty file if it doesn't exist).
            """
            if match is None:

                def match(parameters):
                    return True

            fn = (
                self.path
                / "crds"
                / observatory
                / (reftype if filename is None else filename)
            )
            fn.parent.mkdir(parents=True, exist_ok=True)
            if observatory not in self.mappings:
                self.mappings[observatory] = {}
            if reftype not in self.mappings[observatory]:
                self.mappings[observatory][reftype] = []
            self.mappings[observatory][reftype].append((match, fn))
            # create the file so check_open works
            fn.touch()
            return fn

        def lookup(self, observatory, reftype, parameters):
            """
            Look up a reference file (or "N/A" if it doesn't exist).

            Parameters
            ----------
            observatory : str
                Name of observatory.

            reftype : str
                Reference type name.

            parameters : dict
                Parameters to test against available mappings.

            Returns
            -------
            str
                Filename of reference or "N/A".
            """
            for mapping in self.mappings.get(observatory, {}).get(reftype, []):
                match, filename = mapping
                if match(parameters):
                    return str(filename)
            return "N/A"

        def add_config(self, reftype, config, observatory="jwst"):
            """
            Add a step configuration reference mapping.

            Parameters
            ----------
            reftype : str
                Reference type name.

            config : StepConfig
                StepConfig instance to save as a reference file.

            observatory : str
                Name of observatory
            """
            fn = self.add_mapping(reftype, observatory=observatory)
            config.to_asdf().write_to(fn)

        def _getreferences(self, data_dict, reftypes, observatory):
            paths = {}
            for reftype in reftypes:
                paths[reftype] = self.lookup(observatory, reftype, data_dict)
            return paths

    mock = MockCRDSClient(crds_path)

    # mock cache locking, this fixture is function scoped so no need for locking
    monkeypatch.setattr(crds_cache_locking, "get_cache_lock", nullcontext)
    monkeypatch.setattr(crds, "getreferences", mock._getreferences)
    yield mock
