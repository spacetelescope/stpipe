class StpipeException(Exception):
    """
    Base class for exceptions from the stpipe package.
    """
    pass


class StpipeExitException(StpipeException):
    """
    An exception that carries an exit status that is
    returned by stpipe CLI tools.
    """
    def __init__(self, exit_status, *args):
        super().__init__(exit_status, *args)
        self._exit_status = exit_status

    @property
    def exit_status(self):
        return self._exit_status
