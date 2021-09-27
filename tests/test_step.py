"""Test step.Step"""
import pytest

import asdf

import stpipe.config_parser as cp
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

    step_defs = {'step1': SimpleStep}


@pytest.fixture()
def config_file(tmpdir):
    """Create a config file"""
    config_file = str(tmpdir / 'simple_step.asdf')

    tree = {
        'class': 'test_step.SimpleStep',
        'name': 'SimpleStep',
        'parameters': {
            'str1' : 'from config',
            'str2' : 'from config'
        }
    }
    af = asdf.AsdfFile(tree)
    af.write_to(config_file)
    return config_file


@pytest.fixture
def mock_step_crds(monkeypatch):
    """Mock various crds calls from Step"""

    def mock_get_config_from_reference(dataset, disable=None):
        if dataset == 'step':
            config = cp.config_from_dict({'str1': 'from crds', 'str2': 'from crds', 'str3': 'from crds'})
        elif dataset == 'pipe':
            config = cp.config_from_dict({
                'str1': 'from crds', 'str2': 'from crds', 'str3': 'from crds',
                'steps' : {
                    'step1': {'str1': 'from crds', 'str2': 'from crds', 'str3': 'from crds'},
                }
            })
        else:
            raise RuntimeError(f'No return defined for {dataset}')
        return config

    monkeypatch.setattr(SimpleStep, 'get_config_from_reference', mock_get_config_from_reference)


# #####
# Tests
# #####
def test_build_config_pip_default():
    """Test for empty config"""
    config, config_file = SimplePipe.build_config(None)
    assert not config_file
    assert not len(config)


def test_build_config_step_config_file(mock_step_crds, config_file):
    """Test that local config overrides defaults and CRDS-supplied file"""
    config, returned_config_file = SimpleStep.build_config('step', config_file=config_file)
    assert returned_config_file == config_file
    assert config['str1'] == 'from config'
    assert config['str2'] == 'from config'
    assert config['str3'] == 'from crds'


def test_build_config_step_crds(mock_step_crds):
    """Test override of a CRDS configuration"""
    config, config_file = SimpleStep.build_config('step')
    assert not config_file
    assert len(config) == 3
    assert config['str1'] == 'from crds'
    assert config['str2'] == 'from crds'
    assert config['str3'] == 'from crds'


def test_build_config_step_default():
    """Test for empty config"""
    config, config_file = SimpleStep.build_config(None)
    assert not config_file
    assert not len(config)

def test_build_config_step_kwarg(mock_step_crds, config_file):
    """Test that kwargs override everything"""
    config, returned_config_file = SimpleStep.build_config('step', config_file=config_file, str1='from kwarg')
    assert returned_config_file == config_file
    assert config['str1'] == 'from kwarg'
    assert config['str2'] == 'from config'
    assert config['str3'] == 'from crds'
