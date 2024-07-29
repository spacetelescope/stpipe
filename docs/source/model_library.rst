.. _model_library:

Model Library
=============

`~stpipe.library.AbstractModelLibrary` is a container designed to allow efficient processing of
collections of `~stpipe.datamodel.AbstractDataModel` instances created from an association.

`~stpipe.library.AbstractModelLibrary` is an ordered collection (like a `list`) but provides:

- access to association metadata: `~stpipe.library.AbstractModelLibrary.asn`
- grouping API: `~stpipe.library.AbstractModelLibrary.group_indices` and `~stpipe.library.AbstractModelLibrary.group_names`
- compatibility with `~stpipe.step.Step` and `~stpipe.pipeline.Pipeline` runs
- a consistent indexing API that is the same for "in memory" and "on disk" libraries


.. _library_association:

Loading an association
----------------------

Most commonly an instance will be created from an association file:

.. code-block:: pycon

   >>> library = ModelLibrary("my_asn.json")

.. NOTE::
   For an association that contains a ``group_id`` for each member,
   creating a library will not read any models.

.. _library_borrowing_and_shelving:

Borrowing and shelving models
-----------------------------

Interacting with an `~stpipe.library.AbstractModelLibrary` involves "borrowing" and "shelving"
models, both of which must occur during a ``with`` statement (while the library
is "open"):

.. code-block:: pycon

   >>> with library:
   ...    model = library.borrow(0)
   ...    # do stuff with the model...
   ...    library.shelve(model)

Iteration is also supported (but don't forget to return your models!).

.. code-block:: pycon

   >>> with library:
   ...    for model in library:
   ...        # do stuff with the model...
   ...        library.shelve(model)


.. _library_on_disk:

On Disk Mode
------------

For large associations (like those larger than memory) it is important
that the library avoid reading all models at once. The borrow/shelve API
above maps closely to the loading/saving of input (or tempoary) files
containing the models.

.. code-block:: pycon

   >>> library = ModelLibrary("my_big_asn.json", on_disk=True)
   >>> with library:
   ...     model = library.borrow(0)  # the input file for model 0 is loaded
   ...     library.shelve(model)  # a temporary file for model 0 is written

.. NOTE::
   In the above example, a temporary file was created for model 0. At no
   point will the library overwrite the input file.

If model is not modified during the time it's borrowed (for example if the
``model.dq`` array was read, but not modified). It is helpful to tell the
library that the model was not modified.

.. code-block:: pycon

   >>> with library:
   ...     model = library.borrow(0)  # the input file for model 0 is loaded
   ...     # do some read-only stuff with the model
   ...     library.shelve(model, modify=False)  # No temporary file will be written

This can dramatically reduce the number of times a file is written saving
on both disk space and the time required to write.


.. _library_map_function:

Map function
------------

Let's say you want to get the ``meta.filename`` attribute for all models
in a library. The above "open", "borrow", "shelve" pattern can be quite
verbose. Instead, the helper method `~stpipe.library.AbstractModelLibrary.map_function`
can be used to generate an iterator that returns the result of a function
applied to each model in the library:

.. code-block:: pycon

   >>> def get_model_name(model, index):
   ...     return model.meta.filename
   >>>
   >>> filenames = list(library.map_function(get_model_name))

.. NOTE::
   `~stpipe.library.AbstractModelLibrary.map_function` does not require an open library
   and will handle opening, borrowing, shelving and closing for you.


.. _library_grouping:

Grouping
--------

Grouping also doesn't require an open library (as all grouping is
performed on the association metadata).

.. code-block:: pycon

   >>> print(f"All group names: {library.group_names}")
   >>> group_index_map = library.group_indices
   >>> for group_name in group_index_map:
   ...     print(f"\tModel indices for {group_name}: {group_index_map[group_name]}")

.. WARNING::
   Although `~stpipe.library.AbstractModelLibrary.group_names` and
   `~stpipe.library.AbstractModelLibrary.group_indices` do not require an open library,
   any "borrows" using the indices do. Be sure to open the library before
   trying to borrow a model.

`~stpipe.library.AbstractModelLibrary.asn` provides read-only access to the association data.

.. code-block:: pycon

   >>> library.asn["products"][0]["name"]
   >>> library.asn["table_name"]


.. _library_troubleshooting:

Troubleshooting
===============

.. _library_closed_library_error:

ClosedLibraryError
------------------

.. code-block:: pycon

   >>> model = library.borrow(0)

   ClosedLibraryError: ModelLibrary is not open

The library must be "open" (used in a ``with`` statement) before
a model can be borrowed. This is important for keeping track of
which models were possibly modified.

This error can be avoided by "opening" the library before calling
`~stpipe.library.AbstractModelLibrary.borrow` (and being sure to call
`~stpipe.library.AbstractModelLibrary.shelve`, more on that below):

.. code-block:: pycon

   >>> with library:
   ...     model = library.borrow(0)
   ...     library.shelve(model)

.. _library_borrow_error:

BorrowError
-----------

.. code-block:: pycon

   >>> with library:
   ...     model = library.borrow(0)
   ...     # do stuff with the model
   ...     # forget to shelve it

   BorrowError: ModelLibrary has 1 un-returned models

Forgetting to `~stpipe.library.AbstractModelLibrary.shelve` a borrowed model will result in an
error. This is important for keeping track of model modifications and is
critical when the library uses temporary files to keep models out of memory.

