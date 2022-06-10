# Record provenance of metadata

* Status: proposed
* Date: 2022-05-30

## Context and Problem Statement

To enable tracability of the metadata, and resolution based on metadata sources in case of duplicates, etc., we need to record the provenance of metadata values. To do this, we need to specify a way to do this.

## Considered Options

* Internal comment field
* Dedicated metadata field
* Use PROV standard

## Decision Outcome

Chosen option: "", because comes out best.

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
