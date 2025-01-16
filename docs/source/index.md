<!--
SPDX-FileCopyrightText: 2022 Forschungszentrum Jülich, German Aerospace Center (DLR)

SPDX-License-Identifier: CC-BY-SA-4.0
-->

<!--
SPDX-FileContributor: Oliver Bertuch
SPDX-FileContributor: Stephan Druskat
SPDX-FileContributor: Michael Meinel
SPDX-FileContributor: David Pape
-->

![](_static/img/header.png)

# Overview

```{note}
This is work in progress.
```

Research software must be formally published to satisfy the 
[*FAIR Principles for Research Software*](https://doi.org/10.15497/RDA00068),
improve software sustainability and 
enable software citation. 
Publication repositories make software publication possible 
and provide PIDs for software versions.
But software publication is often a tedious, manual process. 

HERMES workflows automate the publication of research software with rich metadata
using an open source tool, the `hermes` Python package. 

HERMES follows a *push-based* model and runs in 
continuous integration (CI) systems.
This way, it helps overcome limitations of platform-centric
pull-based services and grants its users full control over the
publication process and the metadata compiled for the publication. 

Rich descriptive metadata is the key element to useful software publications. 
We harvest existing metadata from source
code repos and connected platforms, then process, collate and present them for curation, thus preparing software for
automatic submission to publication repositories.

![](_static/img/workflow-overview.svg)

## Plugins

```{plugin-markup} plugins.json plugins-schema.json
```

Hermes is built to be extensible for your needs.
This is a list of available plugins for the different steps in the Hermes workflow:

```{datatemplate:json} plugins.json
:template: plugins.md
```

## Documentation

<!--
```{toctree}
 cli
```
-->

```{toctree}
:glob:
:maxdepth: 1
:caption: Tutorials
tutorials/*
```

```{toctree}
:maxdepth: 1
:caption: Developers
dev/contribute
Tutorial: Get started w/ development <dev/start>
dev/data_model
adr/index
api/index
```

```{toctree}
:maxdepth: 1
:caption: HERMES project
project/index
project/events
project/presentations
```

```{toctree}
:hidden:
:caption: Related
Concept Paper <https://arxiv.org/abs/2201.09015>
```

## Get in touch!

HERMES is part of a global and interdisciplinary effort to improve the state of the art in 
research software engineering, maintenance and scholarly communications around research software. We
appreciate any feedback you may have.

**How to give feedback**

Either [create an issue](https://github.com/softwarepub/hermes/issues/new/choose) in the main `hermes` repository or 
[send us an email](mailto:team@software-metadata.pub?subject=HERMES%20Workflows).

## Acknowledgements

HERMES was developed with initial funding from the [Helmholtz Metadata Collaboration](https://helmholtz-metadaten.de) ([Helmholtz INF](https://www.helmholtz.de/en/about-us/structure-and-governance/initiating-and-networking) grantZT-I-PF-3-006).

```{include} ../../LICENSE.md
```

## Indices and tables

* [](genindex)
* [](modindex)
* [](search)
