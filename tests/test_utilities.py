import pytest

from stpipe import Step
from stpipe.utilities import import_class, import_func


def test_func():
    pass


class HovercraftFullOfEels:
    pass

class Foo(Step):

    def process(self, input_data):
        pass


def test_import_class():
    from stpipe import Step
    step_class = import_class("stpipe.Step", subclassof=Step)
    assert step_class is Step


def test_import_class_on_func():
    with pytest.raises(TypeError):
        import_class("test_utilities.test_func", subclassof=Step)


def test_import_class_not_subclass():
    with pytest.raises(TypeError):
        import_class("test_utilities.HovercraftFullOfEels", subclassof=Step)


def test_import_func():
    step_func = import_func("test_utilities.test_func")
    assert step_func is test_func


def test_import_func_on_class():
    with pytest.raises(TypeError):
        import_func("test_utilities.HovercraftFullOfEels")


def test_import_class_no_module():
    with pytest.raises(ImportError):
        import_class("Foo", subclassof=Step)
