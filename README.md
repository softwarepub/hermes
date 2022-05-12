# hermes

Implementation of the HERMES workflow.

For more information about the HERMES project, see the [HERMES project website](https://software-metadata.pub).

## Structure

- Python sources are in the `src` folder
- pytest tests are in the `test` folder
- Architectural design records are in `docs/adr`

This project uses 

- a development branch (`develop`) to merge developments into, this is the default branch
- actual development is done on "feature" branches (this includes non-feature work such as bug fixing)
- a `main` branch which only includes releases

## Set up for development

1. Clone this repository
2. If you want to use [`poetry`](https://python-poetry.org), run `poetry shell` and `poetry install`

## Usage

The `haggis`[^1] application provides the entry point for the HERMES workflow.
After installation, you can run it from your command line environment:

```shell
haggis --help
haggis harvest
```

You can also call the `hermes` package as Python module:

```shell
python -m hermes --help
python -m hermes 
```

[^1]: Working title, might be subject to change.

## Testing

Tests are implemented using [pytest](https://pytest.org).
You can generate coverage report using the `pytest-cov` plugin.
Both tools are specified as development dependencies in the `pyproject.toml`.

To run tests with an extensive HTML report, run:

```shell
poetry run pytest test --cov=hermes --cov-branch --cov-report=html --cov-report=term
```

## Building documentation

This project comes with extensive documentation that can be built using [Sphinx](https://www.sphinx-doc.org/en/master/).
This also includes automatic API documentation.
To build the documentation in your *poetry* envrionment, run the following commands:

```shell
poetry run sphinx-apidoc -o docs/source/api src
poetry run sphinx-build -M html docs/source docs/build
```
