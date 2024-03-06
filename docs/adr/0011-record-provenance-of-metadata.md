<!--
SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR), Forschungszentrum Jülich, Helmholtz-Zentrum Dresden-Rossendorf

SPDX-License-Identifier: CC-BY-SA-4.0
-->
# Record provenance of metadata

* Status: accepted
* Deciders: sdruskat, jkelling, led02, poikilotherm, skernchen
* Date: 2023-11-15

Technical story: https://github.com/hermes-hmc/hermes/pull/40

## Context and Problem Statement

To enable traceability of the metadata, and resolution based on metadata sources in case of duplicates, etc., we need to record the provenance of metadata values.
To do this, we need to specify a way to do this.

## Considered Options

* Internal comment field
* Dedicated metadata field
* Use PROV standard
* Separate internal provenance model
* Create wrapped JSON-LD entities and add our metadata ([json-ld/json-ld.org#744](https://github.com/json-ld/json-ld.org/issues/744))
* Create non-standard JSON-LD extension with custom [keywords]

## Decision Outcome

Chosen option: "Create non-standard JSON-LD extension with custom [keywords]", because comes out best.

## Pros and Cons of the Options

### Positive Consequences

* We have a unified data model and keep both provenance and actual data at the sample place
* Unifying the data model requires less complex handling in the implementation, as there is no need to recombine data
* It's not possible to loose the provenance information, as it is added to any attribute stored in the model

### Negative Consequences

* We loose the ability to reuse the serialized internal data model as output files (CodeMeta) without further processing
* We have to document these added keywords very well for plugin developers
* We need to define a ontology for this (internal) provenance metadata

### Internal comment field

This would be a comment attached to single metadata fields to record provenance.

* Bad, because Non-standard way to record this kind of information, i.e., non-reusable
* Bad, because Extra documentation effort

### Dedicated metadata field

This would be an extra metadata field to be attached to each field (?), e.g., with a URI (`source: https://repo.org/user/project/codemeta.json` or similar)

* Good, because Very generic way to specify the source of information
* Bad, because Very generic way to specify the source of information
* Bad, because Non-standard way to record provenance

### Use PROV standard

This attaches provenance information following PROV-O to metadata fields

* Good, because Standardized for provenance information
* Good, because Not much extra documentation needed
* Bad, because More circumvent way to describe relatively constricted cases (probably only use a few entities and `prov:wasInformedBy` or similar)

### Separate internal metadata about metadata model

This would create a valid JSON-LD file serializing our internal data model and a auxiliary file with the provencance data

* Good, because keeping things separate enables direct reuse and validation of the data model file
* Good, because serialization of the provenance data is free form and simple to do
* Bad, because we need to re-combine provenance and metadata
* Bad, because we have more files in the output which might confuse people
* Bad, because not easy to debug when recombination fails

### Create wrapped JSON-LD entities and add our metadata

This would work around the limitation of RDF and JSON-LD that [value objects](https://www.w3.org/TR/json-ld/#value-objects) are non-extensible

* Good, because standard compliant, still validates using standard validators
* Bad, because very noisy in the output files
* Bad, because still needs back references to the object when using `@id` in graph objects
* Bad, because would require our own ontology and repeating any field ever needed (when keeping the original fields and not using a graph object)
* Bad, because would require our own objects to keep the type and value separated, requiring reparsing when writing output files

### Create non-standard JSON-LD extension with custom keywords

This would work around the limitation of RDF and JSON-LD that [value objects](https://www.w3.org/TR/json-ld/#value-objects) are non-extensible

* Good, because easy to implement in our custom handling of the graph as Python dictionaries
* Good, because not very noisy
* Good, because keywords are the JSON-LD way to provide metadata already
* Good, because very light extension and not touching definitions from other ontologies
* Good, because we can still make use of an ontology for the metadata objects to provide an open/closed principle compliant structure
* Bad, because not standard compliant
* Bad, because needs filtering when writing output files

[keywords]: https://www.w3.org/TR/json-ld/#keywords