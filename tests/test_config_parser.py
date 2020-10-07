import pytest

from steps import MakeListStep
from stpipe import config_parser
from stpipe.extern.configobj.configobj import ConfigObj

def test_load_config_file_s3(s3_root_dir):
    path = str(s3_root_dir.join("pars-makeliststep.asdf"))
    with MakeListStep.get_pars_model() as model:
        model.save(path)

    result = config_parser.load_config_file("s3://test-s3-data/pars-makeliststep.asdf")
    assert isinstance(result, ConfigObj)

    with pytest.raises(ValueError):
        config_parser.load_config_file("s3://test-s3-data/missing.asdf")
