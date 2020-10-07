import io
import tempfile
import os

import pytest

from stdatamodels import s3_utils

import helpers


@pytest.fixture
def mk_tmp_dirs():
    """Create a set of temporary directorys and change to one of them."""
    tmp_current_path = tempfile.mkdtemp()
    tmp_data_path = tempfile.mkdtemp()
    tmp_config_path = tempfile.mkdtemp()

    old_path = os.getcwd()
    try:
        os.chdir(tmp_current_path)
        yield (tmp_current_path, tmp_data_path, tmp_config_path)
    finally:
        os.chdir(old_path)


@pytest.fixture(scope="session", autouse=True)
def setup_logging():
    from stpipe import log

    # Turn off default logging when running tests
    buffer = io.BytesIO(b"[*]\n")

    log.load_configuration(buffer)


@pytest.fixture(autouse=True)
def monkey_patch_s3_client(monkeypatch, request):
    # If tmpdir is used in the test, then it is providing the file.  Map to it.
    if "s3_root_dir" in request.fixturenames:
        path = request.getfixturevalue("s3_root_dir")
    else:
        path = None
    monkeypatch.setattr(s3_utils, "_CLIENT", helpers.MockS3Client(path))


@pytest.fixture
def s3_root_dir(tmpdir):
    return tmpdir