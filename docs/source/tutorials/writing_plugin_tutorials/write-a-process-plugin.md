<!--
SPDX-FileCopyrightText: 2026 German Aerospace Center (DLR)

SPDX-License-Identifier: CC-BY-SA-4.0
-->

<!-- 
SPDX-FileContributor: Michael Fritzsche
-->

# Process plugin

In this tutorial we are going to write a process plugin called `author_merge` that supplies HERMES with a new strategy for the merge so that no (supposedly identical) authors are only merged druing processing if their id is the same and optionally if their email is the same.
For simplicity's sake our plugin will only provide oly this strategy, but extending it to supply more more will be easy.

## Setup

To follow this tutorial you'll need...

## Writing the plugin

First we'll start with a new python file that contains the following code:

```{code-block} python
from hermes.commands.process.base import HermesProcessCommand, HermesProcessPlugin, ObjectStrategies
from hermes.model.merge.action import MergeAction
from pydantic import BaseModel


class AuthorProcessSettings(BaseModel):
    pass


class AuthorProcessPlugin(HermesProcessPlugin):
    settings_class = AuthorProcessSettings

    def __call__(self, command: HermesProcessCommand) -> ObjectStrategies:
        strategies = {}

        return strategies
```

First let's add a setting to our plugin that lets the user configure whether it should be merged on email eqality.
To do that we have to modify `AuthorProcessSettings` like this:

```{code-block} python
:emphasize-lines: 7
from hermes.commands.process.base import HermesProcessCommand, HermesProcessPlugin, ObjectStrategies
from hermes.model.merge.action import MergeAction
from pydantic import BaseModel


class AuthorProcessSettings(BaseModel):
    merge_on_email: bool = True


class AuthorProcessPlugin(HermesProcessPlugin):
    settings_class = AuthorProcessSettings

    def __call__(self, command: HermesProcessCommand) -> ObjectStrategies:
        strategies = {}

        return strategies
```

By doing this we named our setting `merge_on_email` and let pydantic enforce that its value is a boolean.
It also has a default value, `True`.

Now we only have to create our merge strategy.

That can be achieved for example like this:

```{code-block} python
:emphasize-lines: 1, 5-7, 11-35, 45-55
from typing import Union

from hermes.commands.process.base import HermesProcessCommand, HermesProcessPlugin, ObjectStrategies
from hermes.model.merge.action import MergeAction
from hermes.model.merge.container import ld_merge_dict, ld_merge_list
from hermes.model.types import ld_dict, ld_list
from hermes.model.types.ld_container import BASIC_TYPE, TIME_TYPE
from pydantic import BaseModel


class AuthorMerge(MergeAction):
    merge_on_email: bool = True

    def merge(
        self,
        target: ld_merge_dict,
        key: list[Union[str, int]],
        value: Union[ld_merge_list, str],
        update: Union[BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]
    ) -> ld_merge_list:
        if not isinstance(update, (list, ld_list)):
            update = [update]

        for update_item in update:
            for index, item in enumerate(value):
                if isinstance(item, ld_dict) and isinstance(update_item, ld_dict):
                    same_id = item["@id"] == update_item["@id"] if "@id" in item and "@id" in update_item else False
                    same_email = any(email_update in item.get("schema:email", []) for email_update in update_item.get("schema:email", []))
                    if same_id or (self.merge_on_email and same_email):
                        print("hey")
                        item.update(update_item)
                        break
            else:
                value.append(update_item)
        return value


class AuthorProcessSettings(BaseModel):
    merge_on_email: bool = True


class AuthorProcessPlugin(HermesProcessPlugin):
    settings_class = AuthorProcessSettings

    def __call__(self, command: HermesProcessCommand) -> ObjectStrategies:
        AuthorMerge.merge_on_email = command.settings.testi.merge_on_email
        merger = AuthorMerge()
        strategies = {
            "http://schema.org/SoftwareSourceCode": {
                "http://schema.org/author": merger
            },
            "http://schema.org/SoftwareApplication": {
                "http://schema.org/author": merger
            }
        }

        return strategies
```

## Configuring HERMES to use your plugin

Now use the build tool of your choice to build the python package containing your plugin, so that you can import it.
Suppose in your project you want to use HERMES your plugin class is available as `author_merger_plugin.AuthorProcessPlugin`.

Then in this projects `pyproject.toml`, you have to add `hermes` as a dependency as well as adding `author_merger_plugin:AuthorProcessPlugin` as an entrypoint named `author_merge` for `"hermes.process"`.

For HERMES to use our plugin when processing, just add `"author_merge"` to the list of plugins to be used inside of your `hermes.toml` like this:

```{code-block}
[process]
plugins = [..., "author_merge", ...]
```

For our plugin you should use it with e.g. the basic merger provided by HERMES, because we only supplied a strategy for merging authors.
To do this just add `"codemeta"` somewhere **after** `"author_merge"`.
