<!--
SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)

SPDX-License-Identifier: CC-BY-SA-4.0
-->

<!--
SPDX-FileContributor: Michael Meinel
-->

# HERMES Data Model

*hermes* uses an internal data model to store the output of the different stages.
All the data is collected in a directory called `.hermes` located in the root of the project directory.

You should not need to interact with this data directly.
Instead, use {class}`hermes.model.context.HermesContext` and respective subclasses to access the data in a consistent way.

## Data representation

*hermes* operates on expanded JSON-LD datasets.
All internal data must be valid JSON-LD datasets in expanded form.
All internal data must use CodeMeta vocabulary where applicable.
All vocabulary used in internal datasets must be defined by a JSON-LD context.

*hermes* provides classes that facilitate the access to the expanded JSON-LD data.

### *hermes* internal processing data

*hermes* collects internal processing information in the `hermes-rt` namespace.

## Data cache

For each processing step there exists a command directory in the `.hermes` dir.
Within this command, there exists one further plugin directory for each plugin.
Within this plugin diretory, there are up to for files stores:

- `codemeta.json`: The (possibly extended) CodeMeta data representation of the dataset.
  This should be valid compact JSON-LD data.
- `expanded.json`: The expanded representation of the dataset. This should be valid expanded JSON-LD data.
- `context.json`: The JSON-LD context that can be used to transform `expanded.json` into `codemeta.json`.
- `prov.json`: A JSON-LD dataset that contains the provenance collected by *hermes* during the run.

