import sys

from stpipe import cmdline
from stpipe.cli.main import _print_versions
from stpipe.exceptions import StpipeExitException


def main():
    """
    Run Steps from the command line

    Exit Status
    -----------
        0:  Step completed satisfactorily
        1:  General error occurred

    Other status codes are Step implementation-specific.
    """
    if "--version" in sys.argv:
        _print_versions()
        sys.exit(0)

    try:
        cmdline.step_from_cmdline(sys.argv[1:])
    except StpipeExitException as e:
        sys.exit(e.exit_status)
    except Exception:
        import traceback

        traceback.print_exc()
        sys.exit(1)
