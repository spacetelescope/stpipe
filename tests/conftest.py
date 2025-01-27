import os
from pathlib import Path

import pytest


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
