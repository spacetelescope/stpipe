"""
Pre- and post-hooks
"""

import ast
import inspect

from . import function_wrapper, utilities
from .step import Step


def hook_from_string(step, hooktype, num, command):
    """
    Generate hook from string, function, Step or Step instance

    Parameters
    ----------
    step : `stpipe.step.Step`
        Parent step instance to which this hook is attached, i.e. "self"
    hooktype : str, "pre" or "post"
        Type of hook pre-hook , or post-hook
    num : int
        The number, in order, of the pre- or post-hook in the list
    command : str or `stpipe.step.Step` instance

    Returns
    -------
    `stpipe.step.Step`
    """
    name = f"{hooktype}_hook{num:d}"

    step_class = None
    step_func = None

    # transfer output_ext to hooks
    kwargs = dict(output_ext=step.output_ext)

    # hook is a string of the fully-qualified name of a class or function
    if isinstance(command, str):
        try:
            # String points to a Step subclass
            step_class = utilities.import_class(
                command, subclassof=Step, config_file=step.config_file
            )
        except ImportError:
            # String is possibly a subproc, so handle this later
            pass
        except AttributeError:
            # String points to an instance of a Step
            # So import the class
            class_string, _, params = command.partition("(")
            step_class = utilities.import_class(
                class_string, subclassof=Step, config_file=step.config_file
            )
            # Then convert rest of string to args and instantiate the class
            kwargs_string = params.strip(")")
            expr = ast.parse(f"dict({kwargs_string}\n)", mode="eval")
            kwargs.update(
                {kw.arg: ast.literal_eval(kw.value) for kw in expr.body.keywords}
            )
            return step_class(**kwargs)
        except TypeError:
            # String points to a function
            step_func = utilities.import_func(command)
        else:
            if step_class.class_alias is not None:
                name = step_class.class_alias
            return step_class(name, parent=step, config_file=step.config_file, **kwargs)

        # hook is a string of the fully-qualified name of a function
        if step_func is not None:
            return function_wrapper.FunctionWrapper(
                step_func, parent=step, config_file=step.config_file, **kwargs
            )

    # hook is an already-imported Step subclass
    if inspect.isclass(command) and issubclass(command, Step):
        step_class = command
        if step_class.class_alias is not None:
            name = step_class.class_alias
        return step_class(name, parent=step, config_file=step.config_file, **kwargs)

    # hook is an instance of a Step subclass
    if isinstance(command, Step):
        if command.class_alias is not None:
            command.name = command.class_alias
        else:
            command.name = name
        return command

    # hook is a command-line script or system call
    from .subproc import SystemCall

    return SystemCall(name, parent=step, command=command, **kwargs)


def get_hook_objects(step, hooktype, hooks):
    """
    Get list of pre- or post-hooks for a step

    Parameters
    ----------
    step : `stpipe.step.Step`
        instance to which this is a hook
    hooktype : str, "pre" or "post"
        strings, to indicate whether it is a pre- or post-hook
    hooks : str or class
        path to executable script, or Step class to run as hook

    Returns
    -------
    list of callables that can be run as a hook
    """
    return [hook_from_string(step, hooktype, i, hook) for i, hook in enumerate(hooks)]
