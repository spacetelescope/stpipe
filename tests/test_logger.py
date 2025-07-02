import io
import logging

import pytest

import stpipe.cmdline
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
def root_logger_unchanged():
    """
    Fixture to make sure the root logger is unchanged
    """
    root_logger = logging.getLogger()
    original_level = root_logger.level
    yield
    assert root_logger.level == original_level
    for h in root_logger.handlers:
        # these are added by pytest
        if h.__class__.__name__ in ("LogCaptureHandler", "_LiveLoggingNullHandler"):
            continue
        if isinstance(h, logging.FileHandler) and h.baseFilename == "/dev/null":
            continue
        raise AssertionError(f"Unexpected handler {h} in root logger")


@pytest.mark.parametrize(
    "logging_level",
)
@pytest.fixture(
    params=(
        logging.CRITICAL,
        logging.ERROR,
        logging.WARNING,
        logging.INFO,
        logging.DEBUG,
    )
)
def log_cfg_path(request, tmp_path):
    config_level = logging.CRITICAL - request.param
    cfg = f"[*]\nlevel = {config_level}\nhandler = file:{tmp_path}/myrun.log, stderr"

    log_cfg_path = tmp_path / "stpipe-log.cfg"

    with log_cfg_path.open("w") as f:
        f.write(cfg)

    yield log_cfg_path


def test_call_no_root_logger_changes(log_cfg_path, root_logger_unchanged):
    LoggingPipeline.call(logcfg=str(log_cfg_path))


def test_from_cmdline_no_root_logger_changes(log_cfg_path, root_logger_unchanged):
    LoggingPipeline.from_cmdline(
        ["test_logger.LoggingPipeline", f"--logcfg={log_cfg_path!s}"]
    )


def test_step_from_cmdline_no_root_logger_changes(log_cfg_path, root_logger_unchanged):
    stpipe.cmdline.step_from_cmdline(
        ["test_logger.LoggingPipeline", "--logcfg", str(log_cfg_path)]
    )


def test_just_the_step_from_cmdline_no_root_logger_changes(
    log_cfg_path, root_logger_unchanged
):
    stpipe.cmdline.just_the_step_from_cmdline(
        ["test_logger.LoggingPipeline", "--logcfg", str(log_cfg_path)]
    )


def test_logging_delegation(capsys, root_logger_unchanged):
    """
    Python 3.13.3 and 3.13.4 have a bug where logging within a logger
    is ignored. See https://github.com/python/cpython/pull/135858
    for where this bug was fixed.
    For stpipe this resulted in the DelegationHandler failing
    to delegate log records from the root logger to the step logger.
    This is a minimal reproducer for that issue
    """

    # make a non-step-specific logger
    other_library_logger = logging.getLogger("other_library.logger")
    MSG = "warning from other logger"

    class StepThatLogs(Step):
        spec = """
           output_ext = string(default='step')
        """

        def process(self):
            other_library_logger.warning(MSG)

        def _datamodels_open(self, **kwargs):
            pass

    StepThatLogs.call()

    captured = capsys.readouterr()
    assert MSG in captured.err
