<!--
SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)

SPDX-License-Identifier: CC-BY-SA-4.0
-->

<!-- 
SPDX-FileContributor: Michael Meinel
-->

# Tutorial 1: Make your project compatible with Hermes
 
In this tutorial we will guide you through the process of preparing your project for metadata publication.
We assume that you have a project that is stored in a Git repository.
There is no obvious additional metadata available.
 
We use https://github.com/hermes-hmc/base-example throughout this tutorial.
It should be easily adoptable to other repositories.
 
## Clone the repository
 
This step is optional if you use a checked-out version of your own repository.
 
```
git clone https://github.com/hermes-hmc/base-example.git
cd base-example
```
 
Your directory should look like the following:
 
...
 
## Test-drive hermes
 
Even though there is no metadata stored yet, you should already get some output from Hermes
as it collects author information from the Git history.
To check for this, run:
 
```shell
haggis
```
 
The output will look like follows:
 
```
Metadata harvesting
Metadata processing
```
 
Not much to see here yet.
You can see that there are only two stages of the pipeline executed.
This is the default behavior as you certainly want to review the results,
especially if you just started adding metadata to your repository.
 
If you look at the output folder, you should notice a new directory `.hermes`.
This is automatically created and maintained by Hermes to store the metadata at the different stages.
Inside that folder you will find a sub-folder for every stage.
The cache files are JSON and can be inspected to investigate into the results of the different stages
(topic of future tutorial).
 
```{todo}
Write more about the different output files Hermes generates:
 
- .hermes/harvest/*.json -> Harvest cache files (might be ambiguous; contains all tags)
- .hermes/process/tags.json -> Tags for all entries in the `codemeta.json`
- hermes.log -> Complete log file; useful for debugging
- hermes-report.{md,html} -> Report on what Hermes did
```
 
## Configure your .gitignore
 
As the `.hermes` folder contains transient caches, it is a good idea to not store it in your Git repository.
Hence, it is a good idea to add this folder to your `.gitignore` file.
 
Create a new `.gitignore` and add `/.hermes` to it:
 
```
echo "/.hermes" > .gitignore
```
 
## Provide additional metadata using CITATION.cff
 
Until now, there is not much metadata to publish.
We will change this by adding a `CITATION.cff` file to the repository.
This file stores metadata about the authors of a software project and how to reference it in publications.
 
Create a file `CITATION.cff` with the following contents:
 
```yaml
# This CITATION.cff file was generated with cffinit.
# Visit https://bit.ly/cffinit to generate yours today!
 
cff-version: 1.2.0
title: Hermes Example Project
message: >-
  If you use this software, please cite it using the
  metadata from this file.
type: software
authors:
  - given-names: Michael
    family-names: Meinel
    email: michael.meinel@dlr.de
    affiliation: German Aerospace Center (DLR)
    orcid: 'https://orcid.org/0000-0001-6372-3853'
```
 
Now, if you run Hermes again, you should get some first results:
 
```shell
haggis
```
 
The output should look like the following:
 
```
Metadata harvesting
Found valid Citation File Format file at: CITATION.cff
Metadata processing
```
 
There is also a `codemeta.json` file generated that contains information found in `CITATION.cff`.
You should only add `CITATION.cff` to your repository, but not the generated `codemeta.json` (at least for now).
 
You will also find a `hermes-report.md` file and an matching `hermes-report.html`
that can be reviewed to see details on what Hermes did.
 
## Configuration of your project
 
Hermes currently is very focussed on Python projects.
Hence, it loads configuration settings from the `pyproject.toml` file.
This will change in future to be more flexible.
 
Until then, you can still use the `pyproject.toml` for your Hermes configuration.
The table `tool.hermes.logging` is directly passed to Python's `logging.config.dictConfig`
method and is used to adapt your logging output.
 
Hermes currently uses the following top-level loggers:
 
`cli`
:   The log can be used to output only to command line.
 
`audit`
:   Logs to `audit.md` and should contain all processes run and (automated) decisions made.
 
`audit.hints`
:   Hints on how to resolve conflicts / ambiguities found during havest and process.
 
`hermes`
:   General logging output.