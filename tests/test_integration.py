import glob
import os

import asdf
import yaml

from stpipe.integration import SCHEMAS_PATH


def test_asdf_extension():
    for schema_path in glob.glob(os.path.join(SCHEMAS_PATH, "**/*.yaml"), recursive=True):
        with open(schema_path) as f:
            yaml_schema = yaml.safe_load(f.read())
            asdf_schema = asdf.schema.load_schema(yaml_schema["id"])
            assert asdf_schema["id"] == yaml_schema["id"]
