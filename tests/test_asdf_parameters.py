"""Test initializing steps using ASDF and CRDS"""

import pathlib

import asdf
import pytest

from steps import MakeListPipeline, MakeListStep
from stpipe import Step
from stpipe.config import StepConfig
from stpipe.config_parser import ValidationError

DEFAULT_PAR1 = 42.0
DEFAULT_PAR2 = "Yes, a string"
DEFAULT_RESULT = [DEFAULT_PAR1, DEFAULT_PAR2, False]

_dir = pathlib.Path(__file__).parent


def get_pkg_data_filename(fn):
    return str(_dir / fn)


def test_asdf_roundtrip_pipeline(tmp_cwd, disable_crds_steppars):
    """Save a Pipeline pars and re-instantiate with the save parameters"""

    # Save the parameters
    par_path = "mkp_pars.asdf"
    args = [
        "steps.MakeListPipeline",
        "a.fits",
        "b",
        "--steps.make_list.par1",
        "10.",
        "--steps.make_list.par2",
        "par2",
        "--save-parameters",
        par_path,
    ]
    Step.from_cmdline(args)

    # Rerun with the parameter file
    # Initial condition is that `Step.from_cmdline`
    # succeeds.
    args = [par_path, "a.fits", "b"]
    step = Step.from_cmdline(args)

    # As a secondary condition, ensure the required parameter
    # `par2` is set.
    assert step.make_list.par2 == "par2"


def test_asdf_from_call():
    """Test using an ASDF file from call"""
    config_file = get_pkg_data_filename(
        "steps/jwst_generic_pars-makeliststep_0001.asdf"
    )
    results = MakeListStep.call(config_file=config_file)

    assert results == DEFAULT_RESULT


def test_from_command_line():
    """Test creating Step from command line using ASDF"""
    config_file = get_pkg_data_filename(
        "steps/jwst_generic_pars-makeliststep_0001.asdf"
    )
    args = [config_file]
    step = Step.from_cmdline(args)
    assert isinstance(step, MakeListStep)
    assert step.par1 == 42.0
    assert step.par2 == "Yes, a string"

    results = step.run()
    assert results == DEFAULT_RESULT


def test_from_command_line_override():
    """Test creating Step from command line using ASDF"""
    config_file = get_pkg_data_filename(
        "steps/jwst_generic_pars-makeliststep_0001.asdf"
    )
    args = [config_file, "--par1=0."]
    step = Step.from_cmdline(args)
    assert isinstance(step, MakeListStep)
    assert step.par1 == 0.0
    assert step.par2 == "Yes, a string"

    results = step.run()
    assert results == [0.0, DEFAULT_PAR2, False]


def test_makeliststep_missingpars():
    """Test the testing step class when given insufficient information"""
    with pytest.raises(ValidationError):
        MakeListStep.call()


def test_makeliststep_test():
    """Test the testing step class for basic operation"""
    result = MakeListStep.call(par1=DEFAULT_PAR1, par2=DEFAULT_PAR2)

    assert result == DEFAULT_RESULT


def test_step_from_asdf():
    """Test initializing step completely from config"""
    config_file = get_pkg_data_filename(
        "steps/jwst_generic_pars-makeliststep_0001.asdf"
    )
    step = Step.from_config_file(config_file)
    assert isinstance(step, MakeListStep)
    assert step.name == "make_list"

    results = step.run()
    assert results == DEFAULT_RESULT


def test_step_from_asdf_api_override():
    """Test initializing step completely from config"""
    config_file = get_pkg_data_filename(
        "steps/jwst_generic_pars-makeliststep_0001.asdf"
    )
    results = MakeListStep.call(config_file=config_file, par1=0.0)
    assert results == [0.0, DEFAULT_PAR2, False]


def test_makeliststep_call_config_file():
    """Test override step asdf with .cfg"""
    config_file = get_pkg_data_filename("steps/makelist.cfg")
    results = MakeListStep.call(config_file=config_file)
    assert results == [43.0, "My hovercraft is full of eels.", False]


def test_makeliststep_call_from_within_pipeline():
    """Test override step asdf with .cfg"""
    config_file = get_pkg_data_filename("steps/makelist_pipeline.cfg")
    results = MakeListPipeline.call(config_file=config_file)
    assert results == [43.0, "My hovercraft is full of eels.", False]


def test_step_from_asdf_noname():
    """Test initializing step completely from config without a name specified"""
    root = "jwst_generic_pars-makeliststep_0002"
    config_file = get_pkg_data_filename(f"steps/{root}.asdf")
    step = Step.from_config_file(config_file)
    assert isinstance(step, MakeListStep)
    assert step.name == root

    results = step.run()
    assert results == DEFAULT_RESULT


def test_saving_pars(tmp_path):
    """Save the step parameters from the commandline"""
    cfg_path = get_pkg_data_filename("steps/jwst_generic_pars-makeliststep_0002.asdf")
    saved_path = tmp_path / "savepars.asdf"
    Step.from_cmdline([cfg_path, "--save-parameters", str(saved_path)])
    assert saved_path.exists()

    with asdf.open(
        get_pkg_data_filename("steps/jwst_generic_pars-makeliststep_0002.asdf")
    ) as af:
        original_config = StepConfig.from_asdf(af)
        original_config.parameters["par3"] = False

    with asdf.open(str(saved_path)) as af:
        config = StepConfig.from_asdf(af)
        assert config.parameters == original_config.parameters


@pytest.mark.parametrize(
    "step_obj, expected",
    [
        (
            MakeListStep(par1=0.0, par2="from args"),
            StepConfig(
                "steps.MakeListStep",
                "MakeListStep",
                {
                    "pre_hooks": [],
                    "post_hooks": [],
                    "output_ext": "asdf",
                    "output_use_model": False,
                    "output_use_index": True,
                    "save_results": False,
                    "skip": False,
                    "search_output_file": True,
                    "input_dir": "",
                    "par1": 0.0,
                    "par2": "from args",
                    "par3": False,
                },
                [],
            ),
        ),
    ],
)
def test_export_config(step_obj, expected, tmp_path):
    """Test retrieving of configuration parameters"""
    config_path = tmp_path / "config.asdf"
    step_obj.export_config(config_path)

    with asdf.open(config_path) as af:
        # StepConfig has an __eq__ implementation but we can't use it
        # due to differences between asdf 2.7 and 2.8 in serializing None
        # values.  This can be simplified once the minimum asdf requirement
        # is changed to >= 2.8.
        # assert StepConfig.from_asdf(af) == expected
        config = StepConfig.from_asdf(af)
        assert config.class_name == expected.class_name
        assert config.name == expected.name
        assert config.steps == expected.steps
        parameters = set(expected.parameters.keys()).union(
            set(config.parameters.keys())
        )
        for parameter in parameters:
            assert config.parameters.get(parameter) == expected.parameters.get(
                parameter
            )


@pytest.mark.parametrize(
    "cfg_file, expected_reftype",
    [
        ("local_class.cfg", "pars-withdefaultsstep"),
        ("jwst_generic_pars-makeliststep_0002.asdf", "pars-makeliststep"),
    ],
)
def test_reftype(cfg_file, expected_reftype):
    """Test that reftype is produced as expected"""
    step = Step.from_config_file(get_pkg_data_filename(f"steps/{cfg_file}"))
    assert step.__class__.get_config_reftype() == expected_reftype
    assert step.get_config_reftype() == expected_reftype


def test_step_with_local_class():
    step_fn = get_pkg_data_filename("steps/local_class.cfg")
    step = Step.from_config_file(step_fn)
    assert isinstance(step, Step)
