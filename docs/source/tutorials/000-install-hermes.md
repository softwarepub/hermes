# Tutorial 0: Installation of Hermes

The Hermes command line tool is developed using Python 3.10 and builds upon some dependencies:

- click for providing a commmand line interface
- jsonschema to validate different JSON based file formats
- ruaml.yaml to parse and validate YAML files
- cffconvert to harvest data from the CITATION.cff file

The dependencies are managed using poetry which is another dependency you need to install.

Finally, there are some dependencies that are only required for active development.
These are:

- pytest, pytest-cov to run the developer tests and monitor the test coverage
- Sphinx, myst-parser to build the documentation
- flake8 to check the coding style

While there is no containerized of installable version of Hermes available,
you need to install it manually into your Python environment.

## Prepare your environment

First, install Python 3.10 and activate your Python environment of you choice (e.g., venv, conda, pipenv, ...).
This is very dependent on which Python environment you prefer.

Next to Python 3.10 you need to install `poetry` inside your environment to manage and install dependencies.

If you use `conda`, the above can be achieved with the following commands:

```
conda create --name hermes python=3.10 poetry
```

You should confirm whether to proceed.

## Get the source code

Next, you need to obtain a version of the Hermes source code.

You can either download it as a zipped package or clone the whole Git repository.
You can clone the repository and enter the project directory as follows:

```
git clone https://gitlab.com/hermes-hmc/workflow.git
cd workflow
```

## Install dependencies and Hermes

To finally install all the required dependencies and Hermes itself, you can now use `poetry`:

```
poetry install
```


## Verify installation

That's it, you should now have a working copy of Hermes in your environment.
You can confirm this by running `haggis` (the **h**ermes **agg**regated **i**nterface **s**cript):

```
hermes
```

You should see how Hermes harvests all the information from the input.
In the end, there should be a `hermes-report.md` file that contains information about the successful run.
c