import io
import logging

import pytest

from stpipe import Step
from stpipe import log as stpipe_log
from stpipe.pipeline import Pipeline


@pytest.fixture(autouse=True)
def _clean_up_logging():
    """
    Reset logging configuration to DEFAULT_CONFIGURATION
    """
    yield
    logging.shutdown()
    stpipe_log.load_configuration(io.BytesIO(stpipe_log.DEFAULT_CONFIGURATION))


STEP_WARNING = "This step has called out a warning."
PIPELINE_WARNING = "This pipeline has called out a warning."
EXTERNAL_WARNING = "This external package has called out a warning."


class LoggingStep(Step):
    """A Step that utilizes self.log
    to log a warning
    """

    spec = """
        str1 = string(default='default')
        output_ext = string(default='simplestep')
    """
    _log_records_formatter = logging.Formatter("%(message)s")

    def process(self):
        self.log.warning(STEP_WARNING)
        self.log.warning("%s  %s", self.log, self.log.handlers)
        logging.getLogger("external.logger").warning(EXTERNAL_WARNING)

    def _datamodels_open(self, **kwargs):
        pass


class LoggingPipeline(Pipeline):
    """A Pipeline that utilizes self.log
    to log a warning
    """

    spec = """
        str1 = string(default='default')
        output_ext = string(default='simplestep')
    """
    _log_records_formatter = logging.Formatter("%(message)s")

    step_defs = {"simplestep": LoggingStep}

    def process(self):
        self.log.warning(PIPELINE_WARNING)
        self.log.warning("%s  %s", self.log, self.log.handlers)
        self.simplestep.run()

    def _datamodels_open(self, **kwargs):
        pass


def test_configuration(tmp_path):
    """
    Test that load_configuration configures the stpipe root logger
    """
    logfilename = tmp_path / "output.log"

    configuration = f"""
[.]
handler = file:{logfilename}
break_level = ERROR
level = WARNING
format = '%(message)s'
"""

    with io.StringIO() as fd:
        fd.write(configuration)
        fd.seek(0)
        stpipe_log.load_configuration(fd)

    log = stpipe_log.getLogger(stpipe_log.STPIPE_ROOT_LOGGER)

    log.info("Hidden")
    log.warning("Shown")

    with pytest.raises(stpipe_log.LoggedException):
        log.critical("Breaking")

    logging.shutdown()

    with open(logfilename) as fd:
        lines = [x.strip() for x in fd.readlines()]

    assert lines == ["Shown", "Breaking"]


def test_record_logs():
    """
    Test that record_logs respects the default configuration
    """
    stpipe_logger = stpipe_log.getLogger(stpipe_log.STPIPE_ROOT_LOGGER)
    root_logger = stpipe_log.getLogger()

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

    assert len(log_records) == 2
    assert log_records[0] == "Error from stpipe"
    assert log_records[1] == "Error from root"


def test_logcfg_routing(tmp_path):
    cfg = f"""[*]\nlevel = INFO\nhandler = file:{tmp_path}/myrun.log"""

    logcfg_file = tmp_path / "stpipe-log.cfg"

    with open(logcfg_file, "w") as f:
        f.write(cfg)

    LoggingPipeline.call(logcfg=logcfg_file)

    with open(tmp_path / "myrun.log") as f:
        fulltext = "\n".join(list(f))

    for w in [STEP_WARNING, PIPELINE_WARNING, EXTERNAL_WARNING]:
        assert w in fulltext


def test_log_records():
    pipeline = LoggingPipeline()
    pipeline.run()

    assert STEP_WARNING in pipeline.log_records
    assert PIPELINE_WARNING in pipeline.log_records
    assert EXTERNAL_WARNING in pipeline.log_records
