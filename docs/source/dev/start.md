<!--
SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR), Forschungszentrum Jülich

SPDX-License-Identifier: CC-BY-SA-4.0
-->

<!--
SPDX-FileContributor: Michael Meinel
SPDX-FileContributor: Oliver Bertuch
-->
  
# Tutorial: Get started with development

Follow this tutorial to set up a local copy of the code for development of the workflow itself.
This is not necessary if you only want to use HERMES or want to develop an extension plugin loaded at runtime.

## Prepare your environment

First, install Python 3.10 (or later).

Additionally, you need to [install `poetry >= 1.2.0`](https://python-poetry.org/docs/#installation), either globally, or
within an environment of your choice. As a project, we chose `poetry` to manage our dependencies, builds, and deposits
as a state of the art solution within the Python ecosystem.

## Get the source code

Next, you need to obtain a version of the HERMES source code.

You can either download it as a zipped package or clone the whole Git repository.
You can clone the repository and enter the project directory as follows:

```shell
git clone https://gitlab.com/hermes-hmc/workflow.git
cd workflow
```

## Learn how our repo is structured

- All Python sources are in the `src` folder
- `pytest` tests are in the `test` folder
- [Architectural Decision Records (ADR)](https://adr.github.io/) are in `docs/adr`
- API documentation is automatically generated into `docs/source/api`
- All other Sphinx-based documentation lives in `docs/source/*`

This project uses 

- a development branch (`develop`) to merge developments into, this is the default branch
- actual development is done on "feature" branches (this includes non-feature work such as bug fixing), see also our
  {doc}`contribute`.
- a `main` branch which only includes releases

## Install HERMES and dependencies

`poetry` comes with its own environment management. To create a development environment and install dependencies, run
```shell
# Create an environment dedicated to hermes development
poetry shell
# Install dependencies
poetry install
```

### Which dependencies do we use?

Building a CLI application, we deliberately chose the [Click framework](https://click.palletsprojects.com) to implement
the different workflow parts as commands verbs.

To learn what other packages `hermes` depends on, have a look at the project configuration file `pyproject.toml` 
(in the root of the repository), or use `poetry show --only main`. 

To show dependencies that are only required for active development, or for building documentation run
`poetry show --only dev` and `poetry show --only docs` respectively.


## Verify installation works

That's it, you should now have a working development copy of HERMES in your environment.
You can confirm this by running `hermes --help` to show available commands and options.

## Verify tests can be run

Tests are implemented using [pytest](https://pytest.org).

To run all tests, execute `pytest test/` within the activated `poetry` environment.

To create an extensive test coverage report in HTML, execute:

```shell
poetry run pytest test --cov=hermes --cov-branch --cov-report=html --cov-report=term
```

## Optional: Verify docs build

This project comes with extensive documentation that can be built using [Sphinx](https://www.sphinx-doc.org/en/master/).
This also includes automatic API documentation. To build the documentation in your *poetry* environment, run the
following commands from the project root:

```shell
poetry install --with docs
poetry run task docs-build
```

Or use [`sphinx-autobuild`](https://github.com/executablebooks/sphinx-autobuild) to enable a self-updating preview service:

```shell
poetry install --with docs
poetry run task docs-live
```

