import io
import logging
import warnings

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


STEP_DEBUG = "This step has called out a debug message."
PIPELINE_DEBUG = "This pipeline has called out a debug message."
EXTERNAL_DEBUG = "This external package has called out a debug message."
ALL_DEBUG = [STEP_DEBUG, PIPELINE_DEBUG, EXTERNAL_DEBUG]

STEP_INFO = "This step has called out an info message."
PIPELINE_INFO = "This pipeline has called out an info message."
EXTERNAL_INFO = "This external package has called out an info message."
ALL_INFO = [STEP_INFO, PIPELINE_INFO, EXTERNAL_INFO]

STEP_WARNING = "This step has called out a warning."
PIPELINE_WARNING = "This pipeline has called out a warning."
EXTERNAL_WARNING = "This external package has called out a warning."
ALL_WARNINGS = [STEP_WARNING, PIPELINE_WARNING, EXTERNAL_WARNING]

ALL_MESSAGES = ALL_DEBUG + ALL_INFO + ALL_WARNINGS
ALL_MESSAGES_EXCEPT_DEBUG = ALL_INFO + ALL_WARNINGS

LOGLEVELS = (
    logging.CRITICAL,
    logging.ERROR,
    logging.WARNING,
    logging.INFO,
    logging.DEBUG,
)

logger = logging.getLogger("stpipe.tests.test_logger")


class LoggingStep(Step):
    """A Step that utilizes a local logger to log a warning."""

    spec = """
        str1 = string(default='default')
        output_ext = string(default='simplestep')
    """
    _log_records_formatter = logging.Formatter("%(message)s")

    def process(self):
        logger.info(STEP_INFO)
        logger.warning(STEP_WARNING)
        logger.debug(STEP_DEBUG)
        logging.getLogger("external.logger").warning(EXTERNAL_WARNING)
        logging.getLogger("external.logger").info(EXTERNAL_INFO)
        logging.getLogger("external.logger").debug(EXTERNAL_DEBUG)

    def _datamodels_open(self, **kwargs):
        pass

    @staticmethod
    def get_stpipe_loggers():
        return ("stpipe", "external")


class LoggingPipeline(Pipeline):
    """A Pipeline that utilizes a local logger to log a warning."""

    spec = """
        str1 = string(default='default')
        output_ext = string(default='simplestep')
    """
    _log_records_formatter = logging.Formatter("%(message)s")

    step_defs = {"simplestep": LoggingStep}

    def process(self):
        logger.warning(PIPELINE_WARNING)
        logger.info(PIPELINE_INFO)
        logger.debug(PIPELINE_DEBUG)
        self.simplestep.run()

    def _datamodels_open(self, **kwargs):
        pass

    @staticmethod
    def get_stpipe_loggers():
        return ("stpipe", "external")


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


def test_configuration_apply(capsys):
    log_cfg = stpipe_log.LogConfig(["stderr"], level="INFO")
    stpipe_logger = logging.getLogger("stpipe")
    other_logger = logging.getLogger("other")
    stpipe_msg = "stpipe message"
    other_msg = "other message"

    # By default, only stpipe is configured
    log_cfg.apply()
    stpipe_logger.info(stpipe_msg)
    other_logger.info(other_msg)
    capt = capsys.readouterr()
    assert capt.err.count(stpipe_msg) == 1
    assert capt.err.count(other_msg) == 0

    # Calling again does not attach a duplicate handler
    log_cfg.apply()
    stpipe_logger.info(stpipe_msg)
    other_logger.info(other_msg)
    capt = capsys.readouterr()
    assert capt.err.count(stpipe_msg) == 1
    assert capt.err.count(other_msg) == 0

    # Other logger can be added to the configuration
    log_cfg.apply(log_names=["other"])
    stpipe_logger.info(stpipe_msg)
    other_logger.info(other_msg)
    capt = capsys.readouterr()
    assert capt.err.count(stpipe_msg) == 1
    assert capt.err.count(other_msg) == 1

    # Calling undo removes configuration from both
    log_cfg.undo()
    stpipe_logger.info(stpipe_msg)
    other_logger.info(other_msg)
    capt = capsys.readouterr()
    assert capt.err.count(stpipe_msg) == 0
    assert capt.err.count(other_msg) == 0


