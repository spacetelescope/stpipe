from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    import os
    from collections.abc import Callable


__all__ = ("DataModel",)


@runtime_checkable
class DataModel(Protocol):
    """
    This is a protocol to describe the methods and properties that define a
    DataModel for the purposes of stpipe. This is a runtime checkable protocol
    meaning that any object can be `isinstance` checked against this protocol
    and will succeed even if the object does not inherit from this class.
    Moreover, this object will act as an `abc.ABC` class if it is inherited from.

    Any datamodel class instance that desires to be considered an instance of
    must fully implement the protocol in order to pass the `isinstance` check.

    In addition, although it isn't yet checked (the best approach for supporting
    this is still being considered), such instances must have a meta.filename
    attribute.
    """

    @property
    @abstractmethod
    def crds_observatory(self) -> str:
        """This should return a string identifying the observatory as CRDS expects it"""
        ...

    @property
    @abstractmethod
    def get_crds_parameters(self) -> dict[str, any]:
        """
        This should return a dictionary of key/value pairs corresponding to the
        parkey values CRDS is using to match reference files. Typically it returns
        all metadata simple values.
        """
        ...

    @abstractmethod
    def save(
        self,
        path: os.PathLike | Callable[..., os.PathLike],
        dir_path: os.PathLike | None = None,
        *args,
        **kwargs,
    ) -> os.PathLike:
        """
        Save to a file.

        Parameters
        ----------
        path :
            File path to save to.
            If function, it takes one argument that is
            model.meta.filename and returns the full path string.

        dir_path :
            Directory to save to. If not None, this will override
            any directory information in the ``path``

        Returns
        -------
            The file path the model was saved in.
        """
        ...
