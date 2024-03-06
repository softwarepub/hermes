<!--
SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR), Forschungszentrum Jülich, Helmholtz-Zentrum Dresden-Rossendorf

SPDX-License-Identifier: CC-BY-SA-4.0
-->

# We care for code quality

* Status: proposed
* Date: 2022-03-23

## Context and Problem Statement

We want our code to be of high quality for the well-known reasons.
Therefore, we want to employ a cod quality strategy to safeguard this aim.

## Decision Drivers

* Maintainability
* Reproducibility (of builds)
* Adherance to Python style, good practices
* Automatability (of e.g., doc building)

## Considered Options

* Sonarcloud.io

## Decision Outcome

Chosen option: "Sonarcloud.io", because comes out best.

## Pros and Cons of the Options

### Sonarcloud.io

A free code quality SonarQube instance, provides the standard code quality tools, addressable from CI

* Good, because Free (as in beer)
* Bad, because External dependency to a 3rd party platform

## Links

* https://sonarcloud.io
