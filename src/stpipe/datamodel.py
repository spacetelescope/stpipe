
import abc

class DataModel(abc.ABC):
    """
    This Abstract Base Class is intended to cover multiple implmentations of
    data models so that each will be considered an appropriate subclass of this
    class without requiring that they inherit this class.
    """

    @classmethod
    def __subclasshook__(cls, C):
        """
        Psuedo subclass check based on these attributes and methods
        """
        if cls is DataModel:
            mro = C.__mro__
            if (any([hasattr(CC, "crds_observatory") for CC in mro]) and
                any([hasattr(C, "get_crds_parameters") for CC in mro]) and
                any([hasattr(C, "save") for CC in mro])):
                return True
        return False

    @abc.abstractmethod
    def crds_observatory(self):
        pass

    @abc.abstractmethod
    def get_crds_parameters(self):
        pass

    @abc.abstractmethod
    def save(self, path, dir_path=None, *args, **kwargs):
        pass