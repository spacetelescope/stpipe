import abc
import inspect


class AbstractModelContainer(abc.ABC):
    """
    This Abstract Base Class is intended to cover multiple implementations of
    model containers so that each will be considered an appropriate subclass of this
    class without requiring that they inherit this class.

    Any model container class instance that desires to be considered an instance of
    AbstractModelContainer must implement the following methods.
    """

    @classmethod
    def __subclasshook__(cls, C):
        if cls is not AbstractModelContainer:
            return False
        mro = C.__mro__

        # must provide "crds_observatory"
        if not any(hasattr(CC, "crds_observatory") for CC in mro):
            return False

        # and be iterable
        if not any(hasattr(CC, "__iter__") for CC in mro):
            return False

        # and implement "save"
        if not any(hasattr(CC, "save") for CC in mro):
            return False

        # and that "save" is a function
        save_function = getattr(C, "save")
        if not callable(save_function):
            return False

        # and that "save" accepts the required arguments/parameter
        save_signature = inspect.signature(C.save)
        target_signature = inspect.signature(cls.save)
        for parameter in target_signature.parameters:
            if parameter == 'self':
                pass
            # check that this parameter/argument exists in the save function
            if parameter not in save_signature.parameters:
                return False
            save_parameter = save_signature.parameters[parameter]
            # make sure the required parameter is not positional only
            if save_parameter.kind == inspect.Parameter.POSITIONAL_ONLY:
                return False

        return True

    @property
    @abc.abstractmethod
    def crds_observatory(self):
        """This should return a string identifying the observatory as CRDS expects it"""
        pass

    @abc.abstractmethod
    def save(self, path, save_model_func):
        """
        Save to a file

        Parameters
        ----------
        path : str or callable or None
            - If None, the `meta.filename` is used for each model.
            - If a string, the string is used as a root and an index is
              appended.
            - If a function, the function takes the two arguments:
              the value of model.meta.filename and the
              `idx` index, returning constructed file name.

        save_model_func : callable
            Alternate function to save each model instead of
            the models ``save`` method. Takes one argument, the model,
            and keyword argument ``idx`` for an index.

        Returns
        -------
        output_paths: [str[, ...]]
            List of output file paths of where the models were saved.
        """
        pass
