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


## Data representation

We are trying to be fully JSON-LD compliant. However, there are two special cases, where we are a bit more lazy:

- Storing provenance of harvested data (for later curation)
- Storing alternatives of harvested data (for later curation)

Internally, `hermes` works with the expanded version of the JSON-LD file.
However, there are helper classes that allow you to use compact references.

For the storing of provenance and alternatives, we introduce our own terms.
Especially, we add a `hermes:meta` key to the top level record.
This top level key contains a list of additional meta-metadata (i.e., provenance and alternatives).

Each entry in the meta-metadata list is a dictionary that contains at least a `reference` value and one or more of
`provenance` and `alternative` keys.
The `refrence` value should be a valid JSON Path that references the object that is subject to these metadata.
The `provenance` value should be a JSON dataset that keeps information about where the data came from.
The `alternative` value should be a list with alternative records.

Each alternative record contains a `value` and probably an additional `provenance` key.

Example:

```json
{
	"@context": [
		"https://doi.org/10.5063/schema/codemeta-2.0",
		{"hermes": "https://schema.software-metadata.pub/hermes/1.0"},
		{"legalName": {"@id": "schema:name"}}
	],
	"@type": "SoftwareSourceCode",
	"author": [
		{
			"@id": "https://orcid.org/0000-0001-6372-3853",
			"@type": "Person",
			"affiliation": {
				"@type": "Organization",
				"legalName": "German Aerospace Center (DLR)"
			},
			"familyName": "Meinel",
			"givenName": "Michael",
			"email": "michael.meinel@dlr.de"
		}
	],
	"description": "Tool to automate software publication. Not stable yet.",
	"identifier": "https://doi.org/10.5281/zenodo.13221384",
	"license": "https://spdx.org/licenses/Apache-2.0",
	"name": "hermes",
	"version": "0.8.1",
	"hermes:meta": [
		{
			"reference": "$",
			"provenance": { "harvester": "cff", "source": "CITATION.cff" }
		},
		{
			"reference": "$.author.0.affiliation.legalName",
			"alternative": [
				{"value": "DLR e.V.", "provenance": { "harvester": "orcid" }}
			],
		}
	]
}
```
