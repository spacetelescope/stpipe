"""Test step.Step"""

import copy
import logging
import re
from collections.abc import Sequence
from typing import ClassVar

import asdf
import pytest

import stpipe.config_parser as cp
from stpipe import cmdline
from stpipe.datamodel import AbstractDataModel
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
    _log_records_formatter = logging.Formatter("%(message)s")

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

    assert any(r == "This step has called out a warning." for r in pipeline.log_records)


class StepWithModel(Step):
    """A step that immediately saves the model it gets passed in"""

    spec = """
    output_ext = string(default='simplestep')
    save_results = boolean(default=True)
    """

    def process(self, input_model):
        # make a change to ensure step skip is working
        # without having to define SimpleDataModel.meta.stepname
        if isinstance(input_model, SimpleDataModel):
            input_model.stepstatus = "COMPLETED"
        elif isinstance(input_model, SimpleContainer):
            for model in input_model:
                model.stepstatus = "COMPLETED"
        return input_model


class SimpleDataModel(AbstractDataModel):
    """A simple data model"""

    @property
    def crds_observatory(self):
        return "jwst"

    def get_crds_parameters(self):
        return {"test": "none"}

    def save(self, path, dir_path=None, *args, **kwargs):
        saveid = getattr(self, "saveid", None)
        if saveid is not None:
            fname = saveid + "-saved.txt"
            with open(fname, "w") as f:
                f.write(f"{path}")
            return fname
        return None


def test_save_results(tmp_cwd):
    """Ensure model saved using custom save method override when save_results=True."""

    model = SimpleDataModel()
    model.saveid = "test"
    step = StepWithModel()
    step.run(model)
    assert (tmp_cwd / "test-saved.txt").exists()


def test_skip():
    model = SimpleDataModel()
    step = StepWithModel()
    step.skip = True
    out = step.run(model)
    assert not hasattr(out, "stepstatus")
    assert out is model


@pytest.fixture(scope="function")
def model_list():
    model = SimpleDataModel()
    model_list = [copy.deepcopy(model) for _ in range(3)]
    for i, model in enumerate(model_list):
        model.saveid = f"test{i}"
    return model_list


def test_save_list(tmp_cwd, model_list):
    step = StepWithModel()
    step.run(model_list)
    for i in range(3):
        assert (tmp_cwd / f"test{i}-saved.txt").exists()


class SimpleContainer(Sequence):

    def __init__(self, models):
        self._models = models

    def __len__(self):
        return len(self._models)

    def __getitem__(self, idx):
        return self._models[idx]

    def __iter__(self):
        yield from self._models

    def insert(self, index, model):
        self._models.insert(index, model)

    def append(self, model):
        self._models.append(model)

    def extend(self, model):
        self._models.extend(model)

    def pop(self, index=-1):
        self._models.pop(index)


class SimpleContainerWithSave(SimpleContainer):

    def save(self, path, dir_path=None, *args, **kwargs):
        for model in self._models[1:]:
            # skip the first model to test that the save method is called
            # rather than just looping over all models like in the without-save case
            model.save(path, dir_path, *args, **kwargs)


def test_skip_container(tmp_cwd, model_list):
    step = StepWithModel()
    step.skip = True
    out = step.run(model_list)
    assert not hasattr(out, "stepstatus")
    for i, model in enumerate(out):
        assert not hasattr(model, "stepstatus")
        assert model_list[i] is model


def test_save_container_with_save_method(tmp_cwd, model_list):
    """ensure top-level save method is called for sequence"""
    container = SimpleContainerWithSave(model_list)
    step = StepWithModel()
    step.run(container)
    assert not (tmp_cwd / "test0-saved.txt").exists()
    assert (tmp_cwd / "test1-saved.txt").exists()
    assert (tmp_cwd / "test2-saved.txt").exists()


def test_save_tuple_with_nested_list(tmp_cwd, model_list):
    """
    in rare cases, multiple outputs are returned from step as tuple.
    One example is the jwst badpix_selfcal step, which returns one sci exposure
    and a list containing an arbitrary number of background exposures.
    Expected behavior in this case, at least at time of writing, is to save the
    science exposure and ignore the list
    """
    single_model = SimpleDataModel()
    single_model.saveid = "test"
    container = (single_model, model_list)
    step = StepWithModel()
    step.run(container)
    assert (tmp_cwd / "test-saved.txt").exists()
    for i in range(3):
        assert not (tmp_cwd / f"test{i}-saved.txt").exists()
