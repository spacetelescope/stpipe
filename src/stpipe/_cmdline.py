"""
Various utilities to handle running Steps from the commandline.
"""

import argparse
import logging
import os
import os.path
import textwrap
import warnings

from . import config_parser, log, utilities
from .step import Step, get_disable_crds_steppars

built_in_configuration_parameters = [
    "debug",
    "logcfg",
    "verbose",
    "log-level",
    "log-file",
    "log-stream",
]

logger = logging.getLogger(__name__)


def _print_important_message(header, message, no_wrap=None):
    print("-" * 70)
    print(textwrap.fill(header))
    print(
        textwrap.fill(
            message,
            initial_indent="    ",
            subsequent_indent="    ",
        )
    )
    if no_wrap:
        print(no_wrap)
    print("-" * 70)


def _get_config_and_class(identifier):
    """
    Given a file path to a config file or Python module path, return a
    Step class and a configuration object.
    """
    if os.path.exists(identifier):
        config_file = identifier
        config = config_parser.load_config_file(config_file)
        step_class, name = Step._parse_class_and_name(config, config_file=config_file)
    else:
        try:
            step_class = utilities.import_class(
                utilities.resolve_step_class_alias(identifier), Step
            )
        except (ImportError, AttributeError, TypeError) as err:
            raise ValueError(
                f"{identifier!r} is not a path to a config file or a Python Step class"
            ) from err
        # Don't validate yet
        config = config_parser.config_from_dict({})
        name = None
        config_file = None

    return step_class, config, name, config_file


def _build_parent_arg_parser():
    """Build a top-level argument parser for the command line interface."""
    parser1 = argparse.ArgumentParser(
        description="Run an stpipe Step or Pipeline",
        add_help=False,
    )
    parser1.add_argument(
        "cfg_file_or_class",
        type=str,
        nargs=1,
        help="The configuration file or Python class to run",
    )
    parser1.add_argument(
        "--debug",
        action="store_true",
        help="When an exception occurs, invoke the Python debugger, pdb",
    )
    parser1.add_argument(
        "--save-parameters",
        type=str,
        help="Save step parameters to specified file",
    )
    parser1.add_argument(
        "--disable-crds-steppars",
        action="store_true",
        help="Disable retrieval of step parameter references files from CRDS",
    )
    parser1.add_argument(
        "--logcfg",
        type=str,
        help="DEPRECATED: The logging configuration file to load. "
        "Ignored if verbose or other log arguments are set.",
    )
    parser1.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Turn on all logging messages",
    )
    parser1.add_argument(
        "--log-level",
        type=str,
        default=None,
        help="Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL). "
        "Ignored if 'verbose' is specified.",
    )
    parser1.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Full path to a file name to record log messages",
    )
    parser1.add_argument(
        "--log-stream",
        type=str,
        default=None,
        help="Log stream for terminal messages (stdout, stderr, or null).",
    )
    return parser1


def _build_arg_parser_from_spec(spec, step_class, parent=None):
    """
    Given a configspec, sets up an argparse argument parser that
    understands its arguments.

    The \"path\" in the configspec becomes a dot-separated identifier
    in the commandline arguments.  For example, in the following
    configfile::

        [foo]
          [[bar]]
             baz = 2

    The "baz" variable can be changed with ``--foo.bar.baz=42``.
    """
    # It doesn't translate the configspec types -- it instead
    # will accept any string.  However, the types of the arguments will
    # later be verified by configobj itself.
    parser = argparse.ArgumentParser(
        parents=[parent],
        description=step_class.__doc__,
    )

    def build_from_spec(subspec, parts=None):
        if parts is None:
            parts = []
        for key, val in subspec.items():
            if isinstance(val, dict):
                build_from_spec(val, [*parts, key])
            else:
                comment = subspec.inline_comments.get(key) or ""
                comment = comment.lstrip("#").strip()
                # Only show default value if it is not None or the empty string
                default_value_string = val.split("(")[1].rstrip(")").strip()
                if default_value_string.lstrip("default=") in ["None", "''", '""']:
                    help_string = comment
                else:
                    help_string = f"{comment} [{default_value_string}]"
                argument = "--" + ".".join([*parts, key])
                if argument[2:] in built_in_configuration_parameters:
                    raise ValueError(
                        "The Step's spec is trying to override a built-in parameter"
                        f" {argument!r}"
                    )
                parser.add_argument(
                    "--" + ".".join([*parts, key]),
                    type=str,
                    help=help_string,
                    metavar="",
                )

    build_from_spec(spec)

    parser.add_argument(
        "args",
        nargs="*",
        help="arguments to pass to step",
    )

    return parser


