<!--
SPDX-FileCopyrightText: 2023 German Aerospace Center (DLR), Forschungszentrum Jülich GmbH

SPDX-License-Identifier: CC-BY-SA-4.0
-->

<!-- 
SPDX-FileContributor: Oliver Bertuch
SPDX-FileContributor: Michael Meinel
-->

# T01: Add HERMES to your project
 
In this tutorial we will guide you through the process of preparing your project for metadata publication.

```{note}
We assume that you have a project that is stored in a Git code repository on GitHub.
```
 
We use the [HERMES showcase repo](https://github.com/hermes-hmc/showcase) throughout this tutorial.
It should be easily adoptable to other code repositories.
 
## Clone the example code repository
 
This step is optional if you use a checked-out version of your own code repository.
 
```shell
git clone https://github.com/hermes-hmc/showcase.git hermes-showcase
cd hermes-showcase
```
 
Your directory should look like the following:
 
```{code-block}
---
linenos: True
---
.
├── CITATION.cff
├── .github
│   └── workflows
│       └── hermes.yml
├── .gitignore
├── hermes.toml
├── LICENSE
├── pyproject.toml
├── README.md
└── src
    └── showcase
        ├── hello.py
        └── __init__.py
```

(Again: if you use this for your own project, your mileage will vary.)

At this point, the important files for HERMES are `CITATION.cff` (structured metadata), `hermes.toml`
(workflow configuration) and `.github/workflows/hermes.yml` (CI job for publication).
 
## Test-drive hermes
 
You can run the workflow locally to verify results before adding it to your continuous integration configuration.

Installation assumes you have `python` v3.10+ installed:

```shell
pip install "git+https://github.com/hermes-hmc/workflow.git@deRSE23"
```

Once installed, simply run the workflow:

```shell
hermes
```

The output will look like follows, indicating metadata is collated from `CITATION.cff` and `Git` history:

```plain
hermes workflow (0.1.0)
=======================

Workflow to publish research software with rich metadata

# Running Hermes
Running Hermes command line in: <some place you checked out the showcase>/hermes-showcase
# Metadata harvesting
- Running harvester cff

## Citation File Format

- Running harvester git

## Git History


# Metadata processing
## Process data from cff

### Add author names

## Process data from git

### Add git authors and committers as contributors

### Add git branch
```

You can see that there are only two stages of the pipeline executed, "harvesting" and "processing".
This is the default behavior as you certainly want to review the results, especially if you just started
adding metadata to your code repository.
 
If you look at your working directory, it should look similar to this:

```{code-block}
---
linenos: True
---
.
├── .github
│   └── workflows
│       └── hermes.yml
├── .gitignore
├── .hermes
│   ├── harvest
│   │   ├── cff.json
│   │   └── git.json
│   └── process
│       ├── codemeta.json
│       └── tags.json
├── hermes-audit.md
├── hermes.log
├── hermes.toml
├── LICENSE
├── pyproject.toml
├── README.md
└── src
    └── showcase
        ├── hello.py
        └── __init__.py
```

Note the new directory `.hermes`. This is automatically created and maintained by the workflow to store the metadata
at the different stages. Inside that folder you will find a sub-folder for every stage.
The cache files are JSON and can be inspected to investigate into the results of the different stages.

Also new are the files `hermes-audit.md` and `hermes.log`. You may ignore both for now, they currently are mostly
useful for development and debugging.


## Configure your .gitignore
 
As the `.hermes` folder contains transient caches, it is a good idea to not store it in your code repository.
Hence, it is a good idea to add this folder to your `.gitignore` file, along with the log files.
 
Create a new `.gitignore` and add `.hermes` to it:
 
```
echo ".hermes" >> .gitignore
echo "hermes.log" >> .gitignore
echo "hermes-audit.md" >> .gitignore
```

(This has already been done in the `showcase` project)
 
## Provide additional metadata using CITATION.cff
 
Until now, there is not much metadata to publish for your project.
We will change this by adding a [`CITATION.cff`](https://citation-file-format.github.io/) file to your code repository.
This file stores metadata about the authors of a software project and how to reference it in publications.

The `showcase` project contains a fake but working example as outlined above.
You may copy [this example file](https://github.com/hermes-hmc/showcase/blob/main/CITATION.cff) to your own project 
and adapt or use [cffinit](https://citation-file-format.github.io/cff-initializer-javascript/) to start anew.
 
Please make sure to add your own `CITATION.cff` to your version controlled project.
 
## Configuration of your project
 
The HERMES workflow is fully configurable via a [TOML](https://toml.io) file `hermes.toml`.
This file is structured by having a table for each step of the workflow:

```toml
[harvest]
[process]
[deposit]
[postprocess]
```

HERMES has opinionated defaults, living the "convention over configuration" paradigm, for every step.
If you are not satisfied with the defaults, you can override anything by applying your own configuration.

The `showcase` repository contains a `hermes.toml`, which as an example

- configures to include the Git and Citation File Format metadata harvesters only,
- disables validation in the CFF file harvester,
- activates mapping and deposition to an Invenio based repository,
- and configures the Zenodo Sandbox as the target publication repository:

```toml
[harvest]
from = [ "cff", "git" ]

[harvest.cff]
validate = false

[deposit]
mapping = "invenio"
target = "invenio"

[deposit.invenio]
base_url = "https://sandbox.zenodo.org"
```

Simply copy and paste this file to your own project for now just to get started.

```{note}
Right now, the HERMES workflow only supports a limited number of operations in its "Proof Of Concept" state.
Expect a bumpy ride when trying to alter this minimal configuration.
```

## Optional: Testing depositing locally

Targeting the Zenodo Sandbox, please [receive a "Personal Access Token" from them via your user profile](https://sandbox.zenodo.org/account/settings/applications/tokens/new/)
with the scopes `deposit:actions` and `deposit:write` so the workflow can act on your behalf.

Before executing a deposition, please think about whether you want to include your software as an artifact in it.
A simple example to do that is to create a ZIP file of your sources, here using the `showcase` project:

```shell
git archive --format zip HEAD src > showcase.zip
```

To create a software publication that also includes the software artifact now run:

```shell
hermes deposit --auth-token <PAT here> --file README.md --file showcase.zip
```

If all goes well, you will find the URL of the deposit in the output:
```plain
hermes workflow (0.1.0)
=======================

Workflow to publish research software with rich metadata

# Running Hermes
Running Hermes command line in: <some place you checked out the showcase>/hermes-showcase
Metadata deposition
Published record: https://sandbox.zenodo.org/record/1166086
```

## Add a deposit job via CI

```{note}
This example uses Github Action syntax, but can be transfered to Jenkins or GitLab CI syntax.
```

Add a file `.github/workflows/hermes.yaml` to your project by copy and pasting
[the example from the `showcase` project](https://github.com/hermes-hmc/showcase/blob/main/.github/workflows/hermes.yml):

```yaml
name: Software Publication

on:
  tags: # Change as you see fit for your project!

jobs:
  hermes:
    name: HERMES
    runs-on: ubuntu-latest
    permissions:
      contents: read # We will only read content from the repo
      # pull-requests: write # Postprocessing should be able to create a pull request with changes
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install git+https://github.com/hermes-hmc/workflow.git@deRSE23
      - run: git archive --format zip HEAD src > showcase.zip
      - run: hermes
      - run: hermes deposit --auth-token ${{ secrets.ZENODO_SANDBOX }} --file showcase.zip --file README.md
      # - run: hermes postprocess # (Not implemented yet)
      # - uses: peter-evans/create-pull-request@v4 (TODO once postprocessing has it)
```

Within this workflow, we use a secret called `ZENODO_SANBOX`, which you will need to
[add to your Github repository](https://docs.github.com/en/actions/security-guides/encrypted-secrets#creating-encrypted-secrets-for-a-repository)
and contains your "Personal Access Token".

Now, once you create a new Git tag in your code repository, the HERMES workflow will create a rich metadata
software publication for you within the Zenodo Sandbox.
