.. _stpipe-user-pipelines:

=========
Pipelines
=========

It is important to note that a Pipeline is also a Step, so everything
that applies to a Step in the :ref:`configuring-a-step` chapter also
applies to Pipelines.

Configuring a Pipeline
======================

This section describes how to set parameters on the individual steps
in a pipeline.  To change the order of steps in a pipeline, one must
write a Pipeline subclass in Python.  That is described in the
:ref:`devel-pipelines` section of the developer documentation.

Just as with Steps, Pipelines can by configured either by a
parameter file or directly from Python.

From a parameter file
---------------------

A Pipeline parameter file follows the same format as a Step parameter file:
:ref:`config_asdf_files`

Here is an example pipeline parameter file for an imaginary ``CalibrationPipeline``
class:

.. code-block:: yaml

   #ASDF 1.0.0
   #ASDF_STANDARD 1.5.0
   %YAML 1.1
   %TAG ! tag:stsci.edu:asdf/
   --- !core/asdf-1.1.0
   asdf_library: !core/software-1.0.0 {author: Space Telescope Science Institute, homepage: 'http://github.com/spacetelescope/asdf',
      name: asdf, version: 2.7.3}
   class: mycode.pipelines.CalibrationPipeline
   name: MyCalibrationPipeline
   steps:
   - class: mycode.steps.CleanupStep
     name: cleanup
     parameters:
       skip = True
   - class: mycode.steps.DenoiseStep
     name: denoise
     parameters:
       smoothing: 1.0

Just like a ``Step``, it must have ``name`` and ``class`` values.
Here the ``class`` must refer to a subclass of ``stpipe.Pipeline``.

Following ``name`` and ``class`` is the ``steps`` section.  Under
this section is a subsection for each step in the pipeline.  The easiest
way to get started on a parameter file is to call ``Step.export_config`` and
then edit the file that is created.  This will generate an ASDF config file
that includes every available parameter, which can then be trimmed to the
parameters that require customization.

For each Step’s section, the parameters for that step may either be
specified inline, or specified by referencing an external
parameter file just for that step.  For example, a pipeline
parameter file that contains:

.. code-block:: yaml

   steps:
   - class: mycode.steps.DenoiseStep
     name: denoise
     parameters:
       smoothing: 1.0

is equivalent to:

.. code-block:: yaml

   steps:
   - class: mycode.steps.DenoiseStep
     name: denoise
     parameters:
       config_file = mydenoise.asdf

with the file ``mydenoise.asdf.`` in the same directory:

.. code-block:: yaml

   class: mycode.steps.DenoiseStep
   name: denoise
   parameters:
     smoothing: 1.0

If both a ``config_file`` and additional parameters are specified, the
``config_file`` is loaded, and then the local parameters override
them.

Any optional parameters for each Step may be omitted, in which case
defaults will be used.


From Python
-----------

A pipeline may be configured from Python by passing a nested
dictionary of parameters to the Pipeline’s constructor.  Each key is
the name of a step, and the value is another dictionary containing
parameters for that step.  For example, the following is the
equivalent of the parameter file above:

.. code-block:: python

    from mycode.pipelines import CalibrationPipeline

    steps = {
        'denoise': {'smoothing': 2.0}
    }

    pipe = CalibrationPipeline(steps=steps)

Running a Pipeline
==================

From the command line
---------------------

The same ``strun`` script used to run Steps from the commandline can
also run Pipelines.

The only wrinkle is that any parameters overridden from the
commandline use dot notation to specify the parameter name.  For
example, to override the ``pixfrac`` value on the ``resample``
step in the example above, one can do:

.. code-block:: shell

    strun mycode.pipelines.CalibrationPipeline --steps.denoise.smoothing=2.0

From Python
-----------

Once the pipeline has been configured (as above), run it::

    pipe.run()

For more details, see :ref:`run_examples`.

Hooks
=====

Each Step in a pipeline can also have pre- and post-hooks associated.
Hooks themselves are Step instances, but there are some conveniences
provided to make them easier to specify in a parameter file.

Pre-hooks are run right before the Step.  The inputs to the pre-hook
are the same as the inputs to their parent Step.
Post-hooks are run right after the Step.  The inputs to the post-hook
are the return value(s) from the parent Step. The return values are
always passed as a list. If the return value from the parent Step is a
single item, a list of this single item is passed to the post hooks.
This allows the post hooks to modify the return results, if necessary.

Hooks are specified using the ``pre_hooks`` and ``post_hooks`` parameters
associated with each step. More than one pre- or post-hook may be assigned, and
they are run in the order they are given. There can also be ``pre_hooks`` and
``post_hooks`` on the Pipeline as a whole (since a Pipeline is also a Step).
Each of these parameters is a list of strings, where each entry is one of:

* An external commandline application.  The arguments can be
  accessed using {0}, {1} etc.  (See
  ``stpipe.subproc.SystemCall``).
* A dot-separated path to a Python Step class.
* A dot-separated path to a Python function.


For example, here's a ``post_hook`` that runs ``stat`` on our output file
after the denoise step:

.. code-block:: yaml

   steps:
   - class: mycode.steps.DenoiseStep
     name: denoise
     parameters:
        post_hooks = "stat {0}",
