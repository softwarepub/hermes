<!--
SPDX-FileCopyrightText: 2026 German Aerospace Center (DLR)

SPDX-License-Identifier: CC-BY-SA-4.0
-->

<!-- 
SPDX-FileContributor: Michael Fritzsche
-->

# Harvest plugin

In this tutorial we are going to write a harvest plugin called `pyproject_harvest` that harvests the `pyproject.toml` of Python projects.
For simplicity's sake our plugin will only harvest the name and description of the software, but extending it to harvest more will be easy.

## Setup

To follow this tutorial you'll need...

## Writing the plugin

First we'll start with a new python file that contains the following code:

```{code-block} python
from hermes.commands.harvest.base import HermesHarvestCommand, HermesHarvestPlugin
from hermes.model import SoftwareMetadata
from pydantic import BaseModel


class PyprojectHarvestSettings(BaseModel):
    pass


class PyprojectHarvestPlugin(HermesHarvestPlugin):
    settings_class = PyprojectHarvestSettings

    def __call__(self, command: HermesHarvestCommand) -> SoftwareMetadata:
        data = SoftwareMetadata()

        return data
```

First let's add a setting to our plugin for the location of the `pyproject.toml`.
To do that we have to modify `PyprojectHarvestSettings` like this:

```{code-block} python
:emphasize-lines: 1, 9
from pathlib import Path

from hermes.commands.harvest.base import HermesHarvestCommand, HermesHarvestPlugin
from hermes.model import SoftwareMetadata
from pydantic import BaseModel


class PyprojectHarvestSettings(BaseModel):
    location: Path = Path("pyproject.toml")


class PyprojectHarvestPlugin(HermesHarvestPlugin):
    settings_class = PyprojectHarvestSettings

    def __call__(self, command: HermesHarvestCommand) -> SoftwareMetadata:
        data = SoftwareMetadata()

        return data
```

By doing this we named our setting `location` and let pydantic enforce that its value is a path.
It also has a default value, the `pyproject.toml` in the working directory.

Now we only have to read the file, extract the information needed and write it into the {py:class}`~hermes.model.api.SoftwareMetadata` object.

That can be achieved for example like this:

```{code-block} python
:emphasize-lines: 3, 19-28
from pathlib import Path

import toml
from hermes.commands.harvest.base import HermesHarvestCommand, HermesHarvestPlugin
from hermes.model import SoftwareMetadata
from pydantic import BaseModel


class PyprojectHarvestSettings(BaseModel):
    location: Path = Path("pyproject.toml")


class PyprojectHarvestPlugin(HermesHarvestPlugin):
    settings_class = PyprojectHarvestSettings

    def __call__(self, command: HermesHarvestCommand) -> SoftwareMetadata:
        data = SoftwareMetadata()

        # load data
        pyproject = toml.load(command.settings.pyproject_harvest.location)

        # extract data
        name = pyproject.get("project", {}).get("name", None)
        description = pyproject.get("project", {}).get("description", None)

        # write data
        data["schema:name"] = name
        data["schema:description"] = description

        return data
```

## Configuring HERMES to use your plugin

Now use the build tool of your choice to build the python package containing your plugin, so that you can import it.
Suppose in your project you want to use HERMES your plugin class is available as `pyproject_plugin.PyprojectHarvestPlugin`.

Then in this projects `pyproject.toml`, you have to add `hermes` as a dependency as well as adding `pyproject_plugin:PyprojectHarvestPlugin` as an entrypoint named `pyproject_harvest` for `"hermes.harvest"`.

For HERMES to use our plugin when harvesting, just add `"pyproject_harvest"` to the list of plugins to be used inside of your `hermes.toml` like this:

```{code-block}
[harvest]
sources = [..., "pyproject_harvest", ...]
```
