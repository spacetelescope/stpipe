import pytest

from stpipe import Step
from stpipe.utilities import import_class, import_func, resolve_step_class_alias


def what_is_your_quest():
    pass


class HovercraftFullOfEels:
    pass


class Foo(Step):
    class_alias = "foo_step"

    def process(self, input_data):
        pass


def test_import_class():
    from stpipe import Step

    step_class = import_class("stpipe.Step", subclassof=Step)
    assert step_class is Step


def test_import_class_on_func():
    with pytest.raises(TypeError):
        import_class("test_utilities.what_is_your_quest", subclassof=Step)


def test_import_class_not_subclass():
    with pytest.raises(TypeError):
        import_class("test_utilities.HovercraftFullOfEels", subclassof=Step)


def test_import_func():
    step_func = import_func("test_utilities.what_is_your_quest")
    assert step_func is what_is_your_quest


def test_import_func_on_class():
    with pytest.raises(TypeError):
        import_func("test_utilities.HovercraftFullOfEels")


def test_import_class_no_module():
    with pytest.raises(ImportError):
        import_class("Foo", subclassof=Step)


def test_import_func_no_module():
    with pytest.raises(ImportError):
        import_func("foo")


@pytest.fixture()
def mock_entry_points(monkeypatch, request):
    # as the test class above isn't registered via an entry point
    # we mock the entry points here
    class FakeDist:
        def __init__(self, name):
            self.name = name
            self.version = "dev"

    class FakeEntryPoint:
        def __init__(self, dist_name, steps):
            self.dist = FakeDist(dist_name)
            self.steps = steps

        def load(self):
            def loader():
                return self.steps

            return loader

    def fake_entrypoints(group=None):
        return [FakeEntryPoint(k, v) for k, v in request.param.items()]

    import importlib_metadata

    monkeypatch.setattr(importlib_metadata, "entry_points", fake_entrypoints)
    yield


@pytest.mark.parametrize("name", ("foo_step", "stpipe::foo_step"))
@pytest.mark.parametrize(
    "mock_entry_points", [{"stpipe": [("Foo", "foo_step", False)]}], indirect=True
)
def test_class_alias_lookup(name, mock_entry_points):
    """
    Test that a step name can be resolved if either:
        - only a single step is found that matches
        - a step is found and a valid package name was provided
    """
    assert resolve_step_class_alias(name) == "Foo"


@pytest.mark.parametrize("name", ("bar_step", "other_package::foo_step"))
@pytest.mark.parametrize(
    "mock_entry_points", [{"stpipe": [("Foo", "foo_step", False)]}], indirect=True
)
def test_class_alias_lookup_fallthrough(name, mock_entry_points):
    """
    Test that passing in an unknown class alias or an alias scoped
    to a different package falls through to returning the unresolved
    class_alias (to match previous behavior).
    """
    assert resolve_step_class_alias(name) == name


@pytest.mark.parametrize("name", ("aaa::foo_step", "zzz::foo_step"))
@pytest.mark.parametrize(
    "mock_entry_points",
    [
        {
            "aaa": [("Foo", "foo_step", False)],
            "zzz": [("Foo", "foo_step", False)],
        }
    ],
    indirect=True,
)
def test_class_alias_lookup_scoped(name, mock_entry_points):
    """
    Test the lookup succeeds if more than 1 package
    provides a matching step name but the "scope" (package name)
    is provided on lookup.
    """
    assert resolve_step_class_alias(name) == "Foo"


@pytest.mark.parametrize(
    "mock_entry_points",
    [
        {
            "aaa": [("Foo", "foo_step", False)],
            "zzz": [("Foo", "foo_step", False)],
        }
    ],
    indirect=True,
)
def test_class_alias_lookup_conflict(mock_entry_points):
    """
    Test that an ambiguous lookup (a class alias that resolves
    to more than 1 step from different packages) results in
    an error.
    When the package name is provided, tes
    """
    with pytest.raises(ValueError) as err:
        resolve_step_class_alias("foo_step")
    assert err.match("aaa::foo_step")
    assert err.match("zzz::foo_step")
