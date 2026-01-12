<!--
SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR), Forschungszentrum Jülich, Helmholtz-Zentrum Dresden-Rossendorf

SPDX-License-Identifier: CC-BY-SA-4.0
-->

# <strike>Define interfaces for inter-module data exchange</strike>

* Status: superseded
* Date: 2023-11-15

## Context and Problem Statement

This depends on the data model (ADR 0002).
Do we have to expose different parts of the data model structure at different points in the workflow?

Superseded: decisions in [ADR 2](./0002-use-a-common-data-model) (use JSON-LD) and [ADR 11](./0011-record-provenance-of-metadata)  (create a unified data model of metadata and provenance) will result in a context [DAO](https://en.wikipedia.org/wiki/Data_access_object) from beginning till end of a run.

## Decision Drivers

* Different data need to be available at different points
* Convention over configuration

## Considered Options

* Complete I/O
* Restricted I/O

## Decision Outcome

Chosen option: "", because comes out best.

## Pros and Cons of the Options

### Complete I/O

E.g., with pre-filled contents
