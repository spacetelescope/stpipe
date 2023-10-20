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

        # must provide "crds_observatory"
        if not hasattr(C, "crds_observatory"):
            return False

        # and be iterable
        if not hasattr(C, "__iter__"):
            return False

        # and implements the functions defined below
        for function_name in ["save", "read_asn", "from_asn"]:
            function = getattr(C, function_name, None)
            if function is None or not callable(function):
                return False

            # check that functionaccepts the required arguments/parameter
            signature = inspect.signature(function)
            target_signature = inspect.signature(getattr(cls, function_name))
            for parameter_name in target_signature.parameters:
                if parameter_name == "self":
                    pass
                # check that this required parameter/argument exists in the function signature
                if parameter_name not in signature.parameters:
                    return False
                parameter = signature.parameters[parameter_name]
                # make sure the required parameter is not positional only
                if parameter.kind == inspect.Parameter.POSITIONAL_ONLY:
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

    @staticmethod
    @abc.abstractmethod
    def read_asn(filepath):
        """
        Load from an association file.

        Parameters
        ----------
        filepath : str
            The path to an association file.
        """
        pass

    @abc.abstractmethod
    def from_asn(self, asn_data, asn_file_path=None):
        """
        Load files from an association file.

        Parameters
        ----------
        asn_data: dictionary
            An association dictionary.

        asn_file_path : str or None
            Filepath of the association, if known.
        """
        pass