@pytest.mark.parametrize("log_names", [None, ["stpipe"]])
def test_configuration_undo(capsys, log_names):
    log_cfg = stpipe_log.LogConfig(["stderr"], level="INFO")
    stpipe_logger = logging.getLogger("stpipe")
    stpipe_msg = "stpipe message"

    # If the log_cfg handler is attached to a logger without going
    # through "apply", it can still be removed with undo.
    stpipe_logger.addHandler(log_cfg.handlers[0])

    stpipe_logger.info(stpipe_msg)
    capt = capsys.readouterr()
    assert capt.err.count(stpipe_msg) == 1

    log_cfg.undo(log_names)
    stpipe_logger.info(stpipe_msg)
    capt = capsys.readouterr()
    assert capt.err.count(stpipe_msg) == 0


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
        log_names=[""], level=logging.ERROR, formatter=logging.Formatter("%(message)s")
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
        ("INFO", ALL_MESSAGES_EXCEPT_DEBUG),
        ("WARNING", ALL_WARNINGS),
    ),
)
def test_logcfg_routing(tmp_path, level, expected):
    cfg = f"[*]\nlevel = {level}\nhandler = file:{tmp_path}/myrun.log"

    logcfg_file = tmp_path / "stpipe-log.cfg"

    with open(logcfg_file, "w") as f:
        f.write(cfg)

    with pytest.warns(DeprecationWarning, match="'logcfg' configuration option"):
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

    for msg in ALL_MESSAGES_EXCEPT_DEBUG:
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
    assert not stpipe_log.is_configured(
        root_logger
    ), "Unexpected handler in root logger"


@pytest.fixture(params=LOGLEVELS)
def log_cfg_path(request, tmp_path):
    config_level = logging.CRITICAL - request.param
    cfg = f"[*]\nlevel = {config_level}\nhandler = file:{tmp_path}/myrun.log, stderr"

    log_cfg_path = tmp_path / "stpipe-log.cfg"

    with log_cfg_path.open("w") as f:
        f.write(cfg)

    yield log_cfg_path


def test_call_no_root_logger_changes(log_cfg_path, root_logger_unchanged):
    with pytest.warns(DeprecationWarning, match="'logcfg' configuration option"):
        LoggingPipeline.call(logcfg=str(log_cfg_path))


def test_default_call(capsys, root_logger_unchanged):
    LoggingPipeline.call()
    capt = capsys.readouterr()
    assert capt.out == ""
    for msg in ALL_MESSAGES_EXCEPT_DEBUG:
        assert msg in capt.err
    for msg in ALL_DEBUG:
        assert msg not in capt.err


def test_default_cmdline(capsys, root_logger_unchanged):
    LoggingPipeline.from_cmdline(["test_logger.LoggingPipeline"])
    capt = capsys.readouterr()
    assert capt.out == ""
    for msg in ALL_MESSAGES_EXCEPT_DEBUG:
        assert msg in capt.err
    for msg in ALL_DEBUG:
        assert msg not in capt.err


def test_from_cmdline_no_root_logger_changes(log_cfg_path, root_logger_unchanged):
    with pytest.warns(DeprecationWarning, match="logcfg configuration file"):
        LoggingPipeline.from_cmdline(
            ["test_logger.LoggingPipeline", f"--logcfg={log_cfg_path!s}"]
        )


@pytest.mark.parametrize("logging_level", LOGLEVELS)
def test_from_cmdline_no_root_logger_changes_level_arg(
    root_logger_unchanged, logging_level
):
    LoggingPipeline.from_cmdline(
        ["test_logger.LoggingPipeline", f"--log-level={logging_level!s}"]
    )


def test_step_from_cmdline_no_root_logger_changes(log_cfg_path, root_logger_unchanged):
    with pytest.warns(DeprecationWarning, match="logcfg configuration file"):
        stpipe.cmdline.step_from_cmdline(
            ["test_logger.LoggingPipeline", "--logcfg", str(log_cfg_path)]
        )


@pytest.mark.parametrize("logging_level", LOGLEVELS)
def test_step_from_cmdline_no_root_logger_changes_level_arg(
    root_logger_unchanged, logging_level
):
    stpipe.cmdline.step_from_cmdline(
        ["test_logger.LoggingPipeline", f"--log-level={logging_level!s}"]
    )


