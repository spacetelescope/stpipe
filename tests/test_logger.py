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


STEP_INFO = "This step has called out an info message."
PIPELINE_INFO = "This pipeline has called out an info message."
EXTERNAL_INFO = "This external package has called out an info message."
ALL_INFO = [STEP_INFO, PIPELINE_INFO, EXTERNAL_INFO]

STEP_WARNING = "This step has called out a warning."
PIPELINE_WARNING = "This pipeline has called out a warning."
EXTERNAL_WARNING = "This external package has called out a warning."
ALL_WARNINGS = [STEP_WARNING, PIPELINE_WARNING, EXTERNAL_WARNING]

ALL_MESSAGES = ALL_INFO + ALL_WARNINGS


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
        self.log.info(STEP_INFO)
        self.log.warning(STEP_WARNING)
        logging.getLogger("external.logger").warning(EXTERNAL_WARNING)
        logging.getLogger("external.logger").info(EXTERNAL_INFO)

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
        self.log.info(PIPELINE_INFO)
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
        log_cfg = stpipe_log.load_configuration(fd)

    with log_cfg.context():
        log = logging.getLogger(stpipe_log.STPIPE_ROOT_LOGGER)

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
    stpipe_logger = logging.getLogger(stpipe_log.STPIPE_ROOT_LOGGER)
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

    assert len(log_records) == 2
    assert log_records[0] == "Error from stpipe"
    assert log_records[1] == "Error from root"


@pytest.mark.parametrize(
    "level, expected",
    (
        ("INFO", ALL_MESSAGES),
        ("WARNING", ALL_WARNINGS),
    ),
)
def test_logcfg_routing(tmp_path, level, expected):
    cfg = f"[*]\nlevel = {level}\nhandler = file:{tmp_path}/myrun.log"

    logcfg_file = tmp_path / "stpipe-log.cfg"

    with open(logcfg_file, "w") as f:
        f.write(cfg)

    LoggingPipeline.call(logcfg=logcfg_file)

    with open(tmp_path / "myrun.log") as f:
        fulltext = "\n".join(list(f))

    for msg in ALL_MESSAGES:
        if msg in expected:
            assert msg in fulltext
        else:
            assert msg not in fulltext


def test_log_records():
    pipeline = LoggingPipeline()
    pipeline.run()

    for msg in ALL_MESSAGES:
        assert msg in pipeline.log_records


@pytest.fixture
def root_logger():
    """
    Fixture to restore the root logger level
    """
    root_logger = logging.getLogger()
    original_level = root_logger.level
    yield root_logger
    root_logger.setLevel(original_level)


@pytest.mark.parametrize(
    "logging_level",
    (
        logging.CRITICAL,
        logging.ERROR,
        logging.WARNING,
        logging.INFO,
        logging.DEBUG,
    ),
)
def test_no_root_logger_changes(tmp_path, logging_level, root_logger):
    """
    Test that the root logger is not changed.
    """
    config_level = logging.CRITICAL - logging_level
    cfg = f"[*]\nlevel = {config_level}\nhandler = file:{tmp_path}/myrun.log, stderr"

    logcfg_file = tmp_path / "stpipe-log.cfg"

    with open(logcfg_file, "w") as f:
        f.write(cfg)

    # set the root logger level, this shouldn't be changed by the configuration
    root_logger.setLevel(logging_level)
    assert root_logger.level != config_level

    def no_stpipe_loggers():
        for h in root_logger.handlers:
            if isinstance(h, logging.FileHandler):
                if h.baseFilename == "/dev/null":
                    continue
                return False
            elif isinstance(h, logging.StreamHandler):
                if h.__class__.__name__ == "LogCaptureHandler":
                    # this is added by pytest
                    continue
                return False
        return True

    assert no_stpipe_loggers(), root_logger.handlers

    LoggingPipeline.call(logcfg=logcfg_file)

    # check that the level was as it was set above
    assert root_logger.level == logging_level

    assert no_stpipe_loggers(), root_logger.handlers
