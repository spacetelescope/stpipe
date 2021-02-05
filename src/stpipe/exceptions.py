class StpipeException(Exception):
    """
    Base class for exceptions from the stpipe package.
    """
    pass


class NoDataOnDetectorError(StpipeException):
    """WCS solution indicates no data on detector

    When WCS solutions are available, the solutions indicate that no data
    will be present, raise this exception.

    Specific example is for NIRSpec and the NRS2 detector. For various
    configurations of the MSA, it is possible that no dispersed spectra will
    appear on NRS2. This is not a failure of calibration, but needs to be
    called out in order for the calling architecture to be aware of this.
    """

    def __init__(self, message=None):
        if message is None:
            message = 'WCS solution indicates that no science is in the data.'
        super().__init__(message)
