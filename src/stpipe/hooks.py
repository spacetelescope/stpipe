"""
Pre- and post-hooks
"""
import types

from .step import Step
from . import utilities

def hook_from_string(step, type, num, command):
    name = '{0}_hook{1:d}'.format(type, num)

    step_class = None
    try:
        step_class = utilities.import_class(
            command, Step, step.config_file)
    except Exception:
        pass

    if step_class is not None:
        return step_class(
            name, parent=step, config_file=step.config_file)

    step_func = None
    try:
        step_func = utilities.import_class(
            command, types.FunctionType, step.config_file)
    except Exception:
        pass

    if step_func is not None:
        from . import function_wrapper
        return function_wrapper.FunctionWrapper(
            step_func, parent=step, config_file=step.config_file)

    from .subproc import SystemCall

    return SystemCall(name, parent=step, command=command)


def get_hook_objects(step, type, hooks):
    return [hook_from_string(step, type, i, hook)
            for i, hook in enumerate(hooks)]
