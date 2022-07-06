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

## Decision Outcome

Chosen option: "Seperate model for different stages", because comes out best.
