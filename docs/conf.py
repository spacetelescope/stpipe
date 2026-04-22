# Sphinx configuration
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import importlib
import tomllib
from datetime import datetime
from pathlib import Path

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
    def register_documenter(app, config):
        app.add_autodocumenter(StepSpecDocumenter, True)

    # register it with a high priority so it behaves with the built-in autodoc
    app.connect("config-inited", register_documenter, priority=9000)


# -- Project information -----------------------------------------------------

with open(
    Path(__file__).parent.parent / "pyproject.toml", "rb"
) as project_metadata_file:
    project_metadata = tomllib.load(project_metadata_file)["project"]

project = project_metadata["name"]
author = project_metadata["authors"][0]["name"]
copyright = f"{datetime.today().year}, {author}"

package = importlib.import_module(project_metadata["name"])
try:
    release = package.__version__
    version = package.__version__.split("-", 1)[0]
except AttributeError:
    release = "dev"
    version = "dev"

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx_automodapi.automodapi",
    "numpydoc",
    "sphinx.ext.intersphinx",
]

intersphinx_mapping = {
    "asdf": ("https://asdf.readthedocs.io/en/stable/", None),
    "astropy": ("https://docs.astropy.org/en/stable/", None),
    "drizzle": ("https://spacetelescope-drizzle.readthedocs.io/en/latest/", None),
    "gwcs": ("https://gwcs.readthedocs.io/en/stable/", None),
    "matplotlib": ("https://matplotlib.org/", None),
    "numpy": ("https://numpy.org/devdocs", None),
    "photutils": ("https://photutils.readthedocs.io/en/stable/", None),
    "python": ("https://docs.python.org/3/", None),
    "requests": ("https://requests.readthedocs.io/en/latest/", None),
    "scipy": ("https://scipy.github.io/devdocs", None),
    "stcal": ("https://stcal.readthedocs.io/en/latest/", None),
    "stdatamodels": ("https://stdatamodels.readthedocs.io/en/latest/", None),
    "stpipe": ("https://stpipe.readthedocs.io/en/latest/", None),
    "synphot": ("https://synphot.readthedocs.io/en/latest/", None),
    "tweakwcs": ("https://tweakwcs.readthedocs.io/en/latest/", None),
}
intersphinx_disabled_domains = ["std"]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# reST default role (used for this markup: `text`) to use for all documents
default_role = "obj"

# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "collapse_navigation": True,
    "sticky_navigation": False,
    # "nosidebar": "false",
    # "sidebarbgcolor": "#4db8ff",
    # "sidebartextcolor": "black",
    # "sidebarlinkcolor": "black",
    # "headbgcolor": "white",
}
html_logo = "_static/stsci_pri_combo_mark_white.png"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_last_updated_fmt = "%b %d, %Y"
html_sidebars = {"**": ["globaltoc.html", "relations.html", "searchbox.html"]}
html_domain_indices = True
html_use_index = True

# -- Options for EPUB output -------------------------------------------------
epub_show_urls = "footnote"

# -- Options for extensions

# Don't show summaries of the members in each class along with the class' docstring
numpydoc_show_class_members = False

autosummary_generate = True

automodapi_toctreedirnm = "api"

# Class documentation should contain *both* the class docstring and the __init__ docstring
autoclass_content = "both"

# Render inheritance diagrams in SVG
graphviz_output_format = "svg"

graphviz_dot_args = [
    "-Nfontsize=10",
    "-Nfontname=Helvetica Neue, Helvetica, Arial, sans-serif",
    "-Efontsize=10",
    "-Efontname=Helvetica Neue, Helvetica, Arial, sans-serif",
    "-Gfontsize=10",
    "-Gfontname=Helvetica Neue, Helvetica, Arial, sans-serif",
]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "default"

# -- Options for linkcheck ----------------------------------------------

# linkcheck
linkcheck_retry = 5
linkcheck_ignore = [
    "http://stsci.edu/schemas/fits-schema/",  # Old schema from CHANGES.rst
    "https://outerspace.stsci.edu",  # CI blocked by service provider
    "https://jira.stsci.edu/",  # Internal access only
    r"https://.*\.readthedocs\.io",  # 429 Client Error: Too Many Requests
    "https://doi.org",  # CI blocked by service provider (timeout)
]
linkcheck_timeout = 180
linkcheck_anchors = False
linkcheck_report_timeouts_as_broken = True
linkcheck_allow_unauthorized = False

# Enable nitpicky mode - which ensures that all references in the docs
# resolve.
nitpicky = True
