import warnings
from collections import namedtuple

import importlib_metadata

STEPS_GROUP = "stpipe.steps"


StepInfo = namedtuple(
    "StepInfo",
    ["class_name", "class_alias", "is_pipeline", "package_name", "package_version"],
)


def get_steps():
    """
    Get the list of steps registered with stpipe's entry point group.  Each entry
    point is expected to return a list of tuples, where the first tuple element
    is a fully-qualified Step subclass name, the second element is an optional
    class alias, and the third is a bool indicating whether the class is to be
    listed as a pipeline in the CLI output.

    Returns
    -------
    list of StepInfo
    """
    steps = []

    for entry_point in importlib_metadata.entry_points(group=STEPS_GROUP):
        package_name = entry_point.dist.name
        package_version = entry_point.dist.version
        package_steps = []

        try:
            elements = entry_point.load()()
            package_steps = [
                StepInfo(*element, package_name, package_version)
                for element in elements
            ]

        except Exception as e:
            warnings.warn(
                f"{STEPS_GROUP} plugin from package {package_name}=={package_version} "
                "failed to load:\n\n"
                f"{e.__class__.__name__}: {e}",
                stacklevel=2,
            )

        steps.extend(package_steps)

    return steps