class FromCommandLine(str):
    """
    We need a way to distinguish between config values that come from
    a config file and those that come from the commandline.  For
    example, configfile paths must be resolved against the location of
    the config file.  Commandline paths must be resolved against the
    current working directory.  By setting all commandline overrides
    as instances of this class, we can later (in `config_parser.py`)
    use isinstance to see where the values came from.
    """


def _override_config_from_args(config, args):
    """
    Overrides any configuration values in `config` with values from the
    parsed commandline arguments `args`.
    """

    def set_value(subconf, key, val):
        root, sep, rest = key.partition(".")
        if rest:
            set_value(subconf.setdefault(root, {}), rest, val)
        else:
            val, comment = config._handle_value(val)
            if isinstance(val, str):
                subconf[root] = FromCommandLine(val)
            else:
                subconf[root] = val

    for key, val in vars(args).items():
        if val is not None:
            set_value(config, key, val)


def _print_parser_error(parser, error):
    """
    Print a formatted error message and parser help text.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        The argument parser whose help text will be printed.
    error : Exception
        The error object whose message will be displayed.
    """
    _print_important_message("ERROR PARSING CONFIGURATION:", str(error))
    parser.print_help()


def _config_and_class_from_cmdline(args):
    """
    Parse command line arguments and retrieve step configuration and class.

    Extracts the configuration file or class identifier from command line
    arguments and retrieves the corresponding Step class and configuration.

    Parameters
    ----------
    args : list of str
        Command line arguments.

    Returns
    -------
    step_class : type
        The Step class to be instantiated.
    config : ConfigObj
        The configuration object for the step.
    name : str or None
        The step name from the configuration file, or None.
    config_file : str or None
        Path to the configuration file, or None.
    parser : argparse.ArgumentParser
        The parent argument parser used for parsing.
    known : argparse.Namespace
        The parsed command line arguments.
    """
    parser = _build_parent_arg_parser()
    known, _ = parser.parse_known_args(args)
    try:
        return (*_get_config_and_class(known.cfg_file_or_class[0]), parser, known)
    except Exception as e:
        _print_parser_error(parser, e)
        raise e


def _determine_log_configuration(known):
    """
    Determine and load logging configuration from arguments.

    Parameters
    ----------
    known : argparse.Namespace
        Parsed command line arguments containing logging-related parameters:
        - logcfg: Path to logging configuration file (deprecated)
        - verbose: Enable all logging messages
        - log_level: Specific log level to set
        - log_file: Path to log file
        - log_stream: Output stream for logs

    Returns
    -------
    log_cfg : LogConfig
        The loaded logging configuration ready for use.
    """
    if known.logcfg is not None:
        msg = (
            "The logcfg configuration file is deprecated. "
            "Please use the log_* command line "
            "arguments to configure logging."
        )
        warnings.warn(msg, DeprecationWarning, stacklevel=2)

    # if verbose is enabled
    # or log_level log_file or log_stream are set (not None)
    # then don't try to use the log configuration file (or any passed in log_cfg)
    if known.verbose is True or any(
        getattr(known, attr) is not None
        for attr in ("log_level", "log_file", "log_stream")
    ):
        cfgfile = None
    elif known.logcfg:
        if not os.path.exists(known.logcfg):
            raise OSError(f"Logging config {known.logcfg!r} not found")
        cfgfile = known.logcfg
    else:
        cfgfile = log._find_logging_config_file()

    # determine level
    if known.verbose:
        log_level = "DEBUG"
    elif known.log_level is not None:
        log_level = str(known.log_level).upper()
    else:
        log_level = None

    try:
        log_cfg = log.load_configuration(
            config_file=cfgfile,
            log_level=log_level,
            log_file=known.log_file,
            log_stream=known.log_stream,
        )
    except Exception as e:
        raise ValueError(f"Error parsing logging configuration:\n{e}") from e
    return log_cfg


