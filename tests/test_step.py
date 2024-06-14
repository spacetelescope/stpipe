"""Test step.Step"""

import logging
import re
from typing import ClassVar

import asdf
import pytest

import stpipe.config_parser as cp
from stpipe import cmdline
from stpipe.pipeline import Pipeline
from stpipe.step import Step


# ######################
# Data and Fixture setup
# ######################
class SimpleStep(Step):
    """A Step with parameters"""

    spec = """
        str1 = string(default='default')
        str2 = string(default='default')
        str3 = string(default='default')
        str4 = string(default='default')
        output_ext = string(default='simplestep')
    """


class SimplePipe(Pipeline):
    """A Pipeline with parameters and one step"""

    spec = """
        str1 = string(default='default')
        str2 = string(default='default')
        str3 = string(default='default')
        str4 = string(default='default')
        output_ext = string(default='simplestep')
    """

    step_defs: ClassVar = {"step1": SimpleStep}


class LoggingPipeline(Pipeline):
    """A Pipeline that utilizes self.log
    to log a warning
    """

    spec = """
        str1 = string(default='default')
        output_ext = string(default='simplestep')
    """

    def process(self):
        self.log.warning("This step has called out a warning.")

        self.log.warning("%s  %s", self.log, self.log.handlers)

    def _datamodels_open(self, **kwargs):
        pass


class ListArgStep(Step):
    """A Step with parameters"""

    spec = """
        output_shape = int_list(min=2, max=2, default=None)  # [y, x] - numpy convention
        crpix = float_list(min=2, max=2, default=None)
        crval = float_list(min=2, max=2, default=None)
        rotation = float(default=None)
        pixfrac = float(default=1.0)
        pixel_scale = float(default=0.0065)
        pixel_scale_ratio = float(default=0.65)
        output_ext = string(default='listargstep')
    """


@pytest.fixture()
def config_file_pipe(tmp_path):
    """Create a config file"""
    config_file = tmp_path / "simple_pipe.asdf"

    tree = {
        "class": "test_step.SimplePipe",
        "name": "SimplePipe",
        "parameters": {
            "str1": "from config",
            "str2": "from config",
        },
        "steps": [
            {
                "class": "test_step.SimpleStep",
                "name": "step1",
                "parameters": {
                    "str1": "from config",
                    "str2": "from config",
                },
            },
        ],
    }
    with asdf.AsdfFile(tree) as af:
        af.write_to(config_file)
    return config_file


@pytest.fixture()
def config_file_step(tmp_path):
    """Create a config file"""
    config_file = tmp_path / "simple_step.asdf"

    tree = {
        "class": "test_step.SimpleStep",
        "name": "SimpleStep",
        "parameters": {
            "str1": "from config",
            "str2": "from config",
        },
    }
    with asdf.AsdfFile(tree) as af:
        af.write_to(config_file)
    return config_file


@pytest.fixture()
def config_file_list_arg_step(tmp_path):
    """Create a config file"""
    config_file = tmp_path / "list_arg_step.asdf"

    tree = {
        "class": "test_step.ListArgStep",
        "name": "ListArgStep",
        "parameters": {
            "rotation": None,
            "pixel_scale_ratio": 1.1,
        },
    }
    with asdf.AsdfFile(tree) as af:
        af.write_to(config_file)
    return config_file


@pytest.fixture()
def _mock_step_crds(monkeypatch):
    """Mock various crds calls from Step"""

    def mock_get_config_from_reference_pipe(dataset, disable=None):
        return cp.config_from_dict(
            {
                "str1": "from crds",
                "str2": "from crds",
                "str3": "from crds",
                "steps": {
                    "step1": {
                        "str1": "from crds",
                        "str2": "from crds",
                        "str3": "from crds",
                    },
                },
            }
        )

    def mock_get_config_from_reference_step(dataset, disable=None):
        return cp.config_from_dict(
            {"str1": "from crds", "str2": "from crds", "str3": "from crds"}
        )

    def mock_get_config_from_reference_list_arg_step(dataset, disable=None):
        return cp.config_from_dict({"rotation": "15", "pixel_scale": "0.85"})

    monkeypatch.setattr(
        SimplePipe, "get_config_from_reference", mock_get_config_from_reference_pipe
    )
    monkeypatch.setattr(
        SimpleStep, "get_config_from_reference", mock_get_config_from_reference_step
    )
    monkeypatch.setattr(
        ListArgStep,
        "get_config_from_reference",
        mock_get_config_from_reference_list_arg_step,
    )


