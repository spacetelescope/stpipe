import asdf
import pytest

from stpipe.pipeline import Pipeline
from stpipe.step import Step


class FakeDataModel:
    def __init__(self, data_id=None):
        self.data_id = data_id

    @property
    def crds_observatory(self):
        return "jwst"

    def get_crds_parameters(self):
        return {}

    def save(self, filename):
        asdf.AsdfFile({"data_id": self.data_id}).write_to(filename)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class FakeStep(Step):
    spec = """
    output_ext = string(default='asdf')
    """

    @classmethod
    def _datamodels_open(cls, init, **kwargs):
        return init


class ShovelPixelsStep(FakeStep):
    class_alias = "shovelpixels"

    def process(self, input_data):
        self.log.info("Shoveling...")
        return input_data


class CancelNoiseStep(FakeStep):
    class_alias = "cancelnoise"

    def process(self, input_data):
        self.log.info("De-noising...")
        return input_data


class HookStep(FakeStep):
    class_alias = "myhook"

    spec = """
    param1 = string(default="bar")
    param2 = float(default=1)
    output_ext = string(default='asdf')
    """

    def process(self, input_data):
        self.log.info("Running HookStep with %s and %s", self.param1, self.param2)

        return input_data


class MyPipeline(Pipeline):
    class_alias = "mypipeline"

    spec = """
    output_ext = string(default='asdf')
    """

    step_defs = {  # noqa: RUF012
        "shovelpixels": ShovelPixelsStep,
        "cancelnoise": CancelNoiseStep,
    }

    @classmethod
    def _datamodels_open(cls, init, **kwargs):
        return init

    def process(self, input_data):
        result = self.shovelpixels.run(input_data)
        result = self.cancelnoise.run(result)

        return result  # noqa: RET504


def hook_function(input_data):
    import logging

    log = logging.getLogger(__name__)
    log.info("Running hook_function on data %s", input_data.data_id)

    return input_data


@pytest.mark.parametrize("hook_type", ["pre_hooks", "post_hooks"])
def test_hook_as_step_class(hook_type, caplog, disable_crds_steppars):
    """Test an imported Step subclass can be a hook"""
    model = FakeDataModel()

    steps = {
        "cancelnoise": {
            hook_type: [
                HookStep,
            ]
        }
    }
    MyPipeline.call(model, steps=steps)

    assert "Running HookStep with bar and 1" in caplog.text
    assert "cancelnoise.myhook" in caplog.text


@pytest.mark.parametrize("hook_type", ["pre_hooks", "post_hooks"])
def test_hook_as_step_instance(hook_type, caplog, disable_crds_steppars):
    """Test an imported Step subclass instance with parameters can be a hook"""
    model = FakeDataModel()

    steps = {
        "shovelpixels": {
            hook_type: [
                HookStep(param1="foo", param2=3),
            ]
        }
    }
    MyPipeline.call(model, steps=steps)

    assert "Running HookStep with foo and 3" in caplog.text


@pytest.mark.parametrize("hook_type", ["pre_hooks", "post_hooks"])
def test_hook_as_string_of_importable_step_class(
    hook_type, caplog, disable_crds_steppars
):
    """Test a string of a fully-qualified path to Step subclass can be a hook"""
    model = FakeDataModel()

    steps = {
        "shovelpixels": {
            hook_type: [
                "test_hooks.HookStep",
            ]
        }
    }
    MyPipeline.call(model, steps=steps)

    assert "Running HookStep" in caplog.text


@pytest.mark.parametrize("hook_type", ["pre_hooks", "post_hooks"])
def test_hook_as_string_of_step_instance(hook_type, caplog, disable_crds_steppars):
    """Test a string of a fully-qualified Step instance w/params"""
    model = FakeDataModel()

    steps = {
        "shovelpixels": {
            hook_type: [
                "test_hooks.HookStep(param1='foo', param2=2)",
            ]
        }
    }
    MyPipeline.call(model, steps=steps)

    assert "Running HookStep with foo and 2" in caplog.text


@pytest.mark.parametrize("hook_type", ["pre_hooks", "post_hooks"])
def test_hook_as_string_of_importable_function(
    hook_type, caplog, disable_crds_steppars
):
    """Test a string of a fully-qualified function path can be a hook"""
    data_id = 42
    model = FakeDataModel(data_id)

    steps = {
        "shovelpixels": {
            hook_type: [
                "test_hooks.hook_function",
            ]
        }
    }
    MyPipeline.call(model, steps=steps)

    assert f"Running hook_function on data {data_id}" in caplog.text


@pytest.mark.parametrize("hook_type", ["pre_hooks", "post_hooks"])
def test_hook_as_systemcall(hook_type, caplog, tmp_cwd, disable_crds_steppars):
    """Test a string of a terminal command"""
    model = FakeDataModel()

    # Run post_hook CLI scripts
    steps = {
        "shovelpixels": {
            hook_type: [
                "asdftool info {0}",
            ]
        }
    }
    MyPipeline.call(model, steps=steps)

    # Logs from fitsinfo
    assert "SystemCall instance created" in caplog.text
    assert "Spawning 'asdftool info stpipe.MyPipeline.shovelpixels" in caplog.text