def _build_step_from_args(step_class, config, name, config_file, parser, known, args):
    """
    Build and configure a Step instance from parsed arguments.

    Creates a Step instance using the provided class and configuration,
    merges in command line overrides, retrieves reference parameters from
    CRDS if an input file is provided, and handles configuration validation.

    Parameters
    ----------
    step_class : type
        The Step class to instantiate.
    config : ConfigObj
        The base configuration object.
    name : str or None
        The step name from configuration.
    config_file : str or None
        Path to the configuration file.
    parser : argparse.ArgumentParser
        The parent argument parser.
    known : argparse.Namespace
        Parsed parent-level command line arguments.
    args : list of str
        Remaining unparsed command line arguments.

    Returns
    -------
    step : Step
        The instantiated and configured Step object.
    positional : list of str
        Positional arguments remaining after parsing.
    """
    # Determine whether CRDS should be queried for step parameters
    disable_crds_steppars = get_disable_crds_steppars(known.disable_crds_steppars)

    # This creates a config object from the spec file of the step class merged with
    # the spec files of the superclasses of the step class and adds arguments for
    # all of the expected reference files

    # load_spec_file is a method of both Step and Pipeline
    spec = step_class.load_spec_file()

    step_arg_parser = _build_arg_parser_from_spec(spec, step_class, parent=parser)

    args = step_arg_parser.parse_args(args)

    del args.cfg_file_or_class
    del args.debug
    del args.save_parameters
    del args.disable_crds_steppars
    del args.logcfg
    del args.verbose
    del args.log_level
    del args.log_file
    del args.log_stream
    positional = args.args
    del args.args

    # This updates config (a ConfigObj) with the values from the command line arguments
    # Config is empty if class specified, otherwise contains values from config file
    # specified on command line
    _override_config_from_args(config, args)

    config = step_class.merge_config(config, config_file)

    if len(positional):
        input_file = positional[0]
        if args.input_dir:
            input_file = args.input_dir + "/" + input_file

        # Attempt to retrieve Step parameters from CRDS
        try:
            parameter_cfg = step_class.get_config_from_reference(
                input_file, disable=disable_crds_steppars
            )
        except (FileNotFoundError, OSError):
            logger.warning("Unable to open input file, cannot get parameters from CRDS")
        else:
            if config:
                config_parser.merge_config(parameter_cfg, config)
            config = parameter_cfg
    else:
        logger.info("No input file specified, unable to retrieve parameters from CRDS")

    # This is where the step is instantiated
    try:
        step = step_class.from_config_section(
            config,
            name=name,
            config_file=config_file,
        )
    except config_parser.ValidationError as e:
        # If the configobj validator failed, print usage information.
        _print_important_message("ERROR PARSING CONFIGURATION:", str(e))
        step_arg_parser.print_help()
        raise ValueError(str(e)) from e

    # Define the primary input file.
    # Always have an output_file set on the outermost step
    if len(positional):
        step.set_primary_input(positional[0])
        step.save_results = True

    # Save the step configuration
    if known.save_parameters:
        step.export_config(known.save_parameters, include_metadata=True)
        logger.info(f"Step/Pipeline parameters saved to '{known.save_parameters}'")

    return step, positional


def step_from_cmdline(args):
    """
    Create a step from a configuration file and run it.

    Parameters
    ----------
    args : list of str
        Commandline arguments


    Returns
    -------
    step : Step instance
        If the config file has a `class` parameter, or the commandline
        specifies a class, the return value will be as instance of
        that class.

        Any parameters found in the config file or on the commandline
        will be set as member variables on the returned `Step`
        instance.
    """
    # determine step class
    step_class, config, name, config_file, parser, known = (
        _config_and_class_from_cmdline(args)
    )

    # determine logging parameters
    try:
        log_cfg = _determine_log_configuration(known)
    except Exception as e:
        _print_parser_error(parser, e)
        raise e

    log_cfg.set_recording_formatter(step_class._log_records_formatter)

    # set up logging context
    with log_cfg.context(step_class.get_stpipe_loggers()):
        # finish parsing args, make class
        step, positional = _build_step_from_args(
            step_class, config, name, config_file, parser, known, args
        )

        # run step
        try:
            step.run(*positional)
        except Exception as e:
            _print_important_message(
                f"ERROR RUNNING STEP {step_class.__name__!r}:", str(e)
            )

            if known.debug:
                import pdb  # noqa: T100

                pdb.post_mortem()
            else:
                raise

    return step
