<!--
SPDX-FileCopyrightText: 2026 German Aerospace Center (DLR)

SPDX-License-Identifier: CC-BY-SA-4.0
-->

<!-- 
SPDX-FileContributor: Michael Fritzsche
-->

# Curate plugin

In this tutorial we are going to write a curate plugin called `censor_author_emails` that deletes all author email in the curate step.
For simplicity's sake our plugin will only do this, but extending it to do more will be easy.

## Setup

To follow this tutorial you'll need to have HERMES with version >=0.10 installed.
You can install it like this:

First, install Python 3.11 (or later).

Additionally, you need to [install `poetry >= 2.0.0`](https://python-poetry.org/docs/#installation), either globally, or
within an environment of your choice. As a project, we chose `poetry` to manage our dependencies, builds, and deposits
as a state of the art solution within the Python ecosystem.

In case you still want to install on your machine, you can (for example) use `pip`:

```shell
pip install hermes
```

## Writing the plugin

First we'll start with a new python file that contains the following code:

```{code-block} python
from hermes.commands.curate.base import HermesCurateCommand, HermesCuratePlugin
from hermes.model import SoftwareMetadata
from pydantic import BaseModel


class RedactCurateSettings(BaseModel):
    pass


class RedactCuratePlugin(HermesCuratePlugin):
    settings_class = YourCurateSettings

    def __call__(self, command: HermesCurateCommand, metadata: SoftwareMetadata) -> SoftwareMetadata:
        data = SoftwareMetadata()

        return data
```

First let's add a setting to our plugin that specifies with what the emails should be replaced.
To do that we have to modify `RedactCurateSettings` like this:

```{code-block} python
:emphasize-lines: 7
from hermes.commands.curate.base import HermesCurateCommand, HermesCuratePlugin
from hermes.model import SoftwareMetadata
from pydantic import BaseModel


class RedactCurateSettings(BaseModel):
    redact_with: str = "_REDACTED_"


class RedactCuratePlugin(HermesCuratePlugin):
    settings_class = YourCurateSettings

    def __call__(self, command: HermesCurateCommand, metadata: SoftwareMetadata) -> SoftwareMetadata:
        data = SoftwareMetadata()

        return data
```

By doing this we named our setting `redact_with` and let pydantic enforce that its value is a string.
It also has a default value, `"_REDACTED_"`.

Now we only have to replace all author emails.

That can be achieved for example like this:

```{code-block} python
:emphasize-lines: 13-17
from hermes.commands.curate.base import HermesCurateCommand, HermesCuratePlugin
from hermes.model import SoftwareMetadata
from pydantic import BaseModel


class RedactCurateSettings(BaseModel):
    redact_with: str = "_REDACTED_"


class RedactCuratePlugin(HermesCuratePlugin):
    settings_class = YourCurateSettings

    def __call__(self, command: HermesCurateCommand, metadata: SoftwareMetadata) -> SoftwareMetadata:
        redact_with = command.settings.censor_author_emails.redact_with
        for author in metadata.get("schema:author", []):
            if "schema:email" in author:
                author["schema:email] = len(author["schema:email"]) * [redact_with]

        return metadata
```

## Configuring HERMES to use your plugin

Now use the build tool of your choice to build the python package containing your plugin, so that you can import it.
Suppose in your project you want to use HERMES your plugin class is available as `redact_plugin.RedactProcessPlugin`.

Then in this projects `pyproject.toml`, you have to add `hermes` as a dependency as well as adding `redact_plugin:RedactProcessPlugin` as an entrypoint named `censor_author_emails` for `"hermes.harvest"`.

For HERMES to use our plugin when harvesting, just add `"censor_author_emails"` as the plugin to be used inside of your `hermes.toml` like this:

```{code-block}
[curate]
plugin = "censor_author_emails"
```
