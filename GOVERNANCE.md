<!--
SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR)
SPDX-FileContributor: Stephan Druskat
SPDX-FileContributor: David Pape

SPDX-License-Identifier: CC-BY-SA-4.0
-->

# Governance

This document describes the governance over the repositories listed below as
[HERMES Project Repositories](#hermes-project-repositories) and
[Software CaRD Project Repositories](#software-card-project-repositories).

DLR, HZDR, FZJ, and GFZ share the governance over these repositories and their maintenance.
Maintainers can be contacted via their [mailing list](mailto:team@software-metadata.pub).

The software provided in these repositories is no longer actively developed due to the projects
having reached their conclusions.
Security patches and bug fixes will be provided on a best effort basis but are not guaranteed.
Potential contributors are encouraged to provide bug fixes via pull requests to the relevant
repositories, which are then reviewed and integrated on a best effort basis.

Any of the named institutions may resume the development of these projects.
In this case they should adopt a new governance model.
The old governance model is provided for reference at the bottom of this document.
New contributors and developers may contact the maintainers to be introduced to the projects on a
best effort basis.
The maintenance over any of the projects may be transferred.

## HERMES Project Repositories

The following repositories were developed jointly by DLR, HZDR, and FZJ, within the HERMES project:

- <https://github.com/softwarepub/hermes>
- <https://github.com/softwarepub/ci-templates>
- <https://github.com/softwarepub/showcase>
- <https://github.com/softwarepub/schema.software-metadata.pub>
- <https://github.com/softwarepub/github-action>
- <https://github.com/softwarepub/concept-paper>

The [HERMES project (`ZT-I-PF-3-006`)](https://helmholtz-metadaten.de/inf-projects/hermes) was
funded by the _Initiative and Networking Fund_ of the Helmholtz Association in the framework of the
Helmholtz Metadata Collaboration's 2020 project call.

## Software CaRD Project Repositories

The following repositories were developed jointly by DLR, HZDR, FZJ, and GFZ, within the
Software CaRD project:

- <https://github.com/softwarepub/software-card>
- <https://github.com/softwarepub/hermes-plugin-software-card>
- <https://github.com/softwarepub/software-card-policies>
- <https://codebase.helmholtz.cloud/research-software-directory/hermes-plugin-rsd/>

The [Software CaRD project (`ZT-I-PF-3-080`)](https://helmholtz-metadaten.de/inf-projects/softwarecard)
was funded by the _Initiative and Networking Fund_ of the Helmholtz Association in the framework of
the Helmholtz Metadata Collaboration's 2023 project call.

---

## Old Governance

The HERMES project employs a lightweight governance model.

All decisions are made by the [HERMES Steering Group](#hermes-steering-group) 
together with the maintainer(s) of the repositories affected by the decision.

Decisions that adhere to a single [repository in the scope of the HERMES project](#hermes-project-repositories)
are made by *lazy consensus*: 

1. The maintainer of the repository makes a decision and notifies the HERMES Steering Group
(using `@softwarepub/hermes-steering-group` mention).
2. If no members of the Steering Group veto the decision within the decision period of one week (168 hours),
the decision becomes effective and can be acted upon. 
The maintainer and any member of the Steering Group can ask for a longer decision period, 
which must be granted. 
During this period, the steering committee should meet to discuss the decision.
3. If one or more members of the Steering Group veto the decision, 
the decision is discussed until consensus is reached.

Decisions that adhere to more than one [repository in the scope of the HERMES project](#hermes-project-repositories)
must be based on full consensus within the Steering Group. 


### HERMES project repositories

The following are the repositories that are governed by the Steering Group. 

- <https://github.com/softwarepub/hermes> (Maintainer: Stephan Druskat)
- <https://github.com/softwarepub/ci-templates> (Maintainer: Oliver Bertuch)
- <https://github.com/softwarepub/hermes-plugin-git> (Maintainer: Sophie Kernchen)
- <https://github.com/softwarepub/hermes-plugin-python> (Maintainer: Michael Meinel)
- <https://github.com/softwarepub/showcase> (Maintainer: Oliver Bertuch)
- <https://github.com/softwarepub/schema.software-metadata.pub> (Maintainer: Michael Meinel)
- <https://github.com/softwarepub/github-action> (Maintainer: Oliver Bertuch)
- <https://github.com/softwarepub/concept-paper> (Maintainer: Stephan Druskat)

New repositories may be added to, 
and existing repositories may be removed from, 
the project by the [Steering Group](#hermes-steering-group)
by updating the above list.
Any update needs lazy consensus [as defined above](#governance) from all members of the Steering Group.

### HERMES Steering Group

The HERMES Steering Group has three members, 
each of whom represents one of the three Helmholtz centers 
who were funded under the original Helmholtz Metadata Collaboration project (ZT-I-PF-3-006), i.e.,
German Aerospace Center (DLR), 
Helmholtz-Zentrum Dresden-Rossendorf (HZDR), 
Forschungszentrum Jülich (FZJ).

Currently, the Steering Group consists of:

- Stephan Druskat (DLR), stephan.druskat@dlr.de
- David Pape (HZDR), d.pape@hzdr.de
- Nitai Heeb (FZJ), n.heeb@fz-juelich.de


Whenever a member of the Steering Group wants to step down,
they are asked to nominate a successor.
If no successor is named,
the two remaining members seek a successor affiliated with the Helmholtz center of the leaving member.
New members of the Steering Group join if neither of the other two members disagrees with the decision to join. 

### HERMES repository maintainers

Each [repository in the scope of the HERMES project](#hermes-project-repositories) should have one maintainer at all times.
The Steering Group appoints the maintainer for this repository in agreement with the appointed person.
Whenever a maintainer wants to step down,
they are asked to nominate a successor.
If no successor is named,
the Steering Group seeks a successor.
One member of the Steering Group steps in as interim maintainer until a successor is found.

Authorship is defined by the [steering group](#hermes-steering-group) and declared in
[`CITATION.cff`](https://github.com/softwarepub/hermes/blob/main/CITATION.cff).