def test_just_the_step_from_cmdline_no_root_logger_changes(
    log_cfg_path, root_logger_unchanged
):
    # By default, no log configuration is applied or available in the
    # parameters.  If apply_log_cfg is True, it *will* modify the
    # root logger.
    stpipe.cmdline.just_the_step_from_cmdline(
        ["test_logger.LoggingPipeline"], apply_log_cfg=False
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

        @staticmethod
        def get_stpipe_loggers():
            return ("stpipe", "other_library")

    StepThatLogs.call()

    captured = capsys.readouterr()
    assert MSG in captured.err


def test_self_log_deprecation(caplog):
    class SelfLoggingStep(LoggingStep):
        def process(self):
            self.log.info(STEP_INFO)
            self.log.warning(STEP_WARNING)

    # No deprecation when step is created
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        step = SelfLoggingStep()

    # Deprecation warning when self.log is used
    with pytest.warns(DeprecationWarning, match="Step.log"):
        step.process()

    # Messages are still emitted
    assert STEP_INFO in caplog.text
    assert STEP_WARNING in caplog.text
    assert "stpipe.SelfLoggingStep" in caplog.text


def test_logging_unconfigured_external_package(capsys, root_logger_unchanged):
    """Test that unexpected messages from external packages are not logged."""

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

        @staticmethod
        def get_stpipe_loggers():
            # "other_library" is not a known logger,
            # so it will not be configured.
            return ("stpipe",)

    StepThatLogs.call()

    captured = capsys.readouterr()
    assert MSG not in captured.err


@pytest.mark.parametrize(
    "level, expected",
    zip(LOGLEVELS, [[], [], ALL_WARNINGS, ALL_MESSAGES_EXCEPT_DEBUG, ALL_MESSAGES]),
)
def test_configure_logging_directly(capsys, root_logger_unchanged, level, expected):
    root_logger = logging.getLogger()
    root_level = root_logger.level

    # Allow all messages through
    root_logger.setLevel(logging.DEBUG)

    # Set up a stream handler at the specified level
    handler = logging.StreamHandler()
    handler.setLevel(level)
    root_logger.addHandler(handler)

    # Root logger is now configured
    assert stpipe_log.is_configured(root_logger)

    try:
        LoggingPipeline.call()

        # Stdout should be empty
        capt = capsys.readouterr()
        assert capt.out == ""

        # Check stderr for expected messages
        for msg in ALL_MESSAGES:
            if msg in expected:
                # Make sure there's exactly one copy of the message
                assert capt.err.count(msg) == 1
            else:
                assert msg not in capt.err
    finally:
        # Clean up the root logger
        handler.flush()
        handler.close()
        root_logger.removeHandler(handler)
        root_logger.setLevel(root_level)


def test_call_configure_log(capsys, root_logger_unchanged):
    LoggingPipeline.call(configure_log=False)

    # Nothing is logged
    capt = capsys.readouterr()
    assert capt.out == ""
    assert capt.err == ""


@pytest.mark.parametrize(
    "log_level", [None, "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
)
@pytest.mark.parametrize("log_stream", [None, "stdout", "stderr", "null"])
@pytest.mark.parametrize("log_file", [None, "test_log.txt"])
def test_command_line_arguments(
    capsys, tmp_path, root_logger_unchanged, log_level, log_stream, log_file
):
    # Add specified arguments for the command line
    cmdline_args = ["test_logger.LoggingPipeline"]
    if log_level is not None:
        cmdline_args.append(f"--log-level={log_level}")
    if log_stream is not None:
        cmdline_args.append(f"--log-stream={log_stream}")
    if log_file is not None:
        log_file = tmp_path / log_file
        cmdline_args.append(f"--log-file={str(log_file)}")

    # Run the step with the specified arguments
    stpipe.cmdline.step_from_cmdline(cmdline_args)

    # Check for a log file: it is not created if there are no messages logged
    if log_file is not None and log_level not in ["ERROR", "CRITICAL"]:
        assert log_file.exists()
        with log_file.open() as fh:
            log_lines = fh.readlines()
        file_messages = "\n".join(log_lines)
    else:
        file_messages = []

    # Check for terminal log messages: default is stderr
    capt = capsys.readouterr()
    terminal_messages = ""
    if log_stream in ["null", "stdout"]:
        assert capt.err == ""
        terminal_messages = capt.out
    if log_stream in [None, "null", "stderr"]:
        assert capt.out == ""
        terminal_messages = capt.err

    # Default level is INFO, unless otherwise specified
    if log_level is None or log_level == "INFO":
        expected_messages = ALL_MESSAGES_EXCEPT_DEBUG
    elif log_level == "DEBUG":
        expected_messages = ALL_MESSAGES
    elif log_level == "WARNING":
        expected_messages = ALL_WARNINGS
    else:
        # No messages expected, regardless of other settings
        expected_messages = []
        assert len(file_messages) == 0
        assert len(terminal_messages) == 0

    # Check for expected messages in file or terminal
    for message in expected_messages:
        if log_file is not None:
            # The message is logged to the file exactly once
            assert file_messages.count(message) == 1
        else:
            assert len(file_messages) == 0
        if log_stream != "null":
            # The message is logged to the terminal exactly once
            assert terminal_messages.count(message) == 1
        else:
            assert len(terminal_messages) == 0
