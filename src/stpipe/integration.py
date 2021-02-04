"""
Entry point implementations.
"""
import os

from asdf.extension import AsdfExtension
from asdf import util


SCHEMAS_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "resources", "schemas")
)


class StpipeExtension(AsdfExtension):
    """
    ASDF extension providing access to the stpipe schemas.  This
    class is registered with the asdf_extensions entry point.
    """
    @property
    def types(self):
        # Required by the ABC but unused here
        return []

    @property
    def tag_mapping(self):
        # Required by the ABC but unused here
        return []

    @property
    def url_mapping(self):
        return [
            ("http://stsci.edu/schemas/stpipe", util.filepath_to_url(SCHEMAS_PATH) + "/{url_suffix}.yaml"),
        ]
