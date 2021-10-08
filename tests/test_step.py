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
def config_file_pipe(tmpdir):
    """Create a config file"""
    config_file = str(tmpdir / 'simple_pipe.asdf')

    tree = {
        'class': 'test_step.SimplePipe',
        'name': 'SimplePipe',
        'parameters': {
            'str1': 'from config',
            'str2': 'from config'
        },
        'steps': [
            {'class': 'test_step.SimpleStep',
             'name': 'step1',
             'parameters': {
                 'str1' : 'from config',
                 'str2' : 'from config'
             }},
        ]
    }
    with asdf.AsdfFile(tree) as af:
        af.write_to(config_file)
    return config_file


@pytest.fixture()
def config_file_step(tmpdir):
    """Create a config file"""
    config_file = str(tmpdir / 'simple_step.asdf')

    tree = {
        'class': 'test_step.SimpleStep',
        'name': 'SimpleStep',
        'parameters': {
            'str1': 'from config',
            'str2': 'from config'
        }
    }
    with asdf.AsdfFile(tree) as af:
        af.write_to(config_file)
    return config_file


@pytest.fixture
def mock_step_crds(monkeypatch):
    """Mock various crds calls from Step"""
    def mock_get_config_from_reference_pipe(dataset, disable=None):
        config = cp.config_from_dict({
            'str1': 'from crds', 'str2': 'from crds', 'str3': 'from crds',
            'steps' : {
                'step1': {'str1': 'from crds', 'str2': 'from crds', 'str3': 'from crds'},
            }
        })
        return config

    def mock_get_config_from_reference_step(dataset, disable=None):
        config = cp.config_from_dict({'str1': 'from crds', 'str2': 'from crds', 'str3': 'from crds'})
        return config

    monkeypatch.setattr(SimplePipe, 'get_config_from_reference', mock_get_config_from_reference_pipe)
    monkeypatch.setattr(SimpleStep, 'get_config_from_reference', mock_get_config_from_reference_step)


# #####
# Tests
# #####
def test_build_config_pipe_config_file(mock_step_crds, config_file_pipe):
    """Test that local config overrides defaults and CRDS-supplied file"""
    config, returned_config_file = SimplePipe.build_config('science.fits', config_file=config_file_pipe)
    assert returned_config_file == config_file_pipe
    assert config['str1'] == 'from config'
    assert config['str2'] == 'from config'
    assert config['str3'] == 'from crds'
    assert config['steps']['step1']['str1'] == 'from config'
    assert config['steps']['step1']['str2'] == 'from config'
    assert config['steps']['step1']['str3'] == 'from crds'


def test_build_config_pipe_crds(mock_step_crds):
    """Test that CRDS param reffile overrides a default CRDS configuration"""
    config, config_file = SimplePipe.build_config('science.fits')
    assert not config_file
    assert config['str1'] == 'from crds'
    assert config['str2'] == 'from crds'
    assert config['str3'] == 'from crds'
    assert config['steps']['step1']['str1'] == 'from crds'
    assert config['steps']['step1']['str2'] == 'from crds'
    assert config['steps']['step1']['str3'] == 'from crds'


def test_build_config_pipe_default():
    """Test for empty config"""
    config, config_file = SimplePipe.build_config(None)
    assert config_file is None
    assert len(config) == 0


def test_build_config_pipe_kwarg(mock_step_crds, config_file_pipe):
    """Test that kwargs override CRDS and local param reffiles"""
    config, returned_config_file = SimplePipe.build_config('science.fits', config_file=config_file_pipe,
                                                           str1='from kwarg', steps={'step1': {'str1': 'from kwarg'}})
    assert returned_config_file == config_file_pipe
    assert config['str1'] == 'from kwarg'
    assert config['str2'] == 'from config'
    assert config['str3'] == 'from crds'
    assert config['steps']['step1']['str1'] == 'from kwarg'
    assert config['steps']['step1']['str2'] == 'from config'
    assert config['steps']['step1']['str3'] == 'from crds'


def test_build_config_step_config_file(mock_step_crds, config_file_step):
    """Test that local config overrides defaults and CRDS-supplied file"""
    config, returned_config_file = SimpleStep.build_config('science.fits', config_file=config_file_step)
    assert returned_config_file == config_file_step
    assert config['str1'] == 'from config'
    assert config['str2'] == 'from config'
    assert config['str3'] == 'from crds'


def test_build_config_step_crds(mock_step_crds):
    """Test override of a CRDS configuration"""
    config, config_file = SimpleStep.build_config('science.fits')
    assert config_file is None
    assert len(config) == 3
    assert config['str1'] == 'from crds'
    assert config['str2'] == 'from crds'
    assert config['str3'] == 'from crds'


def test_build_config_step_default():
    """Test for empty config"""
    config, config_file = SimpleStep.build_config(None)
    assert config_file is None
    assert len(config) == 0


def test_build_config_step_kwarg(mock_step_crds, config_file_step):
    """Test that kwargs override everything"""
    config, returned_config_file = SimpleStep.build_config('science.fits', config_file=config_file_step, str1='from kwarg')
    assert returned_config_file == config_file_step
    assert config['str1'] == 'from kwarg'
    assert config['str2'] == 'from config'
    assert config['str3'] == 'from crds'
