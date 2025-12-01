.. _devel-pipelines:

=========
Pipelines
=========

.. _writing-a-pipeline:

Writing a Pipeline
==================

The basics of writing a Pipeline are just like
:ref:`writing-a-step`, but instead of inheriting from the
`~stpipe.Step` class, one inherits from the `~stpipe.Pipeline` class.

In addition, a Pipeline subclass defines what its Steps are so that the
framework can configure parameters for the individual Steps.  This is
done with the ``step_defs`` member, which is a dictionary mapping step
names to step classes.  This dictionary defines what the Steps are,
but says nothing about their order or how data flows from one Step to
the next.  That is defined in Python code in the Pipeline’s
``process`` method. By the time the Pipeline’s ``process`` method is
called, the Steps in ``step_defs`` will be instantiated as member
variables.

For example, here is a pipeline with two steps:

    from stpipe import Pipeline

    from mycode.datamodels import MyDataModel
    from mycode.steps import CleanupStep, DenoiseStep

    class CalibrationPipeline(Pipeline):
        """
        This example pipeline demonstrates how to combine steps
        using Python code, in some way that it not necessarily
        a linear progression.
        """

        step_defs = {
            'cleanup': CleanupStep,
            'denoise': DenoiseStep,
            }

        def process(self, input):
            with MyDataModel(input) as science:

                cleaner = self.cleanup(science, self.multiplier)

                noise_free = self.denoise(cleaner)

            return noise_free

        spec = """
        multiplier = float()     # A multiplier constant
        """

When writing the spec member for a Pipeline, only the parameters
that apply to the Pipeline as a whole need to be included.  The
parameters for each Step are automatically loaded in by the framework.

The parameters for the individual substeps that make up the Pipeline
will be implicitly added by the framework.
