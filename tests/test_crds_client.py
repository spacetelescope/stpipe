import pytest

from stpipe import crds_client


@pytest.mark.skip(
    "CRDS logs in a non-standard way, and pytest can't capture it. "
    "See https://github.com/pytest-dev/pytest/issues/5997"
)
def test_pars_log_filtering(caplog):
    # A bogus pars- reffile will raise an exception in CRDS
    with pytest.raises(Exception, match="Error determining best reference"):
        crds_client.get_multiple_reference_paths(
            parameters={
                "meta.instrument.detector": "NRCA1",
                "meta.instrument.filter": "F140M",
                "meta.instrument.name": "NIRCAM",
                "meta.instrument.pupil": "CLEAR",
                "meta.observation.date": "2012-04-22",
                "meta.subarray.name": "FULL",
                "meta.subarray.xsize": 2048,
                "meta.subarray.xstart": 1,
                "meta.subarray.ysize": 2048,
                "meta.subarray.ystart": 1,
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
    assert (
        "Error determining best reference for 'pars-crunchyfrogstep'" not in caplog.text
    )
