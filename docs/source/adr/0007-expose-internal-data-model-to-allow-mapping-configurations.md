<!--
SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR), Forschungszentrum Jülich, Helmholtz-Zentrum Dresden-Rossendorf

SPDX-License-Identifier: CC-BY-SA-4.0
-->

# Expose internal data model to allow mapping configurations

* Status: proposed
* Date: 2022-03-21

## Context and Problem Statement

Single instances of target repositories may need specific fields to be mapped. Therefore, mapping from our data model to the required model for these repos must be configurable, through either

- a mapping file
- a required function

Our deliverable should also include base templates for vanilla InvenioRDM and Dataverse installations of the latest* version.

## Decision Drivers

* Ensure usability for customized instances, i.e., instances that use data models extending the vanilla repo data models, such as providing custom metadata blocks, different versions of the data model, forks, etc.
* Must be packagable to provide to end users, who shouldn't need to configure individually

## Considered Options

* Mapping file
* Required mapping function
* Provide both ways

## Decision Outcome

Chosen option: "", because comes out best.

## Pros and Cons of the Options

### Mapping file

* Good, because Simple to configure (no Python knowledge needed)
* Good, because Could be provided as a simple function reading a csv/\*ML file
* Bad, because Need to definbe a semantic

### Required mapping function

* Good, because extremely versatile
* Good, because Can implement, e.g., composed fields (many fields to one composed field and vice versa)
* Bad, because Python knowledge needed
