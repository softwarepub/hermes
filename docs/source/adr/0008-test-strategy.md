<!--
SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR), Forschungszentrum Jülich, Helmholtz-Zentrum Dresden-Rossendorf

SPDX-License-Identifier: CC-BY-SA-4.0
-->

# Test strategy

* Status: accepted
* Deciders: sdruskat, poikilotherm, knodel, juckel, led02
* Date: 2022-03-21

## Context and Problem Statement

We will need 

- pipeline end-to-end tests
- unit tests for logically heavy parts
- integration tests
- cross-platform tests

## Decision Drivers

* We may employ the HIFIS CI platform for more complex tests
* We will use GH Actions for faster feedback
* We will use example data/cases for testing (e.g., specific source repositories) including extreme corner cases
* Regression tests are compulsory
* Don't cheat to reach a target metric

## Considered Options

* Use test metric as soft target, evaluate useful coverage during code review

## Decision Outcome

Chosen option: "", because comes out best.
