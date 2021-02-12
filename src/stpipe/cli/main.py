"""
Main function and argument parser for stpipe.
"""
import argparse
import sys
import traceback

from .list import ListCommand
from ..exceptions import StpipeExitException


# New subclasses of Command must be imported
# and appended to this list before they'll
# become available in the CLI:
_COMMAND_CLASSES = [
    ListCommand,
]


def handle_args(raw_args):
    """
    Parse CLI arguments and run the command.  Does not catch exceptions.

    Parameters
    ----------
    raw_args : list of str
        Command-line arguments (excluding the "stpipe" command itself).

    Returns
    -------
    int
        Exit status.
    """
    parser = _get_parser()
    args = parser.parse_args(raw_args)

    if args.version:
        _print_versions()
        return 0

    if args.command_name is None:
        parser.print_help()
        return 0

    command_class = next(c for c in _COMMAND_CLASSES if c.get_name() == args.command_name)

    return command_class.run(args)


def main():
    """
    Main function for stpipe CLI.  Registered with the console_scripts
    entry point as 'stpipe'.  Also called from stpipe.__main__.

    Raises
    ------
    SystemExit
        In all scenarios.
    """
    try:
        sys.exit(handle_args(sys.argv[1:]))
    except StpipeExitException as e:
        sys.exit(e.exit_status)
    except Exception:
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


def _get_parser():
    parser = argparse.ArgumentParser("stpipe", description="stpipe CLI")
    parser.add_argument("-v", "--version", help="print version information and exit", action="store_true")

    subparsers = parser.add_subparsers(dest="command_name", title="commands")

    for command_class in _COMMAND_CLASSES:
        command_class.add_subparser(subparsers)

    return parser


def _print_versions():
    """
    Print stpipe version as well as versions of any packages
    that register an stpipe.steps entry point.
    """
    from .. import entry_points
    import stpipe

    packages = sorted({(s.package_name, s.package_version) for s in entry_points.get_steps()}, key=lambda tup: tup[0])

    print(f"stpipe: {stpipe.__version__}")
    for package_name, package_version in packages:
        print(f"{package_name}: {package_version}")
