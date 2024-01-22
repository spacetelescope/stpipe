import pytest

pytest.importorskip("jwst")

from jwst.stpipe import Pipeline, Step  # noqa: E402


class ShovelPixelsStep(Step):
    class_alias = "shovelpixels"

    def process(self, input_data):
        self.log.info("Shoveling...")
        return input_data


class CancelNoiseStep(Step):
    class_alias = "cancelnoise"

    def process(self, input_data):
        self.log.info("De-noising...")
        return input_data


class HookStep(Step):
    class_alias = "myhook"

    spec = """
    param1 = string(default="bar")
    param2 = float(default=1)
    """

    def process(self, input_data):
        self.log.info("Running HookStep with %s and %s", self.param1, self.param2)

        return input_data


class MyPipeline(Pipeline):
    class_alias = "mypipeline"

    step_defs = {  # noqa: RUF012
        "shovelpixels": ShovelPixelsStep,
        "cancelnoise": CancelNoiseStep,
    }

    def process(self, input_data):
        result = self.shovelpixels(input_data)
        result = self.cancelnoise(result)

        return result  # noqa: RET504


def hook_function(input_data):
    import logging

    log = logging.getLogger(__name__)
    log.info("Running hook_function on data array of size %s", input_data.shape)

    return input_data


def test_hook_as_step_class(caplog):
    """Test an imported Step subclass can be a hook"""
    datamodels = pytest.importorskip("stdatamodels.jwst.datamodels")
    model = datamodels.ImageModel((10, 10))

    steps = {
        "cancelnoise": {
            "post_hooks": [
                HookStep,
            ]
        }
    }
    MyPipeline.call(model, steps=steps)

    assert "Running HookStep with bar and 1" in caplog.text
    assert "cancelnoise.myhook" in caplog.text


def test_hook_as_step_instance(caplog):
    """Test an imported Step subclass instance with parameters can be a hook"""
    datamodels = pytest.importorskip("stdatamodels.jwst.datamodels")
    model = datamodels.ImageModel((10, 10))

    steps = {
        "shovelpixels": {
            "post_hooks": [
                HookStep(param1="foo", param2=3),
            ]
        }
    }
    MyPipeline.call(model, steps=steps)

    assert "Running HookStep with foo and 3" in caplog.text


def test_hook_as_string_of_importable_step_class(caplog):
    """Test a string of a fully-qualified path to Step subclass can be a hook"""
    datamodels = pytest.importorskip("stdatamodels.jwst.datamodels")
    model = datamodels.ImageModel((10, 10))

    steps = {
        "shovelpixels": {
            "post_hooks": [
                "test_hooks.HookStep",
            ]
        }
    }
    MyPipeline.call(model, steps=steps)

    assert "Running HookStep" in caplog.text


def test_hook_as_string_of_step_instance(caplog):
    """Test a string of a fully-qualified Step instance w/params"""
    datamodels = pytest.importorskip("stdatamodels.jwst.datamodels")
    model = datamodels.ImageModel((10, 10))

    steps = {
        "shovelpixels": {
            "post_hooks": [
                "test_hooks.HookStep(param1='foo', param2=2)",
            ]
        }
    }
    MyPipeline.call(model, steps=steps)

    assert "Running HookStep with foo and 2" in caplog.text


def test_hook_as_string_of_importable_function(caplog):
    """Test a string of a fully-qualified function path can be a hook"""
    datamodels = pytest.importorskip("stdatamodels.jwst.datamodels")
    model = datamodels.ImageModel((10, 10))

    steps = {
        "shovelpixels": {
            "post_hooks": [
                "test_hooks.hook_function",
            ]
        }
    }
    MyPipeline.call(model, steps=steps)

    assert "Running hook_function on data array of size (10, 10)" in caplog.text


def test_hook_as_systemcall(caplog, tmp_cwd):
    """Test a string of a terminal command"""
    datamodels = pytest.importorskip("stdatamodels.jwst.datamodels")
    model = datamodels.ImageModel((10, 10))
    filename = "test_hook_as_subprocess.fits"
    path = tmp_cwd / filename
    model.save(path)

    # Run post_hooks of "fitsinfo" and "fitsheader" CLI scripts from astropy
    steps = {
        "shovelpixels": {
            "post_hooks": [
                "fitsinfo {0}",
                "fitsheader {0}",
            ]
        }
    }
    MyPipeline.call(model, steps=steps)

    # Logs from fitsinfo
    assert "SystemCall instance created" in caplog.text
    assert "Spawning 'fitsinfo stpipe.MyPipeline.shovelpixels.post_hook0" in caplog.text

    # logs from fitsheader
    assert "DATAMODL= 'ImageModel'" in caplog.text
