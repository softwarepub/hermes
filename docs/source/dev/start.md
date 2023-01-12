# Tutorial: Start to develop HERMES

Following this tutorial will guide you along setting up a local copy of the code for development of the workflow itself.
This is not necessary if you only want to use HERMES or want to develop an extension plugin loaded at runtime.

```{note}
In the future, there will be a tutorial how to extend HERMES with a plugin available.
```

## Prepare your environment

First, install Python 3.10 and activate your Python environment of you choice (e.g., `venv`, `conda`, `pipenv`, ...).
This is very dependent on which Python environment you prefer.

Next to Python 3.10 you need to [install `poetry`](https://python-poetry.org/docs/#installation) inside your environment
to manage and install dependencies. Please note we require using `poetry>=1.2`.

If you use `conda`, the above can be achieved with the following commands:

```shell
conda create --name hermes python=3.10 poetry
```

You should confirm whether to proceed.

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
- [Architectural Design Records (ADR)](https://adr.github.io/) are in `docs/adr`
- API documentation is automatically generated into `docs/source/api`
- All other Sphinx-based documentation lives in `docs/source/*`

This project uses 

- a development branch (`develop`) to merge developments into, this is the default branch
- actual development is done on "feature" branches (this includes non-feature work such as bug fixing), see also our
  {doc}`contribute`.
- a `main` branch which only includes releases

## Install HERMES and dependencies

To finally install all the required dependencies and HERMES itself, you can now use `poetry`:

```
poetry install
```

### Which dependencies do we use?

Our feature implementations build upon these main dependencies:

- [`click`](https://click.palletsprojects.com/) for providing a commmand line interface
- [`jsonschema`](https://python-jsonschema.readthedocs.io) to validate different JSON based file formats
- [`ruaml.yaml`](https://yaml.readthedocs.io) to parse and validate YAML files
- [`cffconvert`](https://github.com/citation-file-format/cff-converter-python) to harvest data from the CITATION.cff file

Finally, there are some dependencies that are only required for active development. These are:

- `pytest`, `pytest-cov` to run the developer tests and monitor the test coverage
- `Sphinx`, `myst-parser` to build the documentation
- `flake8` to check the coding style

While there is no containerized or installable version of Hermes available yet, you need to install it manually into
your Python environment for development, see below.


## Verify installation works

That's it, you should now have a working development copy of HERMES in your environment.
You can confirm this by running `hermes`, seeing how it harvests all the information from the input:

```shell
hermes
```

## Verify tests can be run

Tests are implemented using [pytest](https://pytest.org). You can generate coverage report using the `pytest-cov` plugin.
Both tools are specified as development dependencies in the `pyproject.toml`.

To verify tests with an extensive HTML report run, execute:

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

Or use [`sphinx-autobuild`](https://) to enable a self-updating preview service:

```shell
poetry install --with docs
poetry run task docs-live
```

Note: you need to run `poetry install` again here because the docs dependencies are optional!

