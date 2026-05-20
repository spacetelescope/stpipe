"""
Entry point implementations.
"""

import os

from asdf.resource import DirectoryResourceMapping

SCHEMAS_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "resources", "schemas")
)


def get_resource_mappings():
    return [
        DirectoryResourceMapping(
            SCHEMAS_PATH, "http://stsci.edu/schemas/stpipe/", recursive=True
        ),
    ]
