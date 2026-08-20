import warnings

from ._format_template import *  # noqa: F403

warnings.warn(
    "stpipe.format_template is deprecated. Use f-strings instead.",
    DeprecationWarning,
    stacklevel=2,
)
