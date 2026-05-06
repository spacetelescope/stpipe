import logging

import asdf

import stpipe
from stpipe import Step, config_parser

logger = logging.getLogger("stpipe.tests.test_test_record_logs")


class DataModel:
    crds_observatory = "jwst"

    def __init__(self):
        self.data = {}
        self.filename = ""

    def get_crds_parameters(self):
        return self.data

    @classmethod
    def from_asdf(cls, init):
        m = cls()
        with asdf.open(init) as af:
            m.data = af.tree
        m.filename = init
        return m

    def save(self, fn, *args, **kwargs):
        # ignore filename to make the from_cmdline test below simpler
        if self.filename:
            fn = self.filename
        asdf.AsdfFile(self.data).write_to(fn)


class LoggingStep(Step):
    """A Step that utilizes a local logger to log a warning."""

    spec = """
        message = string(default='message')
        output_ext = string(default='loggingstep')
    """
    _log_records_formatter = logging.Formatter("%(message)s")

    def process(self, init):
        if isinstance(init, str):
            init = DataModel.from_asdf(init)
        logger.warning(self.message)
        return init

    def _datamodels_open(self, init, *args, **kwargs):
        if not isinstance(init, str):
            return init
        return DataModel.from_asdf(init)

    @classmethod
    def get_config_from_reference(cls, dataset, disable=None, crds_observatory=None):
        logger.warning("get_config_from_reference")
        return config_parser.ConfigObj()

    def finalize_result(self, result, reference_files_used):
        result.data["logs"] = self.log_records.copy()

    @staticmethod
    def get_stpipe_loggers():
        return ("stpipe", "external")


def test_run():
    m = DataModel()
    LoggingStep().run(m)
    assert "message" in m.data["logs"]


def test_call():
    m = DataModel()
    LoggingStep.call(m)
    assert "message" in m.data["logs"]
    assert "get_config_from_reference" in m.data["logs"]


def test_from_cmdline(tmp_path):
    fn = str(tmp_path / "test.asdf")
    DataModel().save(fn)
    Step.from_cmdline(["test_record_logs.LoggingStep", fn])
    m = DataModel.from_asdf(fn)
    assert "message" in m.data["logs"]
    assert "get_config_from_reference" in m.data["logs"]


def test_record_logs():
    stpipe_logger = logging.getLogger(stpipe.log.STPIPE_ROOT_LOGGER)
    root_logger = logging.getLogger()

    for logger in (stpipe_logger, root_logger):
        assert not any(
            isinstance(h, stpipe.log.RecordingHandler) for h in logger.handlers
        )

    m = DataModel()
    LoggingStep().run(m)

    for logger in (stpipe_logger, root_logger):
        assert not any(
            isinstance(h, stpipe.log.RecordingHandler) for h in logger.handlers
        )

    assert "message" in m.data["logs"]
