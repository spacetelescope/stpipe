import logging

from stpipe import log_config as stpipe_log


def test_record_logs():
    stpipe_logger = logging.getLogger("stpipe")
    root_logger = logging.getLogger()

    assert not any(
        isinstance(h, stpipe_log.RecordingHandler) for h in root_logger.handlers
    )

    with stpipe_log.record_logs(
        level=logging.ERROR, formatter=logging.Formatter("%(message)s")
    ) as log_records:
        stpipe_logger.warning("Warning from stpipe")
        stpipe_logger.error("Error from stpipe")
        root_logger.warning("Warning from root")
        root_logger.error("Error from root")

    assert not any(
        isinstance(h, stpipe_log.RecordingHandler) for h in root_logger.handlers
    )

    stpipe_logger.error("Additional error from stpipe")
    root_logger.error("Additional error from root")

    # Only the stpipe error message is expected
    assert len(log_records) == 1
    assert log_records[0] == "Error from stpipe"
