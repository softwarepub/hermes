<!--
SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR), Forschungszentrum Jülich, Helmholtz-Zentrum Dresden-Rossendorf

SPDX-License-Identifier: CC-BY-SA-4.0
-->

# Support curation

* Status: proposed
* Date: 2022-03-16

## Context and Problem Statement

Software publication (and their metadata) may have to be curated, depending on curation workflows at different institutions. We support this by providing a way to produce a normalized metadata set for curation, without drafting or publishing the actual deposit.

## Decision Drivers

* Curation policies at institutions
* Policies can address different stages of the software development and publishing workflow

## Considered Options

* Potentially multiple runs
* Break until curation is successful

## Decision Outcome

Chosen option: "Potentially multiple runs", because this is the option that supports our project targets

## Pros and Cons of the Options

### Potentially multiple runs

The workflow is run multiply for different steps depending on requirements (produce curatable metadata set, curate and sign off, draft, publish).
This needs to be supported even for curation in target repositories in case of updated drafts. This option includes the scenario where metadata has been curated before the first workflow run and can be published straightaway.

* Good, because Covers different curation scenarios
* Bad, because Adds complexity / multiple runs

### Break until curation is successful

Breaks workflow until curation has been successful, continues in the next run

* Good, because Usable for web services
* Bad, because Not usable for CI services

## Links

* https://github.com/hermes-hmc/workflow/issues/1
