# Use SWORD interfaces for deposit

* Status: accepted
* Deciders: sdruskat, poikilotherm, knodel, juckel
* Date: 2022-03-07

## Context and Problem Statement

We need to use interfaces to deposit software on the target systems. Should we use dedicated wrapper libraries, e.g., for SWORD or for the single systems?

## Decision Drivers

* We want to use maximally standard ways for deposition.
* We don't want to rely on too many third-party libraries.
* We want to use generic solutions.

## Considered Options

* - Use wrapper libraries for target systems, e.g.[Zenodraft for Zenodo](https://github.com/zenodraft/zenodraft) - may need to be adapted for InvenioRDM proper - or [pyDataverse](https://pypi.org/project/pyDataverse/)
* - Use [SWORD](https://sword.cottagelabs.com/), either via API endpoints or wrapper library

## Decision Outcome

Chosen option: "- Use SWORD, either via API endpoints or wrapper library", because it is a more high-level solution that can easily be adapted to several targets that support SWORD, and we don't have to rely on several different third-party libraries.

### Positive Consequences

* We'll have a single, consolidated way for deposition on both primary target platforms, as both InvenioRDM and Dataverse support SWORD.

### Negative Consequences

* SWORD doesn't support requirement elicitation from target platforms, so that we may have to use other dependencies for this.
