"""
Support for the new 'stpipe' CLI (see stpipe.cmdline for the
implementation of 'strun').
"""
from .main import handle_args


__all__ = ["handle_args"]
