<!--
SPDX-FileCopyrightText: 2026 German Aerospace Center (DLR)

SPDX-License-Identifier: CC-BY-SA-4.0
-->

<!-- 
SPDX-FileContributor: Michael Fritzsche
-->

# Deposit plugin

In this tutorial we are going to write a deposit plugin called `file_deposit` that deposits the metadata into a configured file.
For simplicity's sake our plugin will not publish to any external source, but extending it to do so will be easy.

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
from hermes.commands.deposit.base import BaseDepositPlugin
from hermes.model import SoftwareMetadata
from pydantic import BaseModel


class FileDepositSettings(BaseModel):
    pass


class FileDepositPlugin(BaseDepositPlugin):
    settings_class = YourDepositSettings

    def prepare(self) -> None:
        """ not neccessary """
        pass

    def map_metadata(self) -> dict:
        """ neccessary """
        mapped_metadata = {}

        return mapped_metadata

    def is_initial_publication(self) -> bool:
        """ neccessary """
        is_initial = True

        return is_initial

    def create_initial_version(self) -> None:
        """ not necessary if is_initial_publication can not return True """
        pass

    def create_new_version(self) -> None:
        """ not necessary if is_initial_publication can not return False """
        pass

    def update_metadata(self) -> dict:
        """ necessary """
        mapped_metadata = {}

        return mapped_metadata

    def delete_artifacts(self) -> None:
        """ not necessary """
        pass

    def upload_artifacts(self) -> None:
        """ not necessary """
        pass

    def publish(self) -> None:
        """ not necessary """
        pass
```

First let's add a setting to our plugin for the location where the data should be deposited to.
To do that we have to modify `FileDepositSettings` like this:

```{code-block} python
:emphasize-lines: 1, 9
from pathlib import Path

from hermes.commands.deposit.base import BaseDepositPlugin
from hermes.model import SoftwareMetadata
from pydantic import BaseModel


class FileDepositSettings(BaseModel):
    file: Path = Path("deposit_results.json")


class FileDepositPlugin(BaseDepositPlugin):
    settings_class = YourDepositSettings
...
```

By doing this we named our setting `file` and let pydantic enforce that its value is a path.
It also has a default value, the `deposit_results.json` in the working directory.

Now we only have to implement `map_metadata()`, `update_metadata()` as well as `publish()`.

That can be achieved for example like this:

```{code-block} python
:emphasize-lines: 21, 39, 51-52
from pathlib import Path

from hermes.commands.deposit.base import BaseDepositPlugin
from hermes.model import SoftwareMetadata
from pydantic import BaseModel


class FileDepositSettings(BaseModel):
    file: Path = Path("deposit_results.json")


class FileDepositPlugin(BaseDepositPlugin):
    settings_class = YourDepositSettings

    def prepare(self) -> None:
        """ not neccessary """
        pass

    def map_metadata(self) -> dict:
        """ neccessary """
        return self.metadata.compact()

    def is_initial_publication(self) -> bool:
        """ neccessary """
        is_initial = True

        return is_initial

    def create_initial_version(self) -> None:
        """ not necessary if is_initial_publication can not return True """
        pass

    def create_new_version(self) -> None:
        """ not necessary if is_initial_publication can not return False """
        pass

    def update_metadata(self) -> dict:
        """ necessary """
        return self.metadata.compact()

    def delete_artifacts(self) -> None:
        """ not necessary """
        pass

    def upload_artifacts(self) -> None:
        """ not necessary """
        pass

    def publish(self) -> None:
        """ not necessary """
        with open(self.command.settings.file_deposit.file) as file:
            file.write(str(self.metadata.compact()))
```

## Configuring HERMES to use your plugin

Now use the build tool of your choice to build the python package containing your plugin, so that you can import it.
Suppose in your project you want to use HERMES your plugin class is available as `file_deposit_plugin.FileDepositPlugin`.

Then in this projects `pyproject.toml`, you have to add `hermes` as a dependency as well as adding `file_deposit_plugin:FileDepositPlugin` as an entrypoint named `file_deposit` for `"hermes.deposit"`.

For HERMES to use our plugin when harvesting, just add `"file_deposit"` as the plugin to be used inside of your `hermes.toml` like this:

```{code-block}
[deposit]
target = "file_deposit"
```
