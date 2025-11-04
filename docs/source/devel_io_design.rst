.. _step_io_design:

===============
Step I/O Design
===============

API Summary
===========

``Step`` command-line options
-----------------------------


* ``--output_dir``: Directory where all output will go.
* ``--output_file``: File name upon which output files will be based.

``Step`` configuration options
------------------------------

* ``output_dir``: Directory where all output will go.
* ``output_file``: File name upon which output files will be based.
* ``suffix``: Suffix defining the output of this step.
* ``save_results``: True to create output files.
* ``search_output_file``: True to retrieve the ``output_file`` from a parent ``Step`` or ``Pipeline``.
* ``output_use_model``: True to always base output file names on the
  ``DataModel.meta.filename`` of the ``DataModel`` being saved.
* ``input_dir``: Generally defined by the location of the primary
  input file unless otherwise specified.  All input files must be
  in this directory.

Classes, Methods, Functions
---------------------------

* :meth:`stpipe.Step.make_input_path`: Create a file name to
  be used as input
* :meth:`stpipe.Step.save_model`: Save a ``DataModel`` immediately
* :attr:`stpipe.Step.make_output_path`: Create a file name
  to be used as output

Design
======

The :class:`~stpipe.Step` architecture is designed such that
a ``Step``'s intended sole responsibility is to perform the calculation
required. Any input/output operations are handled by the surrounding
``Step`` architecture. This is to help facilitate the use of ``Step``'s
from both a command-line environment, and from an interactive Python
environment, such as Jupyter notebooks or IPython.

For command-line usage, all inputs and outputs are designed to come
from and save to files.

For interactive Python use, inputs and outputs are expected to be
Python objects, negating the need to save and reload data after every
``Step`` call. This allows users to write Python scripts without having
to worry about doing I/O at every step, unless, of course, if the user
wants to do so.

The high-level overview of the input/output design is given in
:ref:`writing-a-step`. The following discusses the I/O API and
best practices.

To facilitate this design, a basic ``Step`` is suggested to have the
following structure::

  class MyStep(stpipe.Step):

      spec = ''  # Desired configuration parameters

      def process(self, input):
          return do_calculation(input)

When run from the command line::

  strun MyStep input_data.asdf

the result will be saved in a file called::

  input_data_mystep.asdf

Similarly, the same code can be used in a Python script or interactive
environment as follows::

  result = MyStep.call(input)
  # result contains the resulting data
  # which can then be used by further steps or
  # other functions.
  #
  # when done, the data can be saved with the DataModel.save
  # method
  result.save('my_final_results.asdf')

Input Source
------------

All input files, except for references files provided by CRDS,
are expected to be co-resident in the same directory. That directory
is determined by the directory in which the primary input file
resides. For programmatic use, this directory is available in the
``Step.input_dir`` attribute.

Output
======

.. _devel_io_when_files_are_created:

When Files are Created
----------------------

Whether a ``Step`` produces an output file or not is ultimately
determined by the built-in parameter option ``save_results``. If
`True`, output files will be created. ``save_results`` is set under a
number of conditions:

* Explicitly through a parameter file or as a command-line option.
* Implicitly when a step is called by ``strun``.

Output File Naming
------------------

File names are constructed based on three components: basename,
suffix, and extension::

    basename_suffix.extension

The extension will often be the same as the primary input file. This
will not be the case if the data format of the output needs to be
something different, such as a text table with ``.ecsv`` extension.

Similarly, the basename will usually be derived from the primary input
file. However, there are some :ref:`caveats <basename_determination>`
discussed below.

Ultimately, the suffix is what ``Step`` use to identify their output.

A ``Step``'s suffix is defined in a couple of different ways:

* By the ``Step.name`` attribute. This is the default.
* By the ``suffix`` parameter.
* Explicitly in the code. Often this is done in ``Pipelines`` where
  a single pipeline creates numerous different output files.

.. _basename_determination:

Basename Determination
``````````````````````

Most often, the output file basename is determined through any of the
following, given from higher precedence to lower:

* The ``--output_file`` command-line option.
* The ``output_file`` parameter option.
* Primary input file name.
* If the output is a ``DataModel``, from the ``DataModel.meta.filename``.

In all cases, if the originating file name has a known suffix on it,
that suffix is removed and replaced by the ``Step``'s own suffix.

In very rare cases, when there is no other source for the basename, a
basename of ``step_<step_name>`` is used.  This can happen when a
``Step`` is being programmatically used and only the ``save_results``
parameter option is given.

.. _devel_io_substeps_and_output:

Sub-Steps and Output
````````````````````
Normally, the value of a parameter option is completely local to
the ``Step``: A ``Step``, called from another ``Step`` or ``Pipeline``, can
only access its own parameters. Hence, options such as
``save_results`` do not affect a called ``Step``.

The exceptions to this are the parameters ``output_file`` and
``output_dir``. If either of these parameters are queried by a ``Step``,
but are not defined for that ``Step``, values will be retrieved up
through the parent. The reason is to provide consistency in output
from ``Step`` and ``Pipeline``. All file names will have the same
basename and will all appear in the same directory.

As expected, if either parameter is specified for the ``Step`` in
question, the local value will override the parent value.

Also, for ``output_file``, there is another option,
``search_output_file``, that can also control this behavior. If set to
`False`, a ``Step`` will never query its parent for its value.

Output API: When More Control Is Needed
---------------------------------------

In summary, the standard output API, as described so far, is basically "set a
few parameters, and let the ``Step`` framework handle the rest". However, there
are always the exceptions that require finer control, such as saving
intermediate files or multiple files of different formats. This section
discusses the method API and conventions to use in these situations.

Save That Model: Step.save_model
````````````````````````````````

If a ``Step`` needs to save a ``DataModel`` before the step completes, use
of :meth:`stpipe.Step.save_model` is the recommended over
directly calling ``DataModel.save``.
``Step.save_model`` uses the ``Step`` framework and hence will honor the
following:

* If ``Step.save_results`` is `False`, nothing will happen.
* Will ensure that ``Step.output_dir`` is used.
* Will use ``Step.suffix`` if not otherwise specified.
* Will determine the output basename through the ``Step``
  framework, if not otherwise specified.

The basic usage, in which nothing is overridden, is::

    class MyStep(Step):

        def process(self, input):
            # ...
            result = some_DataModel
            self.save_model(result)

The most common use case, however, is for saving some intermediate
results that would have a different suffix::

    self.save_model(intermediate_result_datamodel, suffix='intermediate')

See :meth:`stpipe.Step.save_model` for further information.

Make That Filename: Step.make_output_path
`````````````````````````````````````````

For the situations when a filename is needed to be constructed before
saving, either to know what the filename will be or for data that is
not a ``DataModel``, use `stpipe.Step.make_output_path`. By default, calling
``make_output_path`` without any arguments will return what the default
output file name will be::

    output_path = self.make_output_path()

This method encapsulates the following ``Step`` framework functions:

* Will ensure that ``Step.output_dir`` is used.
* Will use ``Step.suffix`` if not otherwise specified.
* Will determine the output basename through the ``Step``
  framework, if not otherwise specified.

A typical use case is when a ``Step`` needs to save data that is not a
``DataModel``. The current ``Step`` architecture does not know how to
handle these, so saving needs to be done explicitly. The pattern of
usage would be::

    # A table need be saved and needs a different
    # suffix than what the Step defines.
    table = some_astropy_table_data
    if self.save_results:
        table_path = self.make_output_path(suffix='cat', ext='ecsv')
        table.save(table_path, format='ascii.ecsv', overwrite=True)
