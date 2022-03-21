# Expose internal data model to allow mapping configurations

* Status: proposed
* Date: 2022-03-21

## Context and Problem Statement

Single instances of target repositories may need specific fields to be mapped. Therefore, mapping from our data model to the required model for these repos must be configurable, through either

- a mapping file
- a required function

Our deliverable should also include base templates for vanilla InvenioRDM and Dataverse installations of the latest* version.

## Decision Drivers

* Ensure usability for customized instances

## Considered Options

* Mapping file
* Required mapping function

## Decision Outcome

Chosen option: "", because comes out best.

## Pros and Cons of the Options

### Mapping file

* Good, because Simple to configure (no Python knowledge needed)
* Bad, because Need to definbe a semantic

### Required mapping function

* Good, because extremely versatile
* Bad, because Python knowledge needed
