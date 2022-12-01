<!--
SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR), Forschungszentrum Jülich, Helmholtz-Zentrum Dresden-Rossendorf

SPDX-License-Identifier: CC-BY-SA-4.0
-->

# Use Python as base technology

* Status: accepted
* Deciders: sdruskat, poikilotherm, knodel, juckel, led02
* Date: 2022-03-21

## Context and Problem Statement

We need to decide on a single base technology to implement the workflow.

## Decision Drivers

* Project members know Python

## Considered Options

* Python >= 3.10
* Java

## Decision Outcome

Chosen option: "Python 3.10", because all project members know Python well enough

## Pros and Cons of the Options

### Python >= 3.10

We provide Python packages to be installable through standard channels (e.g., pip, conda, etc.)

* Good, because Pattern matching
* Bad, because Not massively backwards-compatible
