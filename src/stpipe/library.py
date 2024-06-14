import abc
import copy
import json
import os.path
import tempfile
import warnings
from collections.abc import Iterable, MutableMapping
from pathlib import Path
from types import MappingProxyType

import asdf

__all__ = ["LibraryError", "BorrowError", "ClosedLibraryError", "AbstractModelLibrary"]


class LibraryError(Exception):
    """
    Generic ModelLibrary related exception
    """


class BorrowError(LibraryError):
    """
    Exception indicating an issue with model borrowing
    """


class ClosedLibraryError(LibraryError):
    """
    Exception indicating a library method was used outside of a
    ``with`` context (that "opens" the library).
    """


class _Ledger(MutableMapping):
    """
    A "ledger" used for tracking borrowed out models.

    Each model has a unique "index" in the library because
    the order of the models in the library never changes.
    This "index" can be used to track the model.

    For ease-of-use this ledger maintains 2 mappings:

        - id (the id(model) result) to model index
        - index to model

    The "index to model" mapping keeps a reference to every
    model in the ledger (which allows id(model) to be consistent).

    The ledger is a MutableMapping that supports look up of:
        - index for a model
        - model for an index
    """

    def __init__(self):
        self._id_to_index = {}
        self._index_to_model = {}

    def __getitem__(self, model_or_index):
        if isinstance(model_or_index, int):
            return self._index_to_model[model_or_index]
        return self._id_to_index[id(model_or_index)]

    def __setitem__(self, index, model):
        self._index_to_model[index] = model
        self._id_to_index[id(model)] = index

    def __delitem__(self, model_or_index):
        if isinstance(model_or_index, int):
            index = model_or_index
            model = self._index_to_model[index]
        else:
            model = model_or_index
            index = self._id_to_index[id(model)]
        del self._id_to_index[id(model)]
        del self._index_to_model[index]

    def __iter__(self):
        # only return indexes
        return iter(self._index_to_model)

    def __len__(self):
        return len(self._id_to_index)


