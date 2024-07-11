import abc


class Command(abc.ABC):
    """
    Base class for stpipe CLI commands.  Every subclass should
    be added to the _COMMAND_CLASSES list in core.py.
    """

    @classmethod
    def get_name(cls):
        """
        Get this command's name (the first argument to stpipe).

        Returns
        -------
        str
        """

    @classmethod
    def add_subparser(cls, subparsers):
        """
        Add this command's parser to the stpipe subparsers.

        Parameters
        ----------
        subparsers : argparse._SubParsersAction
        """

    @classmethod
    def run(cls, args):
        """
        Run the command with the specified arguments.

        Parameters
        ----------
        args : argparse.Namespace
            Parsed arguments.

        Returns
        -------
        int
            Exit status code.
        """