# #####
# Tests
# #####
@pytest.mark.usefixtures("_mock_step_crds")
def test_build_config_pipe_config_file(config_file_pipe):
    """Test that local config overrides defaults and CRDS-supplied file"""
    config, returned_config_file = SimplePipe.build_config(
        "science.fits", config_file=config_file_pipe
    )
    assert returned_config_file == config_file_pipe
    assert config["str1"] == "from config"
    assert config["str2"] == "from config"
    assert config["str3"] == "from crds"
    assert config["steps"]["step1"]["str1"] == "from config"
    assert config["steps"]["step1"]["str2"] == "from config"
    assert config["steps"]["step1"]["str3"] == "from crds"


@pytest.mark.usefixtures("_mock_step_crds")
def test_build_config_pipe_crds():
    """Test that CRDS param reffile overrides a default CRDS configuration"""
    config, config_file = SimplePipe.build_config("science.fits")
    assert not config_file
    assert config["str1"] == "from crds"
    assert config["str2"] == "from crds"
    assert config["str3"] == "from crds"
    assert config["steps"]["step1"]["str1"] == "from crds"
    assert config["steps"]["step1"]["str2"] == "from crds"
    assert config["steps"]["step1"]["str3"] == "from crds"


def test_build_config_pipe_default():
    """Test for empty config"""
    config, config_file = SimplePipe.build_config(None)
    assert config_file is None
    assert len(config) == 0


@pytest.mark.usefixtures("_mock_step_crds")
def test_build_config_pipe_kwarg(config_file_pipe):
    """Test that kwargs override CRDS and local param reffiles"""
    config, returned_config_file = SimplePipe.build_config(
        "science.fits",
        config_file=config_file_pipe,
        str1="from kwarg",
        steps={"step1": {"str1": "from kwarg"}},
    )
    assert returned_config_file == config_file_pipe
    assert config["str1"] == "from kwarg"
    assert config["str2"] == "from config"
    assert config["str3"] == "from crds"
    assert config["steps"]["step1"]["str1"] == "from kwarg"
    assert config["steps"]["step1"]["str2"] == "from config"
    assert config["steps"]["step1"]["str3"] == "from crds"


@pytest.mark.usefixtures("_mock_step_crds")
def test_build_config_step_config_file(config_file_step):
    """Test that local config overrides defaults and CRDS-supplied file"""
    config, returned_config_file = SimpleStep.build_config(
        "science.fits", config_file=config_file_step
    )
    assert returned_config_file == config_file_step
    assert config["str1"] == "from config"
    assert config["str2"] == "from config"
    assert config["str3"] == "from crds"


@pytest.mark.usefixtures("_mock_step_crds")
def test_build_config_step_crds():
    """Test override of a CRDS configuration"""
    config, config_file = SimpleStep.build_config("science.fits")
    assert config_file is None
    assert len(config) == 3
    assert config["str1"] == "from crds"
    assert config["str2"] == "from crds"
    assert config["str3"] == "from crds"


def test_build_config_step_default():
    """Test for empty config"""
    config, config_file = SimpleStep.build_config(None)
    assert config_file is None
    assert len(config) == 0


@pytest.mark.usefixtures("_mock_step_crds")
def test_build_config_step_kwarg(config_file_step):
    """Test that kwargs override everything"""
    config, returned_config_file = SimpleStep.build_config(
        "science.fits", config_file=config_file_step, str1="from kwarg"
    )
    assert returned_config_file == config_file_step
    assert config["str1"] == "from kwarg"
    assert config["str2"] == "from config"
    assert config["str3"] == "from crds"


