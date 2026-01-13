# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR), Forschungszentrum Jülich
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Stephan Druskat
# SPDX-FileContributor: Oliver Bertuch
# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: David Pape


# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
import toml

sys.path.insert(0, os.path.abspath('../../src'))
sys.path.append(os.path.abspath('_ext'))

def read_from_pyproject(file_path="../../pyproject.toml"):
    """
    Reads the metadata from the pyproject.toml file.

    :param file_path: Path to the pyproject.toml file (default: "pyproject.toml")
    :return: A list of authors or a message if no authors are found.
    """
    try:
        # Load the pyproject.toml file
        data = toml.load(file_path)

        # Navigate to the authors metadata
        metadata = data.get("tool", {}).get("poetry", {})
        if not metadata:
            return "No metadata found in pyproject.toml"
        return metadata
    except FileNotFoundError:
        return f"The file {file_path} was not found."
    except toml.TomlDecodeError:
        return f"Failed to parse {file_path}. Ensure it is a valid TOML file."
    except Exception as e:
        return f"An unexpected error occurred: {e}"

def read_authors_from_pyproject():
    metadata = read_from_pyproject()
    authors = metadata.get("authors", [])
    if not authors:
        return "No authors metadata found in pyproject.toml"
    # Convert the list of authors to a comma-separated string
    return ", ".join([a.split(" <")[0] for a in authors])

def read_version_from_pyproject():
    metadata = read_from_pyproject()
    version = metadata.get("version", "")
    if not version:
        return "No version metadata found in pyproject.toml"
    return version


# -- Project information -----------------------------------------------------

project = 'HERMES Workflow'
copyright = '2025 by Forschungszentrum Jülich (FZJ), German Aerospace Center (DLR) and Helmholtz-Zentrum Dresden-Rossendorf (HZDR)'
author = read_authors_from_pyproject()

# The full version, including alpha/beta/rc tags
release = read_version_from_pyproject()


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.intersphinx',
    'sphinx.ext.extlinks',
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.todo',
    'sphinx.ext.ifconfig',
    'sphinx.ext.githubpages',
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx-favicon',
    'sphinxcontrib.contentui',
    'sphinxcontrib.images',
    'sphinxcontrib.icon',
    'sphinxemoji.sphinxemoji',
    "sphinxext.opengraph",
    'myst_parser',
    'autoapi.extension',
    'sphinxcontrib.mermaid',
    'sphinx_togglebutton',
    'sphinxcontrib.datatemplates',
    # Custom extensions, see `_ext` directory.
    # 'plugin_markup',
]

language = 'en'

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['Thumbs.db', '.DS_Store']

# Prefix document path to section labels, to use:
# `path/to/file:heading` instead of just `heading`
autosectionlabel_prefix_document = True

# MyST parser options
myst_enable_extensions = [
    'tasklist',
    'deflist',
]
myst_heading_anchors = 4

# Sphinx API docs configuration, see https://sphinx-autoapi.readthedocs.io/en/latest/reference/config.html
autoapi_type = "python"
autoapi_dirs = ["../../src"]
autoapi_root = "api"
autoapi_ignore = ["*__main__*"]

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_book_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

html_logo = '_static/img/hermes-visual-blue.svg'
html_title = 'HERMES Documentation'

# Custom sidebar templates, maps document names to template names.
html_sidebars = {
    "**": ["navbar-logo.html", "sbt-sidebar-nav.html", "funding.html"]
}

# Enable and customize the permanent headerlinks with a nice icon (chain symbol from FontAwesome)
html_permalinks = True
html_permalinks_icon = "<i class=\"fas fa-link\"></i>"

html_theme_options = {
    "home_page_in_toc": True,
    "repository_url": "https://github.com/hermes-hmc/hermes",
    "use_repository_button": True,
    "navigation_with_keys": False,
}

html_css_files = [
    'custom.css',
]

html_context = {
    "default_mode": "light",
}

# -- Options for OpenGraph Tags ----------------------------------------------

ogp_site_url = "https://docs.software-metadata.pub/"
ogp_image = "https://docs.software-metadata.pub/en/latest/_static/img/opengraph-workflow.png"
ogp_image_alt = "The HERMES key visual on a blue background with pipelines and the Workflow subproject title"
ogp_description_length = 200
ogp_type = "website"

# -- Options for sphinx-togglebutton -----------------------------------------

togglebutton_hint = "Click to show screenshot"
