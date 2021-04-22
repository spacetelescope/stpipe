
import abc

class AbstractDataModel(abc.ABC):
    """
    This Abstract Base Class is intended to cover multiple implementations of
    data models so that each will be considered an appropriate subclass of this
    class without requiring that they inherit this class.

    Any datamodel class instance that desires to be considered an instance of
    AbstractDataModel must implement the following methods.

    In addition, although it isn't yet checked (the best approach for supporting
    this is still being considered), such instances must have a meta.filename
    attribute.
    """

    @classmethod
    def __subclasshook__(cls, C):
        """
        Psuedo subclass check based on these attributes and methods
        """
        if cls is AbstractDataModel:
            mro = C.__mro__
            if (any([hasattr(CC, "crds_observatory") for CC in mro]) and
                any([hasattr(CC, "get_crds_parameters") for CC in mro]) and
                any([hasattr(CC, "save") for CC in mro])):
                return True
        return False

    @property
    @abc.abstractmethod
    def crds_observatory(self):
        """This should return a string identifying the observatory as CRDS expects it"""
        pass


    @abc.abstractmethod
    def get_crds_parameters(self):
        """
        This should return a dictionary of key/value pairs corresponding to the
        parkey values CRDS is using to match reference files. Typically it returns
        all metadata simple values.
        """

    @abc.abstractmethod
    def save(self, path, dir_path=None, *args, **kwargs):
        """
        Save to a file.

        Parameters
        ----------
        path : string or callable
            File path to save to.
            If function, it takes one argument that is
            model.meta.filename and returns the full path string.

        dir_path : str
            Directory to save to. If not None, this will override
            any directory information in the `path`

        Returns
        -------
        output_path: str
            The file path the model was saved in.
        """
        pass
