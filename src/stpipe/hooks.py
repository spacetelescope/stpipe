"""
Pre- and post-hooks
"""
import contextlib
import types

from . import utilities
from .step import Step


def hook_from_string(step, type, num, command):  # noqa: A002
    name = f"{type}_hook{num:d}"

    step_class = None
    with contextlib.suppress(Exception):
        step_class = utilities.import_class(command, Step, step.config_file)

    if step_class is not None:
        return step_class(name, parent=step, config_file=step.config_file)

    step_func = None
    with contextlib.suppress(Exception):
        step_func = utilities.import_class(
            command, types.FunctionType, step.config_file
        )

    if step_func is not None:
        from . import function_wrapper

        return function_wrapper.FunctionWrapper(
            step_func, parent=step, config_file=step.config_file
        )

    from .subproc import SystemCall

    return SystemCall(name, parent=step, command=command)


def get_hook_objects(step, type_, hooks):
    return [hook_from_string(step, type_, i, hook) for i, hook in enumerate(hooks)]