class AbstractModelLibrary(abc.ABC):
    """
    A "library" of models (loaded from an association file).

    Do not anger the librarian!

    The library owns all models from the association and it will handle
    opening and closing files.

    Models can be "borrowed" from the library (by iterating through the
    library or "borrowing" a specific model). However the library must be
    "open" (used in a ``with`` context)  to borrow a model and the model
    must be "shelved" before the library "closes" (the ``with`` context exits).

    >>> with library:   # doctest: +SKIP
            model = library.borrow(0)  # borrow the first model
            # do stuff with the model
            library.shelve(model, 0)  # return the model

    Failing to "open" the library will result in a ClosedLibraryError.

    Failing to "return" a borrowed model will result in a BorrowError.
    """

    def __init__(
        self,
        init,
        asn_exptypes=None,
        asn_n_members=None,
        on_disk=False,
        temp_directory=None,
        **datamodels_open_kwargs,
    ):
        self._on_disk = on_disk
        self._open = False
        self._ledger = _Ledger()
        self._loaded_models = {}

        self._datamodels_open_kwargs = datamodels_open_kwargs

        if on_disk:
            if temp_directory is None:
                self._temp_dir = tempfile.TemporaryDirectory(dir="")
                self._temp_path = Path(self._temp_dir.name)
            else:
                self._temp_path = Path(temp_directory)
            self._temp_filenames = {}

        if asn_exptypes is not None:
            # if a single string, treat this as a single item list
            if isinstance(asn_exptypes, str):
                asn_exptypes = [asn_exptypes]
            # convert these to lower case to allow case insensitive matching below
            asn_exptypes = [exptype.lower() for exptype in asn_exptypes]

        if isinstance(init, (str, Path)):
            # init is an association filename (or path)
            asn_path = os.path.abspath(os.path.expanduser(os.path.expandvars(init)))
            self._asn_dir = os.path.dirname(asn_path)

            # load association
            asn_data = self._load_asn(asn_path)
        elif isinstance(init, MutableMapping):
            # we will modify the asn below so do a deep copy
            asn_data = copy.deepcopy(init)
            self._asn_dir = os.path.abspath(".")
        elif isinstance(init, self.__class__):
            raise ValueError(f"Invalid init {init}")
        elif isinstance(init, Iterable):  # assume a list of models
            if on_disk:
                raise ValueError("on_disk cannot be used for a list of models")

            # init is a list of models
            # make a fake asn from the models
            filenames = set()
            members = []
            for index, model_or_filename in enumerate(init):
                if asn_n_members is not None and len(members) == asn_n_members:
                    break
                if isinstance(model_or_filename, (str, Path)):
                    # TODO supporting a list of filenames by opening them as models
                    # has issues, if this is a widely supported mode (vs providing
                    # an association) it might make the most sense to make a fake
                    # association with the filenames at load time.
                    model = self._datamodels_open(
                        model_or_filename, **self._datamodels_open_kwargs
                    )
                else:
                    model = model_or_filename
                exptype = getattr(model.meta, "exptype", "SCIENCE")

                if asn_exptypes is not None and exptype.lower() not in asn_exptypes:
                    continue

                filename = model.meta.filename
                if filename in filenames:
                    raise ValueError(
                        f"Models in library cannot use the same filename: {filename}"
                    )
                filenames.add(filename)

                group_id = self._model_to_group_id(model)

                members.append(
                    {
                        "expname": filename,
                        "exptype": exptype,
                        "group_id": group_id,
                    }
                )

                self._loaded_models[len(self._loaded_models)] = model

            # since we've already filtered by asn type and n members reset these values
            asn_exptypes = None
            asn_n_members = None

            # make a fake association
            asn_data = {
                # TODO other asn information?
                "products": [
                    {
                        "members": members,
                    }
                ],
            }
            self._asn_dir = None
        else:
            raise ValueError(f"Invalid init {init}")

        if asn_exptypes is not None:
            asn_data["products"][0]["members"] = [
                m
                for m in asn_data["products"][0]["members"]
                if m["exptype"] in asn_exptypes
            ]

        if asn_n_members is not None:
            asn_data["products"][0]["members"] = asn_data["products"][0]["members"][
                :asn_n_members
            ]

        self._asn = asn_data
        self._members = self._asn["products"][0]["members"]

        for member in self._members:
            if "group_id" not in member:
                filename = os.path.join(self._asn_dir, member["expname"])
                member["group_id"] = self._filename_to_group_id(filename)

        if not on_disk:
            # if models were provided as input, assign the members here
            # now that the fake asn data is complete
            for i in self._loaded_models:
                self._assign_member_to_model(self._loaded_models[i], self._members[i])

    def __del__(self):
        if hasattr(self, "_temp_dir"):
            self._temp_dir.cleanup()

    @property
    def asn(self):
        """
        Association dictionary used to create the library.

        Note that changes to the models may cause this information
        to fall "out-of-sync" with the models. For example, borrowing
        and changing a models "group_id" metadata will not change
        the "group_id" entry for the member at the same index in the
        association dictionary returned for this property.

        This is "read-only" to reduce the chances that the
        information in this dictionary will conflict with
        the model metadata.
        """

        # return a "read only" association
        def _to_read_only(obj):
            if isinstance(obj, dict):
                return MappingProxyType(obj)
            if isinstance(obj, list):
                return tuple(obj)
            return obj

        return asdf.treeutil.walk_and_modify(self._asn, _to_read_only)

    @property
    def group_names(self):
        """
        A ``set`` of association member "group_id" values

        This property (similar to ``asn``) can fall "out-of-sync"
        with the model metadata. The names returned here will
        only reflect the "group_id" at the time of library creation.
        """
        names = set()
        for member in self._members:
            names.add(member["group_id"])
        return names

    @property
    def group_indices(self):
        """
        A ``dict`` with "group_id" as keys. Each value contains
        a ``list`` of indices of members that shared that "group_id".

        Note that this is based on the member entries in the association
        used to create the ModelLibrary. Updating the "group_id" of a model
        in the library will NOT change the values returned by this property
        (and will not change the association data available at ``asn``).
        """
        group_dict = {}
        for i, member in enumerate(self._members):
            group_id = member["group_id"]
            if group_id not in group_dict:
                group_dict[group_id] = []
            group_dict[group_id].append(i)
        return group_dict

    def __len__(self):
        return len(self._members)

    def borrow(self, index):
        """
        "borrow" a model from the library.

        Parameters
        ----------
        index : int
            The index of the model within the library. As the library
            size does not change this is unique to this model for this
            library.

        Returns
        -------
        model : DataModel

        Raises
        ------
        ClosedLibraryError
            If the library is not "open" (used in a ``with`` context).

        BorrowError
            If the model at this index is already "borrowed".
        """
        if not self._open:
            raise ClosedLibraryError("ModelLibrary is not open")

        # if model was already borrowed, raise
        if index in self._ledger:
            raise BorrowError("Attempt to double-borrow model")

        # if this model is in memory, return it
        if self._on_disk:
            if index in self._temp_filenames:
                model = self._datamodels_open(
                    self._temp_filenames[index], **self._datamodels_open_kwargs
                )
            else:
                model = self._load_member(index)
        else:
            if index in self._loaded_models:
                model = self._loaded_models[index]
            else:
                model = self._load_member(index)
                self._loaded_models[index] = model

        self._ledger[index] = model
        return model

    def _temp_path_for_model(self, model, index):
        model_filename = self._model_to_filename(model)
        subpath = self._temp_path / f"{index}"
        if not os.path.exists(subpath):
            os.makedirs(subpath)
        return subpath / model_filename

    def shelve(self, model, index=None, modify=True):
        """
        "shelve" a model, returning it to the library.

        Parameters
        ----------
        model : DataModel
            DataModel to return to the library at the provided index.

        index : int, optional
            The index within the library where the model will be stored.
            If the same model (checked by ``id(model)``) was previously
            borrowed and the index is not provided, the borrowed index
            will be used. If providing a new DataModel (one not borrowed
            from the library) the index must be provided.

        modify : bool, optional, default=True
            For an "on_disk" library, temporary files will only be written
            when modify is True. For a library that is not "on_disk"
            this option has no effect and any modifications made to the model
            while it was borrowed will persist.

        Raises
        ------
        ClosedLibraryError
            If the library is not "open" (used in a ``with`` context).

        BorrowError
            If an unknown model is provided (without an index) or
            if the model at the provided index has not been "borrowed"
        """
        if not self._open:
            raise ClosedLibraryError("ModelLibrary is not open")

        if index is None:
            try:
                index = self._ledger[model]
            except KeyError:
                raise BorrowError("Attempt to shelve an unknown model")

        if index not in self._ledger:
            raise BorrowError("Attempt to shelve model at a non-borrowed index")

        if modify:
            if self._on_disk:
                temp_filename = self._temp_path_for_model(model, index)
                model.save(temp_filename)

                # if we have an old model for this index that was saved
                # in the temporary directory and this model has a different
                # filename, remove the old file.
                if index in self._temp_filenames:
                    old_filename = self._temp_filenames[index]
                    if old_filename != temp_filename:
                        os.remove(old_filename)

                self._temp_filenames[index] = temp_filename
            else:
                self._loaded_models[index] = model

        del self._ledger[index]

    def __iter__(self):
        for i in range(len(self)):
            yield self.borrow(i)

    def _assign_member_to_model(self, model, member):
        for attr in ("group_id", "tweakreg_catalog", "exptype"):
            if attr in member:
                setattr(model.meta, attr, member[attr])

        if not hasattr(model.meta, "asn"):
            model.meta.asn = {}

        model.meta.asn["table_name"] = self.asn.get("table_name", "")
        model.meta.asn["pool_name"] = self.asn.get("asn_pool", "")

    def _load_member(self, index):
        member = self._members[index]
        filename = os.path.join(self._asn_dir, member["expname"])

        model = self._datamodels_open(filename, **self._datamodels_open_kwargs)

        self._assign_member_to_model(model, member)

        return model

    def save(self, path, **kwargs):
        """
        .. warning:: This save is NOT used by Step/Pipeline. This is
                     intentional as the Step/Pipeline has special requirements.

        For now this is a very basic "save". It does not:

            - check that the library contains no duplicate filenames
            - propagate asn_pool and other non-member asn information

        It will save:
            - models with filenames determined by ``_model_to_filename``
            - a very simple association that contains only 1 product that
              lists ``expname`` ``exptype`` and ``group_id``  for each model
              in a file named "asn.json".

        Parameters
        ----------
        path : Path or str
            Directory in which to store the models and generated
            association for this library.

        Returns
        -------
        association_path : Path
            The path to the saved association file.
        """
        if isinstance(path, str):
            path = Path(path)
        if not path.exists():
            path.mkdir()
        members = []
        with self:
            for i, model in enumerate(self):
                mfn = Path(self._model_to_filename(model))
                model.save(path / mfn, **kwargs)
                members.append(
                    {
                        "expname": str(mfn),
                        "exptype": model.meta.exptype,
                        "group_id": model.meta.group_id,
                    }
                )
                self.shelve(model, i, modify=False)
        asn_data = {"products": [{"members": members}]}
        asn_path = path / "asn.json"
        with open(asn_path, "w") as f:
            json.dump(asn_data, f)
        return asn_path

    def get_crds_parameters(self):
        """
        Get the "crds_parameters" from either:
            - the first "science" member (based on model.meta.exptype)
            - the first model (if no "science" member is found)

        If no "science" members are found in the library a ``UserWarning``
        will be issued.

        Returns
        -------
        crds_parameters : dict
            The result of ``get_crds_parameters`` called on the selected
            model.
        """
        with self:
            science_index = None
            for i, member in enumerate(self._members):
                if member["exptype"].lower() == "science":
                    science_index = i
                    break
            if science_index is None:
                warnings.warn(
                    "get_crds_parameters failed to find any science members. "
                    "The first model was used to determine the parameters",
                    UserWarning,
                )
                science_index = 0
            model = self.borrow(science_index)
            parameters = model.get_crds_parameters()
            self.shelve(model, science_index, modify=False)
        return parameters

    def finalize_result(self, step, reference_files_used):
        """
        Called from `stpipe.Step.run` after `stpipe.Step.process` has
        completed. This method will call `stpipe.Step.finalize_result`
        for each model in the library.

        Parameters
        ----------
        step : Step
            The step calling this method.

        reference_files_used : list
            List of reference files used during the execution of this
            step.
        """
        with self:
            for i, model in enumerate(self):
                step.finalize_result(model, reference_files_used)
                self.shelve(model, i)

    def __enter__(self):
        """
        "open" the library. This is required for any "borrow" and "shelve"
        calls. While the library is "open" it will track which models are
        borrowed and raise a `BorrowError` if an attempt is made to close
        the library before all borrowed models are returned.
        """
        self._open = True
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        "close" the library.

        Raises
        ------
        BorrowError
            If the library "closes" and one or more models have not been
            "shelved" (returned) this exception will be raised.
        """
        self._open = False
        if exc_value:
            # if there is already an exception, don't worry about checking the ledger
            # instead allowing the calling code to raise the original error to provide
            # a more useful feedback without any chained ledger exception about
            # un-returned models
            return
        if self._ledger:
            raise BorrowError(
                f"ModelLibrary has {len(self._ledger)} un-returned models"
            )

    def map_function(self, function, modify=True):
        """
        Call a function once for each model in the library.

        Similar to the built-in ``map`` function this applies the
        function "function" to each model in the library by iterating
        through the models (yielding on each function call).

        Parameters
        ----------
        function : callable
            A function that accepts 2 arguments, ``model`` and ``index``

        modify : bool, optional, default=True
            For an "on_disk" library, temporary files will only be written
            when modify is True. For a library that is not "on_disk"
            this option has no effect and any modifications made to the model
            while it was borrowed will persist.

        Returns
        -------
        result_iter : generator
            A generator that will return function results. This can be
            converted to a list ``list(result_iter)`` to get the results
            of all the function calls (ordered the same as the models in
            the library).
        """
        with self:
            for index, model in enumerate(self):
                try:
                    yield function(model, index)
                finally:
                    # this is in a finally to allow cleanup if the generator is
                    # deleted after it finishes (when it's not fully consumed)
                    self.shelve(model, index, modify)

    def _model_to_filename(self, model):
        """
        Determine the "filename" for a model. This will be used
        when writing temporary files (if the library is "on_disk")
        and for the ``save`` method (see the method for a note about
        how this is not used for the pipeline code).

        By default this method will return ``model.meta.filename``
        or "model.asdf" (if ``model.meta.filename`` is None).

        Parameters
        ----------
        model : DataModel

        Returns
        -------
        filename : str
        """
        model_filename = model.meta.filename
        if model_filename is None:
            model_filename = "model.asdf"
        return model_filename

    @property
    @abc.abstractmethod
    def crds_observatory(self):
        """
        Return the name of the observatory as a string
        """

    @abc.abstractmethod
    def _datamodels_open(self, filename, **kwargs):
        """
        Open a model from a filename
        """

    @classmethod
    @abc.abstractmethod
    def _load_asn(cls, filename):
        """
        Load an association from a filename
        """

    @abc.abstractmethod
    def _filename_to_group_id(self, filename):
        """
        Compute a "group_id" without loading the file as a DataModel

        This function will return the meta.group_id stored in the ASDF
        extension (if it exists) or a group_id calculated from the
        FITS headers.
        """

    @abc.abstractmethod
    def _model_to_group_id(self, model):
        """
        Compute a "group_id" from a model using the DataModel interface
        """
