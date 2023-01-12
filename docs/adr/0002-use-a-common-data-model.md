<!--
SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR), Forschungszentrum Jülich, Helmholtz-Zentrum Dresden-Rossendorf

SPDX-License-Identifier: CC-BY-SA-4.0
-->

# Use a common data model

* Status: accepted
* Deciders: sdruskat, poikilotherm, knodel, juckel, led02
* Date: 2022-03-07

## Context and Problem Statement

We need a data model that's

- extensible, to take up metaedata that cannot yet be included in CodeMeta.json
- compatible with RO-Crate

to exchange data between modules.

## Considered Options

* CodeMeta + schema.org via RO-Crate
* CodeMeta + schema-based, extended JSON-LD for internal data model

## Decision Outcome

Chosen option: "CodeMeta + schema-based, extended JSON-LD for internal data model", because extensibility is safeguarded, but can still be written out to standards.

### Positive Consequences

* Compatibility with RO-Crate
* Compatibility with CodeMeta

### Negative Consequences

* Conversion step necessary to write out to existing standards

## Pros and Cons of the Options

### CodeMeta + schema.org via RO-Crate

* Good, because Works with RO-Crate
* Bad, because May not include potentially needed fields

### CodeMeta + schema-based, extended JSON-LD for internal data model

* Good, because Can still be written to pure CodeMeta
* Bad, because Danger of implicitly creating another standard (can be curcumvented by careful definition of relations)
