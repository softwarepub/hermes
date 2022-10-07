<!--
SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR), Forschungszentrum Jülich, Helmholtz-Zentrum Dresden-Rossendorf

SPDX-License-Identifier: CC-BY-SA-4.0
-->

# CLI takes single sources and targets only

* Status: proposed
* Deciders: sdruskat
* Date: 2022-06-22

## Context and Problem Statement

There are potentially two way to use the CLI in case of multiple software sources in a single repository:

1. The workflow is run once for all software sources
2. The workflow is run for each source

The cases this would have to work for are:

- Single software source (with single target)
- Single software source (with multiple, different targets)
- Multiple software sources (with single target)
- Multiple software sources (with multiple, different targets)

## Decision Drivers

* Ease of implementation
* Clear use case: UNIX-style single purpose tool vs. swiss army knife

## Considered Options

* Let CLI take multiple targets and multiple sources
* Let CLI take exactly one source and exactly one target

## Decision Outcome

Chosen option: "Let CLI take exactly one source and exactly one target", because easier to implement and better architectural design (UNIX-style single purpose)

### Positive Consequences

* Easier to implement
* Usage is more obvious

### Negative Consequences

* Must be parallelized by downstream clients (local command line use, CI workflows)

## Pros and Cons of the Options

### Let CLI take multiple targets and multiple sources

The CLI takes multiple sources (paths) and multiple targets, and maps these, running the workflow once for all combinations

* Good, because CLI only has to be run once
* Bad, because Mapping multiple sources and targets alone is more/harder work, and will make usage of the workflow software less obvious

### Let CLI take exactly one source and exactly one target

CLI takes these and must be run for each combination of source and target

* Good, because Single purpose
* Good, because Easier to implement
* Bad, because CLI may have to be run multiple times, depending on use case
