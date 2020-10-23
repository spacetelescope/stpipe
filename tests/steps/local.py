from stpipe import Step
import logging

log = logging.getLogger("FOO")
log.setLevel(logging.DEBUG)


# TODO: Need to rework this to use smoething other than ImageModel.  Maybe
# define some dummy model classes somewhere?
# class DummyStep(Step):
#     """
#     This is a dummy step that does dumb things.
#     """

#     spec = """
#     foo = string()
#     """

#     def process(self, *args):
#         from jwst.datamodels import ImageModel

#         log.info("Default logger")
#         log.debug("Default logger")

#         self.log.info("Foo: {0}".format(self.foo))

#         self.log.debug("Debug!!!")

#         return ImageModel(args[0])
