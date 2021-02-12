import pytest

from stpipe.cli import handle_args
from stpipe import entry_points
from stpipe.entry_points import StepInfo


@pytest.fixture(autouse=True)
def monkey_patch_get_steps(monkeypatch):
    def _get_steps():
        return [
            StepInfo("jwst.pipeline.Ami3Pipeline", "calwebb_ami3", True, "jwst", "0.18.4"),
            StepInfo("jwst.pipeline.Coron3Pipeline", "calwebb_coron3", True, "jwst", "0.18.4"),
            StepInfo("jwst.pipeline.DarkPipeline", "calwebb_dark", True, "jwst", "0.18.4"),
            StepInfo("jwst.step.AlignRefsStep", None, False, "jwst", "0.18.4"),
            StepInfo("jwst.step.AmiAnalyzeStep", None, False, "jwst", "0.18.4"),
            StepInfo("jwst.step.AmiAverageStep", None, False, "jwst", "0.18.4"),
            StepInfo("romancal.pipeline.SomeRomanPipeline", None, True, "romancal", "0.1.1"),
            StepInfo("romancal.step.FlatFieldStep", None, False, "romancal", "0.1.1"),
        ]

    monkeypatch.setattr(entry_points, "get_steps", _get_steps)


def assert_captured_steps(captured, class_names):
    captured_class_names = []

    content = captured.out.strip()
    if content != "":
        captured_class_names.extend([line.split(" ")[0] for line in content.split("\n")])

    assert captured_class_names == class_names


def test_no_arguments(capsys):
    assert handle_args(["list"]) == 0

    assert_captured_steps(capsys.readouterr(), [
        "jwst.pipeline.Ami3Pipeline",
        "jwst.pipeline.Coron3Pipeline",
        "jwst.pipeline.DarkPipeline",
        "jwst.step.AlignRefsStep",
        "jwst.step.AmiAnalyzeStep",
        "jwst.step.AmiAverageStep",
        "romancal.pipeline.SomeRomanPipeline",
        "romancal.step.FlatFieldStep",
    ])


def test_pipelines_only(capsys):
    assert handle_args(["list", "--pipelines-only"]) == 0

    assert_captured_steps(capsys.readouterr(), [
        "jwst.pipeline.Ami3Pipeline",
        "jwst.pipeline.Coron3Pipeline",
        "jwst.pipeline.DarkPipeline",
        "romancal.pipeline.SomeRomanPipeline",
    ])


def test_steps_only(capsys):
    assert handle_args(["list", "--steps-only"]) == 0

    assert_captured_steps(capsys.readouterr(), [
        "jwst.step.AlignRefsStep",
        "jwst.step.AmiAnalyzeStep",
        "jwst.step.AmiAverageStep",
        "romancal.step.FlatFieldStep",
    ])


def test_filter_class_names(capsys):
    assert handle_args(["list", "romancal.*"]) == 0

    assert_captured_steps(capsys.readouterr(), [
        "romancal.pipeline.SomeRomanPipeline",
        "romancal.step.FlatFieldStep",
    ])

    # Should be case-insensitive:
    assert handle_args(["list", "*.ami*"]) == 0

    assert_captured_steps(capsys.readouterr(), [
        "jwst.pipeline.Ami3Pipeline",
        "jwst.step.AmiAnalyzeStep",
        "jwst.step.AmiAverageStep",
    ])


def test_filter_aliases(capsys):
    assert handle_args(["list", "calwebb*"]) == 0

    assert_captured_steps(capsys.readouterr(), [
        "jwst.pipeline.Ami3Pipeline",
        "jwst.pipeline.Coron3Pipeline",
        "jwst.pipeline.DarkPipeline",
    ])
