# -- Path setup --------------------------------------------------------------
import os
import sys
sys.path.insert(0, os.path.abspath("../../src"))

# -- Project information -----------------------------------------------------

project = 'jaws-scripts'
copyright = '2022, Ryan Slominski'
author = 'Ryan Slominski'

# The full version, including alpha/beta/rc tags
release = '4.5.2'


# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx_click'
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
html_theme = "sphinx_rtd_theme"

html_static_path = ['_static']

source_suffix = ['.rst', '.md']
