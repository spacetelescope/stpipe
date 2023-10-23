from typing import Optional, Protocol, Union, runtime_checkable


class _Base(Protocol):
    @property
    def crds_observatory(self) -> str:
        """This should return a string identifying the observatory as CRDS expects it"""

    def save(
        self,
        path: Union[str, callable, None] = None,
        dir_path: Optional[str] = None,
        *args,
        **kwargs,
    ) -> str:
        """
        Save to a file.

        Parameters
        ----------
        path : string or callable (optional)
            - If None, use default for model, `model.meta.filename`
            - If str, used as prefix for file path
            - If function, it takes in two arguments that is
              `model.meta.filename` and an `index`, returning a full file name.

        dir_path : str (optional)
            Directory to save to. If not None, this will override
            any directory information in the `path`

        Returns
        -------
        output_path: str
            The file path the model was saved in.
        """


@runtime_checkable
class DataModel(_Base, Protocol):
    @property
    def get_crds_parameters(self) -> dict[str, any]:
        """
        This should return a dictionary of key/value pairs corresponding to the
        parkey values CRDS is using to match reference files. Typically it returns
        all metadata simple values.
        """


@runtime_checkable
class ModelContainer(_Base, Protocol):
    def __iter__(self) -> iter:
        """
        Method to iterate over the models in the container
            This is so it can function like a Sequence/List of models
        """

    @staticmethod
    def read_asn(filepath: str) -> any:
        """
        Load from an association file.

        Parameters
        ----------
        filepath : str
            The path to an association file.
        """

    def from_asn(self, asn_data: dict, asn_file_path: Optional[str] = None):
        """
        Load files from an association file.
        Parameters
        ----------
        asn_data: dictionary
            An association dictionary.
        asn_file_path : str or None
            Filepath of the association, if known.
        """
