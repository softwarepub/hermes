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


## Harvest Data

The data of the havesters is cached in the sub-directory `.hermes/harvest`.
Each harvester has a separate cache file to allow parallel harvesting.
The cache file is encoded in JSON and stored in `.hermes/harvest/HARVESTER_NAME.json`
where `HARVESTER_NAME` corresponds to the entry point name.

{class}`hermes.model.context.HermesHarvestContext` encapsulates these harvester caches.
