from crds.core.exceptions import CrdsLookupError
import pytest

from stpipe import crds_client


def test_missing_pars_log_filtering(capfd):
    # CRDS needs stdatamodels to handle JWST lookups
    pytest.importorskip("stdatamodels.jwst")

    # A made-up pars- reffile will raise an exception in CRDS
    with pytest.raises(CrdsLookupError):
        crds_client.get_multiple_reference_paths(
            parameters={
                "meta.instrument.name": "NIRCAM",
                "meta.telescope": "JWST",
            },
            reference_file_types=["pars-crunchyfrogstep"],
            observatory="jwst",
        )

    # The following will always be true because of a bug in how pytest handles
    # oddball logging setups, as used by crds.  See issue
    # https://github.com/pytest-dev/pytest/issues/5997
    # So don't rely on this test passing (currently) to be actually testing what
    # you think it is.
    capture = capfd.readouterr()
    assert (
        "Error determining best reference for 'pars-crunchyfrogstep'" not in capture.err
    )
