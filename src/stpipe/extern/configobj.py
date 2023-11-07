import inspect
import sys
import warnings

from astropy.extern import configobj

# Add submodules to system modules so they are available under the same path
for mod in inspect.getmembers(configobj, inspect.ismodule):
    # add as a local variable
    locals()[mod[0]] = mod[1]
    # Add the submodule to the system modules so it can be imported
    sys.modules[f"stpipe.extern.configobj.{mod[0]}"] = mod[1]


warnings.warn(
    "stpipe.extern.configobj is deprecated in favor of astropy.extern.configobj, "
    "please use that instead.",
    DeprecationWarning,
    stacklevel=2,
)
