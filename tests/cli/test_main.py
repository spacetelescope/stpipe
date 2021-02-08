import subprocess

import pytest

import stpipe
from stpipe.cli import handle_args
from stpipe import entry_points
from stpipe.entry_points import StepInfo


@pytest.fixture(autouse=True)
def monkey_patch_get_steps(monkeypatch):
    def _get_steps():
        return [
            StepInfo("jwst.pipeline.Ami3Pipeline", "calwebb_ami3", True, "jwst", "0.18.4"),
            StepInfo("jwst.pipeline.Coron3Pipeline", "calwebb_coron3", True, "jwst", "0.18.4"),
            StepInfo("romancal.pipeline.SomeRomanPipeline", None, True, "romancal", "0.1.1"),
            StepInfo("romancal.step.FlatFieldStep", None, False, "romancal", "0.1.1"),
            StepInfo("razzledazzle.step.RazzleDazzleStep", None, False, "razzledazzle", "9.5.3"),
        ]

    monkeypatch.setattr(entry_points, "get_steps", _get_steps)


@pytest.mark.parametrize("flag", ["-v", "--version"])
def test_version(flag, capsys):
    assert handle_args([flag]) == 0

    captured = capsys.readouterr()

    assert f"stpipe: {stpipe.__version__}" in captured.out
    assert "jwst: 0.18.4" in captured.out
    assert "razzledazzle: 9.5.3" in captured.out
    assert "romancal: 0.1.1" in captured.out


def test_package_main():
    out = subprocess.check_output(["python", "-m", "stpipe", "--version"]).decode("utf-8")
    assert f"stpipe: {stpipe.__version__}" in out


def test_cli_main():
    out = subprocess.check_output(["stpipe", "--version"]).decode("utf-8")
    assert f"stpipe: {stpipe.__version__}" in out
