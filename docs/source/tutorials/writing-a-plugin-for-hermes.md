<!--
SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR), Forschungszentrum Jülich GmbH

SPDX-License-Identifier: CC-BY-SA-4.0
-->

<!--
SPDX-FileContributor: Michael Meinel
SPDX-FileContributor: Sophie Kernchen
SPDX-FileContributor: Nitai Heeb
SPDX-FileContributor: Oliver Bertuch
-->

# Write a plugin for HERMES
 

This tutorial will present the basic steps for writing an additional harvester.
At the moment only the architecture for harvester plugins is stable.
The full code and structure is available at  [hermes-plugin-git](https://github.com/softwarepub/hermes-plugin-git).
This plugin extracts information from the local git history.
The hermes-plugin-git will help to gather contributing and branch metadata.
```{note}
For this tutorial you should be familiar with HERMES. 
If you never used HERMES before, you might want to check the tutorial: [Automated Publication with HERMES](https://docs.software-metadata.pub/en/latest/tutorials/automated-publication-with-ci.html).
```

## Plugin Architecture

HERMES uses a plugin architecture. Therefore, users are invited to contribute own features.
The structure for every plugin follows the same schema.
There is a top-level base class for every plugin. In this `HermesPlugin` class there is one abstract method `__call__` which needs to be overwritten.
Furthermore, the `HermesCommand` class provides all needs for writing a plugin used in a HERMES command.
So the `HermesPlugin`s call method gets an instance of the `HermesCommand` that triggered this plugin to run.
In our case this will be the `HermesHarvestCommand` which calls all harvest plugins.
The plugin class also uses a derivative of `HermesSettings` to add parameters that can be adapted by the configuration file.
`HermesSettings` are the base class for command specific settings.
It uses [pydantic](https://docs.pydantic.dev/latest/) [settings](https://docs.pydantic.dev/latest/api/pydantic_settings/) to specify and validate the parameters.
The user can either set the parameters in the `hermes.toml` or overwrite them in the command line.
To overwrite a parameter from command line, use the `-O` command line option followed by the dotted parameter name and the value.
E.g., you can set your authentication token for InvenioRDM by adding the following options to your call to `hermes deposit`:
```shell
hermes deposit -O invenio_rdm.auth_token YourSecretAuthToken
```

## Set Up Plugin
To write a new plugin, it is important to follow the given structure.
This means your plugins source code has a pydantic class with Settings and the plugin class which inherits from one base class.
For our specific case, we want to write a git harvest plugin.
Our class Structure should look like this:


```{code-block} python
from hermes.commands.harvest.base import HermesHarvestPlugin
from pydantic import BaseModel


class GitHarvestSettings(BaseModel):
    from_branch: str = 'main'


class GitHarvestPlugin(HermesHarvestPlugin):
    settings_class = GitHarvestSettings

    def __call__(self, command):
        print("Hello World!")

        return {}, {}
```
 
The code uses the `HermesHarvestPlugin` as base class and pydantic's base model for the settings.
In the `GitHarvestSettings` you can see that an additional parameter is defined.
The Parameter `from_branch` is specific for this plugin and can be accessed inside the plugin using `self.settings.harvest.git.from_branch` as long as our plugin will be named `git`.
In the `hermes.toml` this would be achieved by [harvest.{plugin_name}].
The `GitHarvestSettings` are associated with the `GitHarvestPlugin`.
In the plugin you need to overwrite the `__call__` method.
For now a simple "Hello World" will do. The method returns two dictionaries.
These will contain the harvested data in CodeMeta (JSON-LD) and additional information, e.g., to provide provenance information.
That is the basic structure for the plugins source code.

To integrate this code, you have to register it as a plugin in the `pyproject.toml`.
To learn more about the `pyproject.toml` check https://python-poetry.org/docs/pyproject/ or refer to [PEP621](https://peps.python.org/pep-0621/).
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
```{code-block} toml
...
[tool.poetry.dependencies]
python = "^3.10"
hermes = "^0.8.0"
...
...
[tool.poetry.plugins."hermes.harvest"]
git = "hermes_plugin_git.harvest:GitHarvestPlugin"
...
```
As you can see the plugin class from `hermes_plugin_git` is declared as `git` for the `hermes.harvest` entrypoint.
To use the plugin you have to adapt the harvest settings in the `hermes.toml`.
We will discuss the exact step after showing the other `pyproject.toml` configuration.
```{note}
You have to run poetry install to add and install all entrypoints declared in the pyproject.toml.
```

### Write Plugin to be included in HERMES
This variant is used to contribute to the HERMES community or adapt the HERMES workflow for own purposes.
If you want to contribute, see the [Contribution Guidelines](https://docs.software-metadata.pub/en/latest/dev/contribute.html).
After cloning the HERMES workflow repository you can adapt the pyproject.toml.
In the code below you see the parts with the important lines.
```{code-block} toml
...
[tool.poetry.dependencies]
...
pydantic-settings = "^2.1.0"
hermes-plugin-git = { git = "https://github.com/softwarepub/hermes-plugin-git.git", branch = "main" }
...
...
[tool.poetry.plugins."hermes.harvest"]
cff = "hermes.commands.harvest.cff:CffHarvestPlugin"
codemeta = "hermes.commands.harvest.codemeta:CodeMetaHarvestPlugin"
git = "hermes_plugin_git.harvest:GitHarvestPlugin"
...
```
In the dependencies you have to install your plugin. If your Plugin is pip installable than you can just give the name and the version.
If your plugin is in a buildable git repository, you can install it with the given expression. 
Note that this differs with the accessibility and your wishes, check [Explicit Package Sources](https://python-poetry.org/docs/repositories/#explicit-package-sources).

The second thing to adapt is to declare the access point for the plugin.
You can do that with `git = "hermes_plugin_git.harvest:GitHarvestPlugin"`.
This expression makes the `GitHarvestPlugin` from the `hermes_plugin_git` package, a `hermes.harvest` plugin named `git`.
So you need to configure this line with your plugin properties.

Now you just need to add the plugin to the `hermes.toml` and reinstall the adapted poetry package.

### Configure hermes.toml
To use the plugin, you have to activate it in the `hermes.toml`.
The settings for the plugins are also set there.
For the harvest plugin the `hermes.toml` could look like this:
```{code-block} toml
[harvest]
sources = [ "cff", "git" ] # ordered priority (first one is most important)

[harvest.cff]
enable_validation = false

[harvest.git]
from_branch = "develop"
...
```
In the `[harvest]` section you define that this plugin is used with less priority than the built-in `cff` plugin.
in the `[harvest.git]` section you set the configuration for the plugin. 
In the beginning of this tutorial we set the parameter `from_branch` in the git settings. Now we change the default `from_branch` to `develop`.
With this configuration the plugin will be used. If you run `hermes harvest`, you should see the "Hello World" message.

```{admonition} Congratulations!
You can now write plugins for HERMES.
```
To fill the plugin with code, you can check our [hermes-plugin-git](https://github.com/softwarepub/hermes-plugin-git) repository.
There is the code to check the local git history and extract contributors of the given branch.

If you have any questions, wishes or requests, feel free to contact us.
