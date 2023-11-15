<!--
SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR), Forschungszentrum Jülich, Helmholtz-Zentrum Dresden-Rossendorf

SPDX-License-Identifier: CC-BY-SA-4.0
-->
# Record provenance of metadata

* Status: accepted
* Deciders: sdruskat, jkelling, led02
* Date: 2022-09-21

Technical story: https://github.com/hermes-hmc/hermes/pull/40

## Context and Problem Statement

To enable traceability of the metadata, and resolution based on metadata sources in case of duplicates, etc., we need to record the provenance of metadata values.
To do this, we need to specify a way to do this.

## Considered Options

* Internal comment field
* Dedicated metadata field
* Use PROV standard
* Separate internal provenance model

## Decision Outcome

Chosen option: "Separate internal metadata about metadata model", because comes out best.

## Pros and Cons of the Options

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