This error can be avoided by making sure to `~stpipe.library.AbstractModelLibrary.shelve` all
borrowed models:

.. code-block:: pycon

   >>> with library:
   ...     model = library.borrow(0)
   ...     library.shelve(model)

Attempting to "double borrow" a model will also result in a `~stpipe.library.BorrowError`.

.. code-block:: pycon

   >>> with library:
   ...     model_a = library.borrow(0)
   ...     model_b = library.borrow(0)

   BorrowError: Attempt to double-borrow model

This check is also important for the library to track model modifications. The
error can be avoided by only borrowing each model once (it's ok to borrow
more than one model if they are at different positions in the library).

`~stpipe.library.BorrowError` exceptions can also be triggered when trying to replace
a model in the library.

.. code-block:: pycon

   >>> with library:
   ...     library.shelve(some_other_model)

   BorrowError: Attempt to shelve an unknown model

Here the library does not know where to shelve ``some_other_model`` (since
the ``some_other_model`` wasn't borrowed from the library). To replace
a model in the library you will need to first borrow the model at the index
you want to use and provide the index to the call to
`~stpipe.library.AbstractModelLibrary.shelve`.

.. code-block:: pycon

   >>> with library:
   ...     library.borrow(0)
   ...     library.shelve(some_other_model, 0)

Forgetting to first borrow the model at the index will also produce a
`~stpipe.library.BorrowError` (even if you provide the index).

.. code-block:: pycon

   >>> with library:
   ...     library.shelve(some_other_model, 0)

   BorrowError: Attempt to shelve model at a non-borrowed index

.. _library_implementing_a_subclass:

Implementing a subclass
=======================

Several methods are abstract and will need implementations:

- Methods used by stpipe:

  - `~stpipe.library.AbstractModelLibrary.crds_observatory`

- Methods used by `~stpipe.library.AbstractModelLibrary`

  - ``_datamodels_open``
  - ``_load_asn``
  - ``_filename_to_group_id``
  - ``_model_to_group_id``

It's likely that a few other methods might require overriding:

- ``_model_to_filename``
- ``_assign_member_to_model``

Consult the docstrings (and base implementations) for more details.

It may also be required (depending on your usage) to update
``stpipe.step.Step._datamodels_open`` to allow stpipe to open and inspect an
`~stpipe.library.AbstractModelLibrary` when provided as a `~stpipe.step.Step` input.

.. _library_developer_documentation:

Developer Documentation
=======================

What follows are note primarily aimed towards developers and
maintainers of `~stpipe.library.AbstractModelLibrary`. This section might be useful
to provide context to users but shouldn't be necessary for a user
to effectively use `~stpipe.library.AbstractModelLibrary`.

.. _library_motivation:

Motivation
----------

The development of `~stpipe.library.AbstractModelLibrary` was largely motivated by
the need for a container compatible with stpipe machinery
that would allow passing "on disk" models between steps. Existing
containers (when used in "memory saving" modes) were not compatible
with stpipe. These containers also sometimes allowed input files
to be overwritten. It was decided that a new container would be
developed to address these and other issues. This would allow
gradual migration for pipeline code where specific steps and pipelines
could update to `~stpipe.library.AbstractModelLibrary` while leaving the existing
container unchanged for other steps.

A survey of container usage was performed with a few key findings:

- Many uses could be replaced by simpler containers (lists)
- When loaded from an association, the container size never changed
- The order of models was never changed
- Needs various methods for stpipe
- Several steps implemented different memory optimizations
  and had significant complexity added to deal with containers
  that sometimes returned filenames and sometimes returned models

Additionally, pipelines and steps may be expected to handle large
volumes of input data. For one example, consider a pipeline
responsible for generating a mosaic of a large number of input imaging
observations. As the size of the input data approaches (and exceeds)
the available memory it is critical that the pipeline, step, and
container code never read and hold all input data in memory.

.. _library_design_priciples:

Design principles
-----------------

The high level goals of `~stpipe.library.AbstractModelLibrary` are:

- Replace many uses of existing containers, focusing on areas
  where large data is expected.
- Implement a minimal API that can be later expanded as needs
  arise.
- Provide a consistent API for "on disk" and "in memory" modes
  so step code does not need to be aware of the mode.
- Support all methods required by stpipe to allow a "on disk"
  container to pass between steps.

Most of the core functionality is public and described in the above
user documentation. What follows will be description of other parts
of the API (most private) and internal details.

One core issue is how can the container know when to load and
save models (to temporary files) if needed? With a typical list
``__getitem__`` can map to load but what will map to save?
Initial prototypes used ``__setitem__`` which lead to some confusion
amongst reviewers. Treating the container like a list also
leads to expectations that the container also support
``append`` ``extend`` and other API that is unnecessary (as determined
in the above survey) and would be difficult to implement in a way that
would keep the container association information and model information
in sync.

.. _library_integration_with_stpipe:

Integration with stpipe
-----------------------

An `~stpipe.library.AbstractModelLibrary` may interact with stpipe when used as an
input or output for a `~stpipe.step.Step`.

- as a `~stpipe.step.Step` input where `~stpipe.library.AbstractModelLibrary.get_crds_parameters` and
  `~stpipe.library.AbstractModelLibrary.crds_observatory` will be used (sometimes with
  a limited model set, including only the first member of the input
  association).
- as a `~stpipe.step.Step` output where `~stpipe.library.AbstractModelLibrary.finalize_result` will
  be used.
