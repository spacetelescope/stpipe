"""
Pre- and post-hooks
"""
import contextlib
import inspect
import types

from . import utilities
from .step import Step


def hook_from_string_or_class(step, type, num, command):
    """
    Generate hook from string (or pass along the class)

    Parameters
    ----------
    step : `stpipe.step.Step`
        Parent step instance to which this hook is attached, i.e. "self"
    type : str, "pre" or "post"
        Type of hook pre-hook , or post-hook
    num : int
        The number, in order, of the pre- or post-hook in the list
    command : str or `stpipe.step.Step` instance

    Returns
    -------
    `stpipe.step.Step`

    """
    name = f"{type}_hook{num:d}"

    step_class = None

    # hook is a string of the fully-qualified name of a class, i.e. from strun
    if isinstance(command, str):
        try:
            step_class = utilities.import_class(command, subclassof=Step, config_file=step.config_file)
        except ImportError:
            pass
        else:
            name = step_class.class_alias
            return step_class(name, parent=step, config_file=step.config_file)

    # hook is an already-imported Step subclass
    if inspect.isclass(command) and issubclass(command, Step):
        step_class = command
        name = step_class.class_alias
        return step_class(name, parent=step, config_file=step.config_file)

    # hook is an instance of a Step subclass
    if isinstance(command, Step):
        command.name = command.class_alias
        return command

    # hook is a string of the fully-qualified name of a function not subclassing Step
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

    # hook is a command-line script of some sort
    from .subproc import SystemCall

    return SystemCall(name, parent=step, command=command)


def get_hook_objects(step, type, hooks):
    """
    Get list of pre- or post-hooks for a step

    Parameters
    ----------
    step : `stpipe.step.Step`
        instance to which this is a hook
    type : str, "pre" or "post"
        strings, to indicate whether it is a pre- or post-hook
    hooks : str or class
        path to executible script, or Step class to run as hook

    Returns
    -------
    list of callables that can be run as a hook
    """
    return [hook_from_string_or_class(step, type, i, hook) for i, hook in enumerate(hooks)]
