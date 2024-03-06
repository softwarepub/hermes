<!--
SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR), Forschungszentrum Jülich, Helmholtz-Zentrum Dresden-Rossendorf

SPDX-License-Identifier: CC-BY-SA-4.0
-->

# Use native API interfaces for deposit

* Status: accepted
* Deciders: sdruskat, poikilotherm, knodel, juckel, led02
* Date: 2022-03-07

## Context and Problem Statement

We need to use interfaces to deposit software on the target systems. Should we use dedicated wrapper libraries, e.g., for SWORD or for the single systems?

SWORD provides a standard way to deposit metadata in DublinCore.

## Decision Drivers

* We want to use maximally standard ways for deposition.
* We don't want to rely on too many third-party libraries.
* We want to use generic solutions.

## Considered Options

* Use wrapper libraries for target systems, e.g. Zenodraft for Zenodo - may need to be adapted for InvenioRDM proper - or pyDataverse
* Use SWORD, either via API endpoints or wrapper library, as one way to deposit metadata in addition to more generic ways
* Use native API endpoints initially for deposit
* Build own SWORD endpoint that dispatches to other APIs

## Decision Outcome

Chosen option: "Use native API endpoints initially for deposit", because It is the most usable solution at the moment.

### Positive Consequences

* We'll have a working solution

### Negative Consequences

* We have to target the different system-native endpoints

## Pros and Cons of the Options

### Use SWORD, either via API endpoints or wrapper library, as one way to deposit metadata in addition to more generic ways

* Good, because Standard way to deposit
* Bad, because At least the Dataverse SWORD interface is reportedly not easily usable for our purposes

### Use native API endpoints initially for deposit

* Good, because The endpoints work

### Build own SWORD endpoint that dispatches to other APIs

* Good, because Provides a potentially unified interface that may make it easier to deposit via SWORD later on
* Bad, because Still needs translation
