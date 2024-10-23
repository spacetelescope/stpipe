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
    Creating a library does not read any models into memory,
    as long as the association contains a ``group_id`` for each member

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
   ...    for model in library:  # implicitly calls borrow()
   ...        # do stuff with the model...
   ...        library.shelve(model)


.. _library_on_disk:

On Disk Mode
------------

For large associations (like those larger than memory) it is important
that the library avoid reading all models at once. The borrow/shelve API
above maps closely to the loading/saving of input (or temporary) files
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
``model.dq`` array was read, but not modified), it is helpful to tell the
library that the model was not modified.

.. code-block:: pycon

   >>> with library:
   ...     model = library.borrow(0)  # the input file for model 0 is loaded
   ...     # do some read-only stuff with the model
   ...     library.shelve(model, modify=False)  # No temporary file will be written

This tells the library not to overwrite the model's temporary file while shelving, saving
on both disk space and the time required to write.

.. WARNING::
   In the above example ``model`` remains in scope after the call to
   `~stpipe.library.AbstractModelLibrary.shelve` (and even after
   the exit of the with statement). This means ``model`` will not
   be garbage collected (and it's memory will not be freed) until
   the end of the scope containing the ``with library`` exits. If
   more work occurs within the scope please consider adding an
   explicit ``del model`` when your code is finished with the model.


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


.. _library_association_information:

Association Information
=======================

`~stpipe.library.AbstractModelLibrary.asn` provides read-only access to the association data.

.. code-block:: pycon

   >>> library.asn["products"][0]["name"]
   >>> library.asn["table_name"]

Although the specifics of what is returned by `~stpipe.library.AbstractModelLibrary.asn`
depends on how the subclass implements ``AbstractModelLibrary._load_asn``, it
is required that the association metadata dictionary contain a "members" list. This
can be inspected via ``library.asn["products"][0]["members"]`` and must contain a
dictionary for each "member" including key-value pairs for:

- "expname" for the exposure name, with a string value corresponding to the
  name of the file for this member
- "exptype" for the exposure type, with a string value describing the type
  of exposure (for example "science" or "background")

Although not required, "group_id" (with a string value corresponding to the
group name) should be added to each member dictionary (see
:ref:`library_association` for more details).

.. _library_usage_patterns:

Usage Patterns
==============

What follows is a section about using `~stpipe.library.AbstractModelLibrary`
in `~stpipe.step.Step` and `~stpipe.pipeline.Pipeline` code. This section
is short at the moment and can be extended with additional patterns as
the `~stpipe.library.AbstractModelLibrary` is used in more pipeline code.

.. _library_step_input_handling:

Step input handling
-------------------

It is recommended that any `~stpipe.step.Step` (or `~stpipe.pipeline.Pipeline`)
that accept an
`~stpipe.library.AbstractModelLibrary` consider the performance when
processing the input. It likely makes sense for any `~stpipe.step.Step`
that accepts a `~stpipe.library.AbstractModelLibrary` to also accept
an association filename as an input. The basic input handling could look
something like the following:

.. code-block:: pycon

   >>> def process(self, init):
   ...     if isinstance(init, ModelLibrary):
   ...         library = init  # do not copy the input ModelLibrary
   ...     else:
   ...         library = ModelLibrary(init, self.on_disk)
   ...     # process library without making a copy as
   ...     # that would lead to 2x required file space for
   ...     # an "on disk" model and 2x the memory for an "in memory"
   ...     # model
   ...     return library

The above pattern supports as input (``init``):

- an `~stpipe.library.AbstractModelLibrary`
- an association filename (via the `~stpipe.library.AbstractModelLibrary` constructor)
- all other inputs supported by the `~stpipe.library.AbstractModelLibrary` constructor

It is generally recommended to expose ``on_disk`` in the ``Step.spec``
allowing the `~stpipe.step.Step` to generate an :ref:`library_on_disk`
`~stpipe.library.AbstractModelLibrary`:

.. code-block:: pycon

   >>> class MyStep(Step):
   ...     spec = """
   ...         on_disk = boolean(default=False)  # keep models "on disk" to reduce RAM usage
   ...     """

.. NOTE::
   As mentioned in :ref:`library_on_disk` at no point will the input files
   referenced in the association be modified. However, the above pattern
   does allow ``Step.process`` to "modify" ``init`` when
   ``init`` is a `~stpipe.library.AbstractModelLibrary` (the models
   in the library will not be copied).

``Step.process`` can extend the above pattern to
support additional inputs (for example a single
`~stpipe.datamodel.AbstractDataModel` or filename containing
a `~stpipe.datamodel.AbstractDataModel`) to allow more
flexible data processings, although some consideration
should be given to how to handle input that does not
contain association metadata. Does it make sense
to construct a `~stpipe.library.AbstractModelLibrary` when the
association metadata is made up? Alternatively, is
it safer (less prone to misattribution of metadata)
to have the step process the inputs separately
(more on this below)?

.. _library_isolated_processing:

Isolated Processing
-------------------

Let's say we have a `~stpipe.step.Step`, ``flux_calibration``
that performs an operation that is only concerned with the data
for a single `~stpipe.datamodel.AbstractDataModel` at a time.
This step applies a function ``calibrate_model_flux`` that
accepts a single `~stpipe.datamodel.AbstractDataModel` and index as an input.
Its ``Step.process`` function can make good use of
`~stpipe.library.AbstractModelLibrary.map_function` to apply
this method to each model in the library.

.. code-block:: pycon

   >>> class FluxCalibration(Step):
   ...     spec = "..." # use spec defined above
   ...     def process(self, init):
   ...         # see input pattern described above
   ...         # list is used here to consume the generator produced by map_function
   ...         list(library.map_function(calibrate_model_flux))
   ...         return library

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
`~stpipe.library.AbstractModelLibrary.shelve`):

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
- ``_model_to_exptype``
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
- When loaded from an association, the container size never changed;
  that is, no use-cases required adding new models to associations within steps
