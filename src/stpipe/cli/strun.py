#!/usr/bin/env python

"""
Run Steps from the command line

Exit Status
-----------
    0:  Step completed satisfactorily
    1:  General error occurred

Other status codes are Step implementation-specific.
"""

import sys

from stpipe import Step
from stpipe.cli.main import _print_versions
from stpipe.exceptions import StpipeExitException

if __name__ == "__main__":
    if "--version" in sys.argv:
        _print_versions()
        sys.exit(0)

    try:
        step = Step.from_cmdline(sys.argv[1:])
    except StpipeExitException as e:
        sys.exit(e.exit_status)
    except Exception:
        import traceback

        traceback.print_exc()
        sys.exit(1)
