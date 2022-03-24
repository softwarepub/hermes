# hermes

Implementation of the HERMES workflow.

For more information about the HERMES project, see the [HERMES project website](https://software-metadata.pub).

## Structure

- Python sources are in the `src` folder
- pytest tests are in the `test` folder
- Architectural design records are in `docs/adr`

## Set up for development

1. Clone this repository
2. If you want to use [`poetry`](https://python-poetry.org), run `poetry shell` and `poetry install`

This project uses 

- a development branch (`develop`) to merge developments into, this is the default branch
- actual development is done on "feature" branches (this includes non-feature work such as bug fixing)
- a `main` branch which only includes releases
