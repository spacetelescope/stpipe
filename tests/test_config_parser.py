import contextlib
from collections.abc import Mapping

import pytest
from astropy.extern.configobj.configobj import ConfigObj, Section

from stpipe import config_parser
from stpipe.utilities import _not_set


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


@pytest.mark.parametrize("value", [True, False, None, _not_set])
def test_preserve_comments_deprecation(value):
    class Foo:
        spec = """
        # initial comment
        bar = string(default='bam')  # an inline comment (with parentheses)
        # final comment
        """

    # if preserve_comments is _not_set there should be no warning
    if value is _not_set:
        ctx = contextlib.nullcontext()
    else:
        ctx = pytest.warns(DeprecationWarning)

    with ctx:
        spec = config_parser.load_spec_file(Foo, preserve_comments=value)

    assert "initial comment" in spec.initial_comment[0]
    assert "final comment" in spec.final_comment[0]
    assert "inline comment (with parentheses)" in spec.inline_comments["bar"]
