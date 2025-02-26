<!--
SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR), Forschungszentrum Jülich

SPDX-License-Identifier: CC-BY-SA-4.0
-->

<!--
SPDX-FileContributor: Stephan Druskat
SPDX-FileContributor: Michael Meinel
SPDX-FileContributor: Oliver Bertuch
-->

![HERMES Key Visual](https://docs.software-metadata.pub/en/latest/_static/img/header.png)

[![Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)
![PyPI - Version](https://img.shields.io/pypi/v/hermes)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/hermes)

# hermes

Implementation of the HERMES workflow to automatize software publication with rich metadata.
For more extensive documentation, see our [HERMES workflow documentation](https://docs.software-metadata.pub/en/latest).

(For more information about the HERMES [HMC](https://helmholtz-metadata.de) *project*, see the [HERMES project website](https://software-metadata.pub).)

![HERMES Workflow Visualization](https://docs.software-metadata.pub/en/latest/_static/img/workflow-horizontal.png)

## Installation

`hermes`' primary use case is to [use it in a continuous integration environment](https://docs.software-metadata.pub/en/latest/tutorials/automated-publication-with-ci.html).

In case you still want to install on your machine, you can (for example) use `pip`:

```shell
pip install hermes
```

**Note: you must have Python 3.10 or newer installed.**
Older installations of Python will receive a non-related package because of PyPI limitations!

### Development Snapshot

To install the most recent version that has not been released yet, please install from our sources on GitHub:

```commandline
pip install git+https://github.com/hermes-hmc/hermes.git
```

## Usage

The `hermes` application provides the entry point for the HERMES workflow.
After installation, you can run it from your command line environment:

```shell
hermes --help
hermes harvest
```

You can also call the `hermes` package as a Python module:

```shell
python -m hermes --help
python -m hermes harvest
```

## Contributions, Extension and Development

We welcome external contributions! Please follow our [contribution guidelines](CONTRIBUTING.md).

HERMES was designed with extensibility in mind. Our [development guide](https://docs.software-metadata.pub/en/latest/dev/start.html)
contains in-depth information on how to get ready and start coding.

## Acknowledgements

This project (ZT-I-PF-3-006) was funded by the *Initiative and Networking Fund*
of the [Helmholtz Association](https://www.helmholtz.de/en/about-us/structure-and-governance/initiating-and-networking)
in the framework of the [Helmholtz Metadata Collaboration](https://helmholtz-metadaten.de)'s
[2020 project call](https://helmholtz-metadaten.de/en/projects/hmc-projects-2020).

## License and Citation

Please see [`LICENSE.md`](LICENSE.md) for legal information.
We provide a [`CITATION.cff`](CITATION.cff) containing all metadata for citation, which is also easy to
use via the widget on the right-hand side.