- The order of models was never changed
- Must be compatible with stpipe infrastructure (implements
  ``crds_observatory``, ``get_crds_parameters``, etc methods)
- Several steps implemented different memory optimizations
- Step code has additional complexity to deal with containers
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
Initial prototypes used ``__setitem__`` which led to some confusion
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


.. _library_future_directions:

Future directions
-----------------

The initial implementation of `~stpipe.library.AbstractModelLibrary` was intentionally
simple. Several features were discussed but deemed unnecessary for the current code.
This section will describe some of the discussed features to in-part provide a
record of these discussions.

.. _library_borrow_limits:

Borrow limits
^^^^^^^^^^^^^

As `~stpipe.library.AbstractModelLibrary` handles the loading and saving of models
(when "on disk") it could be straightforward to impose a limit to the number
and/or combined size of all "borrowed" models. This would help to avoid crashes
due to out-of-memory issues (especially important for HPC environments where
the memory limit may be defined at the job level). Being able to gracefully
recover from this error could also allow pipeline code to load as many
models as possible for more efficient batch processing.


.. _library_hollowing_out_models:

Hollowing out models
^^^^^^^^^^^^^^^^^^^^

Currently the `~stpipe.library.AbstractModelLibrary` does not close
models when they are "shelved" (it relies on the garbage collector).
This was done to allow easier integration with existing pipeline code
but does mean that the memory used for a model will not be freed until
the model is freed. By explicitly closing models and possibly
removing references between the model and the data arrays ("hollowing
out") memory could be freed sooner allowing for an overall decrease.

.. _library_append:

Append
^^^^^^

There is no way to append a model to a `~stpipe.library.AbstractModelLibrary`
(nor is there a way to pop, extend, delete, etc, any operation that changes the
number of models in a library). This was an intentional choice as any operation
that changes the number of models would obviously invalidate the
`~stpipe.library.AbstractModelLibrary.asn` data. It should be possible
(albeit complex) to support some if not all of these operations. However
serious consideration of their use and exhuasting of alternatives is
recommended as the added complexity would likely introduce bugs.

.. _library_updating_asn_on_shelve:

Updating asn on shelve
^^^^^^^^^^^^^^^^^^^^^^

Related to the note about :ref:`library_append` updating the
`~stpipe.library.AbstractModelLibrary.asn` data on
`~stpipe.library.AbstractModelLibrary.shelve` would allow step code
to modify asn-related attributes (like group_id) and have these changes
reflected in the `~stpipe.library.AbstractModelLibrary.asn` result.
A similar note of caution applies here where some consideration
of the complexity required vs the benefits is recommended.

.. _library_get_sections:

Get sections
^^^^^^^^^^^^

`~stpipe.library.AbstractModelLibrary` has no replacement for
the ``get_sections`` API provided with ``ModelContainer``. If its use
is generally required it might make sense to model the API off of
the existing group_id methods (where the subclass provides 2 methods
for efficiently accessing either an in-memory section or an on-disk
section for the "in memory" and "on disk" modes).

.. _library_parallel_map_function:

Parallel map function
^^^^^^^^^^^^^^^^^^^^^

`~stpipe.library.AbstractModelLibrary.map_function` is applied to each model
in a library sequentially. If this method proves useful and is typically
used with an independent and stateless function, extending the method to
use parallel application seems straightforward (although a new API might
be called for since a parallel application would likely not behave
as a generator.
