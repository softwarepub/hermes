<!--
SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR), Forschungszentrum Jülich, Helmholtz-Zentrum Dresden-Rossendorf

SPDX-License-Identifier: CC-BY-SA-4.0
-->
# Overall data model design

* Status: proposed
* Date: 2022-07-06

## Context and Problem Statement

Data from different stages has different requirements towards the consistency and meta-meta data.
E.g., during harvesting it is important to keep all different possible values for a certain attribute.
It is also curcial to add information about the source of the data.
In contrast in the deposit state only curated, well defined, and unambiguous data should be stored.
The source for single attributes is not required anymore.

## Considered Options

* One common model for all stages
* Seperate model for different stages
* Common model for all stages
* Processing model and curated model

## Decision Outcome

Chosen option: "Seperate model for different stages", because comes out best.

## Pros and Cons of the Options

### One common model for all stages

A common data model that is capable of storing all information required by HERMES throughout the whole workflow.

* Good, because Single, consistent model
* Good, because Less classes to cope with
* Bad, because Complex model
* Bad, because Complex interface
* Bad, because Probable case of YAGNI
