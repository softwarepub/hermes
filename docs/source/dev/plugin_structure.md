<!--
SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR), Forschungszentrum Jülich GmbH

SPDX-License-Identifier: CC-BY-SA-4.0
-->

<!--
SPDX-FileContributor: Michael Meinel
SPDX-FileContributor: Sophie Kernchen
SPDX-FileContributor: Nitai Heeb
SPDX-FileContributor: Oliver Bertuch
SPDX-FileContributor: Michael Fritzsche
-->

# HERMES plugins


This reference will present the basic structure of additional plugins that are not shipped with `HERMES` but can be made availabe for others through the [HERMES marketplace](../index.md#plugins).

The full code and structure of a harvest plugin is available at [hermes-plugin-git](https://github.com/softwarepub/hermes-plugin-git).
This plugin extracts information from the local git history.
The hermes-plugin-git will help to gather contribution and branch metadata.

```{note}
You should be familiar with HERMES before learning about the structure of plugins.
If you never used HERMES before, you might want to check the tutorial: [Automated Publication with HERMES](./../tutorials/automated-publication-with-ci).

Also all metadata directly handled by HERMES is [JSON-LD](https://json-ld.org/) so you should be familiar with [how it is used by HERMES](./data_model.md) when writing a plugin.
And that HERMES uses the [schema.org](https://schema.org/) (with prefix "schema") and the [CodeMeta](https://codemeta.github.io/) (without prefix) context.
```

## Plugin Architecture

HERMES uses a plugin architecture. Therefore, users are invited to contribute own features.

The structure for every plugin follows the same schema.
Every plugin is a sub class of a sub class of the {py:class}`~hermes.commands.base.HermesPlugin` class.
This class implements one abstract method, {py:meth}`~hermes.commands.base.HermesPlugin.__call__`, which needs to be overwritten by every plugin.
In between the {py:class}`~hermes.commands.base.HermesPlugin` class and the class of a specific plugin there is another class which follows the naming scheme `Hermes{Step}Plugin` where `{Step}` is the workflow step the plugin is associated with.
These base classes may implement additional (abstract) methods that may have to be implemented by the plugins class.

The first positional attribute of the `__call__` method is an object of class `Hermes{Step}Command` (where `{Step}` is the step the plugin is for), which is a sub class of {py:class}`~hermes.commands.base.HermesCommand`, which triggered this plugin to run.
An exception to this are the deposit plugins. Those don't implement the `__call__` method and instead can implement (and have to implement some) other functions.

The plugin class also uses a derivative of {py:class}`~hermes.commands.base.HermesSettings` to add parameters that can be adapted by the configuration file.
{py:class}`~hermes.commands.base.HermesSettings` is the base class for command specific settings.
It uses [pydantic](https://docs.pydantic.dev/latest/) [settings](https://docs.pydantic.dev/latest/api/pydantic_settings/) to specify and validate the parameters.
The user can either set the parameters in the `hermes.toml` or overwrite them in the command line.
To overwrite a parameter from command line, use the `-O` command line option followed by the dotted parameter name and the value.
E.g., you can set your authentication token for InvenioRDM by adding the following options to your call to `hermes deposit`:
```shell
hermes deposit -O invenio_rdm.auth_token YourSecretAuthToken
```

## Implement plugin class
To write a new plugin, it is important to follow the given structure.
This means your plugins source code has a pydantic class with Settings and the plugin class which inherits from the plugins steps base class.
But because the details of the plugin structure vary depending on what step the plugin is for, we will discuss the structures separatly.

### Harvest plugin
The class structure of a harvest plugin should look like this:

```{code-block} python
from hermes.commands.harvest.base import HermesHarvestCommand, HermesHarvestPlugin
from hermes.model import SoftwareMetadata
from pydantic import BaseModel


class YourHarvestSettings(BaseModel):
    # TODO: add your settings
    pass


class YourHarvestPlugin(HermesHarvestPlugin):
    settings_class = YourHarvestSettings

    def __call__(self, command: HermesHarvestCommand) -> SoftwareMetadata:
        data = SoftwareMetadata()

        # TODO: collect the metadata and write it into data

        return data
```

The {py:meth}`~hermes.commands.harvest.base.HermesHarvestPlugin.__call__` method of harvest plugins needs to return a {py:class}`~hermes.model.api.SoftwareMetadata` object containing the harvested metadata.
For more information on how to use this object see [here](./data_model.md).

```{attention}
Please use for **all** load operations the {py:meth}`~hermes.commands.harvest.base.HermesHarvestPlugin.load` function of {py:class}`hermes.commands.harvest.base.HermesHarvestPlugin` using `self.load(...)` inside your plugin object.

This is necessary for collection of provenance information.
```

### Process plugin
The class structure of a process plugin should look like this:

```{code-block} python
from hermes.commands.process.base import HermesProcessCommand, HermesProcessPlugin, ObjectStrategies
from hermes.model.merge.action import MergeAction
from pydantic import BaseModel


class YourProcessSettings(BaseModel):
    # TODO: add your settings
    pass


class YourProcessPlugin(HermesProcessPlugin):
    settings_class = YourProcessSettings

    def __call__(self, command: HermesProcessCommand) -> ObjectStrategies:
        strategies = {}

        # TODO: define the merge strategies that will be used by HERMES

        return strategies
```

The {py:meth}`~hermes.commands.process.base.HermesProcessPlugin.__call__` method of process plugins needs to return `ObjectStrategies`, a dictionary mapping strings and/ or `None` to dictionaries mapping strings or `None` to {py:class}`~hermes.model.merge.action.MergeAction`.
Alone this data structure, `ObjectStrategies` isn't enough to understand how this object is supposed to represent the merge strategies.
The following example will illustrate the sematics of each layer within the dictionary.

If `strategies` looked like this (where {py:class}`~hermes.model.merge.action.Reject` is imported from {py:mod}`hermes.model.merge.action`)
```{code-block} python
strategies = {
    full_type_iri: {
        full_property_iri: Reject(),
        ...
    },
    ...
}
```

HERMES would use the {py:class}`~hermes.model.merge.action.Reject` strategy for merging values of the key `full_property_iri` in objects of type `full_type_iri`. (A key in strategies being `None` instead of a string indicates to HERMES that its value is to be used as a default [i.e. if no more specific entry exists].)

HERMES will prioritize strategies from other plugins depending on the order of the plugins in the `hermes.toml`. Generally the hierarchy is as follows (first most important):
1. strategies with `full_property_iri` and `full_type_iri` not `None`.
2. strategies with `full_property_iri` not `None` and `full_type_iri` `None`.
3. strategies with `full_property_iri` `None` and `full_type_iri` not `None`.
4. strategies with `full_property_iri` and `full_type_iri` `None`.

But if multiple plugins specify overlapping strategies on the same hierarchy level the strategy of the plugin listed first in the `hermes.toml` is used.

### Curate plugin
The class structure of a curate plugin should look like this:

```{code-block} python
from hermes.commands.curate.base import HermesCurateCommand, HermesCuratePlugin
from hermes.model import SoftwareMetadata
from pydantic import BaseModel


class YourCurateSettings(BaseModel):
    # TODO: add your settings
    pass


class YourCuratePlugin(HermesCuratePlugin):
    settings_class = YourCurateSettings

    def __call__(self, command: HermesCurateCommand, metadata: SoftwareMetadata) -> SoftwareMetadata:
        data = SoftwareMetadata()

        # TODO: curate the metadata and write it into data

        return data
```

The {py:meth}`~hermes.commands.curate.base.HermesCuratePlugin.__call__` method of curate plugins needs to return a {py:class}`~hermes.model.api.SoftwareMetadata` object containing the curated metadata.
For more information on how to use this object see [here](./data_model.md).
The returned object may be the object `metadata` passed to `__call__`.

### Deposit plugin
The class structure of a deposit plugin should look like this:

```{code-block} python
from hermes.commands.deposit.base import HermesDepositPlugin
from hermes.model import SoftwareMetadata
from pydantic import BaseModel


class YourDepositSettings(BaseModel):
    # TODO: add your settings
    pass


class YourDepositPlugin(HermesDepositPlugin):
    settings_class = YourDepositSettings

    def prepare(self) -> None:
        """ not neccessary """
        pass

    def map_metadata(self) -> dict:
        """ neccessary """
        mapped_metadata = {}
        # TODO: implement
        return mapped_metadata

    def is_initial_publication(self) -> bool:
        """ neccessary """
        is_initial = True
        # TODO: implement logic
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
        # TODO: implement
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

A deposit plugin doesn't implement a `__call__` method like plugins for other steps.
Instead it can (and in some cases has to) implement methods, which will be called in a predefined order.
For information on the order and the purpose of a single function see {py:class}`~hermes.commands.deposit.base.HermesDepositPlugin`.

The plugin still has access to the command (via `self.command`) and the metadata for the software (via `self.metadata`).

### Postprocess plugin
The class structure of a postprocess plugin should look like this:

```{code-block} python
from hermes.commands.postprocess.base import HermesPostprocessCommand, HermesPostprocessPlugin
from hermes.model import SoftwareMetadata
from pydantic import BaseModel


class YourPostprocessSettings(BaseModel):
    # TODO: add your settings
    pass


class YourPostprocessPlugin(HermesPostprocessPlugin):
    settings_class = YourPostprocessSettings

    def __call__(self, command: HermesPostprocessCommand) -> None:
        # TODO: implement logic
        pass
```

```{attention}
Please use for **all** load operations the {py:meth}`~hermes.commands.postprocess.base.HermesPostprocessPlugin.load` function of {py:class}`hermes.commands.postprocess.base.HermesPostprocessPlugin` using `self.load(...)` inside your plugin object.
And {py:meth}`~hermes.commands.postprocess.base.HermesPostprocessPlugin.write` for **all** write operations.
As well as {py:meth}`~hermes.commands.postprocess.base.HermesPostprocessPlugin.get_deposit_result` for loading the result of the deposit plugin.

This is necessary for collection of provenance information.
```

## Implement and use plugin specific settings
The class set in the `settings_class` attribute of your plugin class is your plugins settings class.
All attributes in it can be set in the `hermes.toml` of your project or passed via the command line.
If not set, they will be set to the (in the class) specified default value.
Pydantic will also validate the attributes value against the type hint of the attribute.

The settings of your plugin can be accessed via `command.settings.{plugin_name}.{attribute_name}` where `command` is the `Hermes{Step}Command` object usually passed via the `__call__` method.
And setting it in the `hermes.toml` works like this:
```shell
[{plugin_step}.{plugin_name}]
{attribute_name} = value
```

## Configure HERMES to use your plugin

To integrate your plugin, you have to register it as a plugin in the `pyproject.toml` by regestering it as an entry point.
To learn more about the `pyproject.toml` check out [this guide](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) or refer to [PEP621](https://peps.python.org/pep-0621/).
We will just look at the important places for this plugin.
There are two ways to integrate this plugin.
First we will show how to use the plugin environment as the running base with HERMES as a dependency.
Then we say how to integrate this plugin in HERMES itself.

### Include HERMES as Dependency
This is probably the more common way, where you can see HERMES as a framework.
The idea is that your project is the main part. You create the `pyproject.toml` as usual.
In the dependencies block you need to include `hermes`. Then you just have to declare your plugin.
The HERMES software will look for installed plugins and use them.
In the code below you can see the parts of the `pyproject.toml` that are important.
```{code-block}
...
[tool.poetry.dependencies]
python = "^3.10"
hermes = "^0.8.0"
...
...
[tool.poetry.plugins."hermes.{plugin_step}"]
{plugin_name} = "{plugin_package}.{plugin_module}:{plugin_class}"
...
```
As you can see the plugin class from `plugin_package` is declared as `plugin_name` for the `hermes.{plugin_step}` entrypoint.
To use the plugin you have to adapt the settings for `plugin_step` in the `hermes.toml`.
We will discuss the exact step after showing the other `pyproject.toml` configuration.
```{note}
You have to run poetry install to add and install all entrypoints declared in the pyproject.toml.
```

### Include Plugin into HERMES
This variant is used to contribute to the HERMES community or adapt the HERMES workflow for own purposes.
If you want to contribute, see the [Contribution Guidelines](https://docs.software-metadata.pub/en/latest/dev/contribute.html).
After cloning the HERMES workflow repository you can adapt the pyproject.toml.
In the code below you see the parts with the important lines.
```{code-block}
...
[dependencies]
...
pydantic-settings = "^2.1.0"
{plugin_package} = { {plugin_name} = "{link_to_your_repo}", branch = "main" }
...
...
[project.entry-points."hermes.{plugin_step}"]
{plugin_name} = "{plugin_package}.{plugin_module}:{plugin_class}"
...
```
In the dependencies you have to install your plugin. If your Plugin is pip installable than you can just give the name and the version.
If your plugin is in a buildable git repository, you can install it with the given expression. 
Note that this differs with the accessibility and your wishes, check available [dependency specifiers](https://packaging.python.org/en/latest/specifications/dependency-specifiers/#dependency-specifiers).

The second thing to adapt is to declare the access point for the plugin.
You can do that with `{plugin_name} = "{plugin_package}.{plugin_module}:{plugin_class}"`.
This expression makes the `plugin_class` from the `plugin_package` package, a `hermes.{plugin_step}` plugin named `plugin_name`.
So you need to configure this line with your plugin properties.

Now you just need to add the plugin to the `hermes.toml` and reinstall the package.

### Configure hermes.toml
To use the plugin, you have to activate it in the `hermes.toml`.
The settings for the plugins are also set there.

Here are some examples how to integrate your plugin...

#### ... for a harvest plugin.
```{code-block}
...
[harvest]
sources = [ ..., "{plugin_name}", ... ] # ordered priority (first one is most important)
...
```
#### ... for a process plugin.
```{code-block}
...
[process]
plugins = [ ..., "{plugin_name}", ... ] # ordered priority (first one is most important)
...
```
#### ... for a curate plugin.
```{code-block}
...
[curate]
plugin = "{plugin_name}"
...
```
#### ... for a deposit plugin.
```{code-block}
...
[deposit]
target = "{plugin_name}"
...
```
#### ... for a postprocess plugin.
```{code-block}
...
[postprocess]
run = [ ..., "{plugin_name}", ... ]
...

```

```{admonition} Congratulations!
You can now write plugins for HERMES.
```

Consider publishing it to the [HERMES plugin marketplace](../index.md#plugins) for others to use following this guide. TODO: add link

If you have any questions, wishes or requests, feel free to contact us.
