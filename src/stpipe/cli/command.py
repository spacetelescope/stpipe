import abc


class Command(abc.ABC):
    """
    Base class for stpipe CLI commands.  Every subclass should
    be added to the _COMMAND_CLASSES list in core.py.
    """

    @abc.abstractmethod
    @classmethod
    def get_name(cls):
        """
        Get this command's name (the first argument to stpipe).

        Returns
        -------
        str
        """

    @abc.abstractmethod
    @classmethod
    def add_subparser(cls, subparsers):
        """
        Add this command's parser to the stpipe subparsers.

        Parameters
        ----------
        subparsers : argparse._SubParsersAction
        """

    @abc.abstractmethod
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
