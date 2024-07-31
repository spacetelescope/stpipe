import importlib
import sys

if sys.version_info < (3, 11):
    import tomli as tomllib
else:
    import tomllib

from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent.parent

# Modules that automodapi will document need to be available
# in the path:
sys.path.insert(0, str(REPO_ROOT / "src" / "stpipe"))

# Read the package's `pyproject.toml` so that we can use relevant
# values here:
with open(REPO_ROOT / "pyproject.toml", "rb") as configuration_file:
    conf = tomllib.load(configuration_file)
setup_metadata = conf["project"]

project = setup_metadata["name"]
primary_author = setup_metadata["authors"][0]
author = f'{primary_author["name"]} <{primary_author["email"]}>'
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

# Set the default role for all single backtick annotations
default_role = "obj"

intersphinx_mapping = {}
intersphinx_mapping["python"] = ("https://docs.python.org/3", None)
