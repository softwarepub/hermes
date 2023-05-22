<!--
SPDX-FileCopyrightText: 2023 German Aerospace Center (DLR), Forschungszentrum Jülich GmbH

SPDX-License-Identifier: CC-BY-SA-4.0
-->

<!-- 
SPDX-FileContributor: Oliver Bertuch
SPDX-FileContributor: Michael Meinel
SPDX-FileContributor: Stephan Druskat
-->

# Set up automatic software publishing
 
```{note}
This tutorial works for repositories hosted on GitHub, and shows how to automatically publish to Zenodo Sandbox.
Zenodo Sandbox is a "toy" repository that can be used to try things out.

This tutorial should also work with the "real" Zenodo.
```
 
## Configure your .gitignore
 
The HERMES workflow (`hermes`) uses temporary caches in `.hermes/`.
Ignore this directory in your git repository.

Add `.hermes/` to your `.gitignore` file:
 
```{code-block} bash
:caption: .gitignore

.hermes/
```

## Provide additional metadata using CITATION.cff
 
To provide high-quality citation metadata for your project and your publication,
provide a `CITATION.cff` file in the [Citation File Format](https://citation-file-format.github.io/).

If you don't have one yet,
use the [cffinit](https://citation-file-format.github.io/cff-initializer-javascript/) website
to create a `CITATION.cff` file.
Save it to the root directory of your repository, and add it to version control.

```bash
git add CITATION.cff
git commit -m "Add citation file"
git push
```
 
## HERMES configuration
 
The HERMES workflow is configured in a [TOML](https://toml.io) file: `hermes.toml`.
Each step in the publication workflow has its own section.

Configure HERMES to:

- harvest metadata from Git and `CITATION.cff`
- skip validation of `CITATION.cff`
- deposit on Zenodo Sandbox (which is built on the InvenioRDM)
- use Zenodo Sandbox as the target publication repository

```{code-block} toml
:caption: hermes.toml
:name: hermes.toml

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

Copy this file to your repository and add it to version control:

```bash
git add hermes.toml
git commit -m "Configure HERMES to harvest git and CFF, and deposit on Zenodo Sandbox"
git push
```

## Get a personal access token for Zenodo Sandbox

To allow GitHub Actions to publish our repository to Zenodo Sandbox for us,
we need a personal access token from Zenodo Sandbox.

Log in at https://sandbox.zenodo.org (you may have to register first),
then [create a personal access token in your user profile](https://sandbox.zenodo.org/account/settings/applications/tokens/new/)
with the scopes `deposit:actions` and `deposit:write`.

Copy the newly created token into a new [GitHub Secret](https://docs.github.com/en/actions/security-guides/encrypted-secrets#creating-encrypted-secrets-for-a-repository) called `ZENODO_SANDBOX` in your repository.

## Configure a GitHub Action to automate publication 

The HERMES project provides templates for continous integration systems in a dedicated repository:
https://github.com/hermes-hmc/ci-templates.

Copy the [template for GitHub to Zenodo Sandbox publication](https://github.com/hermes-hmc/ci-templates/blob/main/TEMPLATE_hermes_github_to_zenodo.yml)
into the `.github/workflows/` directory in your repository, and rename it as you like (e.g. `hermes_github_to_zenodo.yml`).

Go through the file, and look for comments marked with `# ADAPT`.
Adapt the file to your needs.
If you need help with how GitHub Action workflows work in general,
have a look at the [documentation on GitHub](https://docs.github.com/actions).

Add the workflow file to version control and push it.

```{warning}
If you haven't adapted the workflow file, and push it to the branch `main`, you will create an automatic publication at this point.
```

```bash
git add .github/workflows/hermes_github_to_zenodo.yml
git commit -m "Configure automatic publication with HERMES"
git push
```

## Automatic publication workflow

```{admonition} Congratulations!
You can now automatically publish your repository to Zenodo Sandbox!
```

````{margin}
```{mermaid}
---
---
flowchart TD
    t(("Trigger\n (i.e. push)")) -->
    ci1("Run Harvest, Process,\n Curate steps") -->
    pr1("Create Curation PR") -->
    d{"Accept?"}
    d -->|Merge| ci2("Run Deposit &\n Postprocess step") --> pr2("Create PR from\n Postprocessing") --> e((("End")))
    d -->|Close| ci3("Cleanup") --> e((("End")))
```
````

Now, whenever the GitHub Actions workflow is triggered, it will publish a new version of your repository to Zenodo Sandbox.
If you haven't adapted the workflow file, this will happen whenever you push to your `main` branch.

The diagram on the right shows the different steps that will happen each time.

When the workflow runs, it harvests and processes the metadata from Git and your `CITATION.cff` file,
and creates a new pull request in your repository.
You then have the chance to curate the metadata, i.e., make sure that it looks the way you want.
If you merge the pull request, the actual publication is created, 
and the HERMES configuration file is updated 
with the ID of the publication.
This is needed so that future published versions are collected under the same [*concept DOI*](https://help.zenodo.org/#versioning).

If the updates from the publication actually change the configuration file, or the `CITATION.cff` file,
HERMES will create another pull request after publication.
In this pull request, you can accept or reject the changes that are made.
