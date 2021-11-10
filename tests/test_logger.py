import io
import logging

import pytest

from stpipe import log as stpipe_log


@pytest.fixture(autouse=True)
def clean_up_logging():
    yield
    logging.shutdown()
    stpipe_log.load_configuration(io.BytesIO(stpipe_log.DEFAULT_CONFIGURATION))


def test_configuration(tmpdir):
    logfilename = tmpdir.join('output.log')

    configuration = """
[.]
handler = file:{0}
break_level = ERROR
level = WARNING
format = '%(message)s'
""".format(logfilename)

    fd = io.StringIO()
    fd.write(configuration)
    fd.seek(0)
    stpipe_log.load_configuration(fd)
    fd.close()

    log = stpipe_log.getLogger(stpipe_log.STPIPE_ROOT_LOGGER)

    log.info("Hidden")
    log.warning("Shown")

    with pytest.raises(stpipe_log.LoggedException):
        log.critical("Breaking")

    logging.shutdown()

    with open(logfilename, 'r') as fd:
        lines = [x.strip() for x in fd.readlines()]

    assert lines == ['Shown', 'Breaking']


def test_record_logs():
    stpipe_logger = stpipe_log.getLogger(stpipe_log.STPIPE_ROOT_LOGGER)
    root_logger = stpipe_log.getLogger()

    assert not any(isinstance(h, stpipe_log.RecordingHandler) for h in root_logger.handlers)

    with stpipe_log.record_logs(level=logging.ERROR) as log_records:
        stpipe_logger.warning("Warning from stpipe")
        stpipe_logger.error("Error from stpipe")
        root_logger.warning("Warning from root")
        root_logger.error("Error from root")

    assert not any(isinstance(h, stpipe_log.RecordingHandler) for h in root_logger.handlers)

    stpipe_logger.error("Additional error from stpipe")
    root_logger.error("Additional error from root")

    assert len(log_records) == 2
    assert log_records[0].message == "Error from stpipe"
    assert log_records[1].message == "Error from root"
