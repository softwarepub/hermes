<!--
SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR), Forschungszentrum Jülich, Helmholtz-Zentrum Dresden-Rossendorf

SPDX-License-Identifier: CC-BY-SA-4.0
-->

# Use high-level modularization

* Status: accepted
* Deciders: sdruskat, juckel, knodel, poikilotherm, led02
* Date: 2022-03-07

## Context and Problem Statement

We want to support arbitrary recombination of modules from the workflows.
There are at least four levels of architecture where modularization can be achieved:
1. Workflow level: Running workflows
1. Application level: Organizing the single workflow pipelines
2. Pipeline level: Combining processing steps within a single domain (i.e., harvesting, processing, deposition, post-processing)
3. Processing step level: A single data retrieval or transformation step

## Decision Drivers

* - Reusability
* - Domain-driven design
* - Clean architecture

## Considered Options

* Meta CLI application with modularized independent steps
* One application per pipeline
* One application per processing step

## Decision Outcome

Chosen option: "Meta application with modularized independent steps", because Modularity, reusability and configurability can be achieved in a meta ("runner") application that call the single pipelines. Provides a unified user interface.

### Positive Consequences

* Good practice
* High SOC
* Enables strongly domain-driven design
* Ease of maintenance for single steps
* Simple mocking of steps (I=O)

### Negative Consequences

* Engineering overhead (many projects)
* Needs strictly defined interfaces for data exchange

## Pros and Cons of the Options

### Meta CLI application with modularized independent steps

A single application that provides access to at least the pipeline steps

* Good, because Everything in one place, one language, one ecosystem
* Good, because Less need for highly formalized internal interchange format or serialization
* Bad, because More monolithic than the other architectures

### One application per pipeline

Each of the four pipelines has its own application package. Data is interchanged through a common interface/interchange format.

* Good, because Clear separation of pipeline domains
* Good, because Easy to assemble workflow
* Bad, because May be internally too monolithic to reuse specific steps

### One application per processing step

Each processing step has its own application

* Good, because Maximal modularization and reusability/reconfigurability
* Bad, because Engineering overhead (many projects instead of a few)