@pytest.mark.usefixtures("_mock_step_crds")
def test_step_list_args(config_file_list_arg_step):
    """Test that list arguments, provided as comma-separated values are parsed
    correctly.
    """
    config, returned_config_file = ListArgStep.build_config(
        "science.fits", config_file=config_file_list_arg_step
    )
    assert returned_config_file == config_file_list_arg_step

    # Command line tests below need the config file path to be a string
    returned_config_file = str(returned_config_file)

    c, *_ = cmdline.just_the_step_from_cmdline(
        [
            "filename.fits",
            "--output_shape",
            "1500,1300",
            "--crpix=123,456",
            "--pixel_scale=0.75",
            "--config-file",
            returned_config_file,
        ],
        ListArgStep,
    )
    assert c.rotation is None
    assert c.pixel_scale == 0.75
    assert c.pixel_scale_ratio == 1.1
    assert c.pixfrac == 1
    assert c.output_shape == [1500, 1300]
    assert c.crpix == [123, 456]

    msg = re.escape(
        "Config parameter 'output_shape': the value \"['1500', '1300', '90']\" "
        "is too long."
    )
    with pytest.raises(ValueError, match=msg):
        cmdline.just_the_step_from_cmdline(
            [
                "filename.fits",
                "--output_shape",
                "1500,1300,90",
                "--crpix=123,456",
                "--pixel_scale=0.75",
                "--config-file",
                returned_config_file,
            ],
            ListArgStep,
        )

    msg = re.escape(
        "Config parameter 'output_shape': the value \"['1500']\" is too short."
    )
    with pytest.raises(ValueError, match=msg):
        cmdline.just_the_step_from_cmdline(
            [
                "filename.fits",
                "--output_shape",
                "1500,",
                "--crpix=123,456",
                "--pixel_scale=0.75",
                "--config-file",
                returned_config_file,
            ],
            ListArgStep,
        )

    msg = re.escape(
        "Config parameter 'output_shape': the value \"1500\" is of the wrong type."
    )
    with pytest.raises(ValueError, match=msg):
        cmdline.just_the_step_from_cmdline(
            [
                "filename.fits",
                "--output_shape",
                "1500",
                "--crpix=123,456",
                "--pixel_scale=0.75",
                "--config-file",
                returned_config_file,
            ],
            ListArgStep,
        )

    msg = re.escape(
        "Config parameter 'output_shape': the value \"1500.5\" is of the wrong type."
    )
    with pytest.raises(ValueError, match=msg):
        cmdline.just_the_step_from_cmdline(
            [
                "filename.fits",
                "--output_shape",
                "1500.5,1300.2",
                "--crpix=123,456",
                "--pixel_scale=0.75",
                "--config-file",
                returned_config_file,
            ],
            ListArgStep,
        )


def test_logcfg_routing(tmp_path):
    cfg = f"""[*]\nlevel = INFO\nhandler = file:{tmp_path}/myrun.log"""

    logcfg_file = tmp_path / "stpipe-log.cfg"

    with open(logcfg_file, "w") as f:
        f.write(cfg)

    LoggingPipeline.call(logcfg=logcfg_file)

    logdict = logging.Logger.manager.loggerDict
    for log in logdict:
        if not isinstance(logdict[log], logging.PlaceHolder):
            for handler in logdict[log].handlers:
                if isinstance(handler, logging.FileHandler):
                    logdict[log].removeHandler(handler)
                    handler.close()

    with open(tmp_path / "myrun.log") as f:
        fulltext = "\n".join(list(f))

    assert "called out a warning" in fulltext


def test_log_records():
    pipeline = LoggingPipeline()
    pipeline.run()

    assert any(
        r.message == "This step has called out a warning." for r in pipeline.log_records
    )
