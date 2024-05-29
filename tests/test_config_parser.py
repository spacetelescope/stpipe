import contextlib
import warnings
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


@pytest.mark.parametrize(
    "action", ["default", "error", "ignore", "always", "module", "once"]
)
def test_validate_extra_value_warning(action, monkeypatch):
    """Test that extra values in the configuration raise warnings.

    The warning behavior can be configured by modifying the
    EXTRA_VALUE_WARNING_ACTION switch for the module
    """
    config = ConfigObj({"expected": True, "unexpected": False})

    class MockStep:
        spec = "expected = boolean(default=False) # Expected parameter"

    spec = config_parser.load_spec_file(MockStep)

    monkeypatch.setattr(
        config_parser, "EXTRA_VALUE_WARNING_ACTION", action
    )
    if action == "error":
        # Error is raised
        with pytest.raises(
            config_parser.ValidationError, match="Extra value 'unexpected'"
        ):
            config_parser.validate(config, spec)
    elif action == "ignore":
        # No warnings or errors issued
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            config_parser.validate(config, spec)
    else:
        # Warning is issued
        with pytest.warns(
            config_parser.ValidationError, match="Extra value 'unexpected'"
        ):
            config_parser.validate(config, spec)
