import importlib
import sys
from datetime import datetime
from pathlib import Path

if sys.version_info < (3, 11):
    import tomli as tomllib
else:
    import tomllib

from sphinx.ext.autodoc import AttributeDocumenter

from stpipe import Step


class StepSpecDocumenter(AttributeDocumenter):
    def should_suppress_value_header(self):
        if self.name == "spec" and issubclass(self.parent, Step):
            # if this attribute is named "spec" and belongs to a "Step"
            # don't show the value, it will be formatted in add_context below
            return True
        return super().should_suppress_value_header()

    def add_content(self, more_content):
        super().add_content(more_content)
        if self.name != "spec" or not issubclass(self.parent, Step):
            return
        if not self.object.strip():
            return

        # format the long "Step.spec" string to improve readability
        source_name = self.get_sourcename()
        self.add_line("::", source_name, 0)
        self.add_line("  ", source_name, 1)
        txt = "\n".join((l.strip() for l in self.object.strip().splitlines()))
        self.add_line(f"  {txt}", source_name, 2)


def setup(app):
    # add a custom AttributeDocumenter subclass to handle Step.spec formatting
    app.add_autodocumenter(StepSpecDocumenter, True)


REPO_ROOT = Path(__file__).parent.parent.parent

# Read the package's `pyproject.toml` so that we can use relevant
# values here:
with open(REPO_ROOT / "pyproject.toml", "rb") as configuration_file:
    conf = tomllib.load(configuration_file)
setup_metadata = conf["project"]

project = setup_metadata["name"]
primary_author = setup_metadata["authors"][0]
author = primary_author["name"]
copyright = f"{datetime.now().year}, {author}"

package = importlib.import_module(project)
version = package.__version__.split("-", 1)[0]
release = package.__version__

extensions = [
    "sphinx_automodapi.automodapi",
    "numpydoc",
    "sphinx.ext.intersphinx",
]

autosummary_generate = True
numpydoc_show_class_members = False
autoclass_content = "both"

html_theme = "sphinx_rtd_theme"
html_logo = "_static/stsci_pri_combo_mark_white.png"
html_theme_options = {
    "collapse_navigation": True,
}
html_domain_indices = True
html_sidebars = {"**": ["globaltoc.html", "relations.html", "searchbox.html"]}
html_use_index = True

# Enable nitpicky mode - which ensures that all references in the docs
# resolve.
nitpicky = True
nitpick_ignore = []

suppress_warnings = ["app.add_directive"]

# Set the default role for all single backtick annotations
default_role = "obj"

intersphinx_mapping = {}
intersphinx_mapping["python"] = ("https://docs.python.org/3", None)
