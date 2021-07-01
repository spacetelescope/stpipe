from collections.abc import Mapping

from stpipe import config_parser
from stpipe.extern.configobj.configobj import ConfigObj, Section


def test_merge_config_nested_mapping():
    """
    Test that non-dict Mapping implementations are not
    converted to config sections.
    """
    config = ConfigObj()
    config_parser.merge_config(config, {"foo": {"bar": "baz"}})
    assert isinstance(config["foo"], Section)
    assert config["foo"]["bar"] == "baz"

    class TestMapping(Mapping):
        def __init__(self, delegate):
            self._delegate = delegate

        def __iter__(self):
            return iter(self._delgate)

        def __getitem__(self, key):
            return self._delegate[key]

        def __len__(self):
            return len(self._delegate)

    config = ConfigObj()
    config_parser.merge_config(config, {"foo": TestMapping({"bar": "baz"})})
    assert isinstance(config["foo"], TestMapping)
    assert config["foo"]["bar"] == "baz"
