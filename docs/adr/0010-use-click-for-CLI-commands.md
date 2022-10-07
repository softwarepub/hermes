<!--
SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR), Forschungszentrum Jülich, Helmholtz-Zentrum Dresden-Rossendorf

SPDX-License-Identifier: CC-BY-SA-4.0
-->

# Use click for CLI commands

* Status: accepted
* Deciders: led02, sdruskat
* Date: 2022-03-24

## Context and Problem Statement

We have the choice between pure Python argparse implementation of CLI commands, setuptools with the command package and third-party libraries, such as click or typer.

## Decision Drivers

* Be able to use features such as entrypoints
* Leverage advanced features such as help creation, subcommands and command classes
* Small dependency footprint

## Considered Options

* argparse
* click
* typer

## Decision Outcome

Chosen option: "click", because provides advanced features without adding too many dependencies

### Positive Consequences

* Lots of docs available
* Has advanced features

### Negative Consequences

* Devs need to get acquainted with the library

## Pros and Cons of the Options

### argparse

Pure Python argparse implementation

* Good, because No further dependencies needed
* Bad, because Verbose
* Bad, because Boilerplate needed

### click

Use the click library to implement CLI

* Good, because Provides sought-after features
* Good, because Colourful output
* Good, because Go-to solution for Python CLIs
* Bad, because Adds dependencies (itself and colorama)

### typer

Wraps click to make it even simpler to write CLIs

* Good, because Adds shell auto-completion
* Bad, because Unclear what it adds over click apart form auto-completion
* Bad, because Adds yet another dependency
