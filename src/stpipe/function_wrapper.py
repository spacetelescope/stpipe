"""
A Step whose only purpose is to wrap an ordinary function.
"""
from .step import Step


class FunctionWrapper(Step):
    """
    This Step wraps an ordinary Python function.
    """
    def __init__(self, func, *args):
        Step.__init__(self, func.__name__, *args)

        self._func = func

    def process(self, *args):
        return self._func(*args)
