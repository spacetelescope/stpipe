.. _run_examples:

Executing a pipeline via run()
==============================

When calling a pipeline or step instance using the ``run`` method,
you can specify individual parameter values manually. In this case, parameter
files are not used. If you use ``run`` after instantiating with a parameter
file (as is done when using the :ref:`call <call_examples>` method), the
parameter file will be ignored::

    # Instantiate the class. Do not provide a parameter file.
    pipe = MyPipeline()

    # Manually set any desired non-default parameter values
    pipe.mystep.myparameter = 26
    pipe.save_result = True
    pipe.output_dir = '/my/data/pipeline_outputs'

    # Execute the pipeline using the run method
    result = pipe.run('myfile.asdf')

To run a single step::

    # Instantiate the step
    step = MyStep()

    # Set parameter values
    step.myparameter = 26
    step.save_results = True
    step.output_dir = '/my/data/step_outputs'

    # Execute using the run method
    result = step.run('myfile.asdf')
