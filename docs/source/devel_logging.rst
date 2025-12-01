=======
Logging
=======

The logging in stpipe is built on the Python standard library's
`logging` module.  For detailed information about logging, refer to
the documentation there.

Stpipe will pick up and configure any loggers defined by
``stpipe.Step.get_stpipe_loggers``. It is recommended that pipeline developers
include the logger for their project in the list of logger names
returns by that method. If developers follow this recommendation
there is no further actions required to add loggers from project
submodules to the list of stpipe configured loggers due to the
default propagation performed by the python logging module.
By convention, loggers should be named for the module they are used
in. Expanding on this example, all the library code has to do is
use a Python `logging.Logger` as normal::

    import logging

    log = logging.getLogger(__name__)

    def my_library_call():
        # ...
        log.info("I want to make note of something")
        # ...
