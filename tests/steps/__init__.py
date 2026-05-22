import logging

from stpipe import Pipeline, Step

log = logging.getLogger("stpipe.tests.steps")


class BaseStep(Step):
    spec = """
        output_ext = string(default='.asdf')
    """

    def _datamodels_open(self, **kwargs):
        pass


class BasePipeline(Pipeline, BaseStep):
    pass


class WithDefaultsStep(BaseStep):
    """A step that contains defaults for each of its pars."""

    spec = """
    par1 = string(default='default par1 value')
    par2 = string(default='default par2 value')
    par3 = string(default='default par3 value')
    par4 = string(default='default par4 value')
    """

    def process(self, input_data):  # noqa: D102
        log.info(
            "Parameters par1=%s, par2=%s, par3=%s, par4=%s",
            self.par1,
            self.par2,
            self.par3,
            self.par3,
        )

        return input_data


class MakeListStep(BaseStep):
    """Make a list of all arguments and parameters."""

    spec = """
    par1 = float() # Control the frobulization
    par2 = string() # Reticulate the splines
    par3 = boolean(default=False) # Does it blend?
    """

    def process(self, a=None, b=None):  # noqa: D102
        log.info("Arguments a=%s b=%s", a, b)
        log.info(
            "Parameters par1=%s, par2=%s, par3=%s", self.par1, self.par2, self.par3
        )

        result = [
            item for item in [a, b, self.par1, self.par2, self.par3] if item is not None
        ]

        log.info("The list is %s", result)
        return result


class EmptyPipeline(BasePipeline):
    """A pipeline that has no substeps."""

    spec = """
    par1 = string(default='Name the atomizer') # Control the frobulization
    """

    def process(self, *args):  # noqa: D102
        return args


class MakeListPipeline(BasePipeline):
    """A pipeline that calls MakeListStep."""

    spec = """
    par1 = string(default='Name the atomizer') # Control the frobulization
    """

    step_defs = {
        "make_list": MakeListStep,
    }

    def process(self, *args):  # noqa: D102
        return self.make_list.run(*args)
