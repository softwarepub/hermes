<!--
SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR)

SPDX-License-Identifier: CC-BY-SA-4.0
-->

<!--
SPDX-FileContributor: Michael Meinel
SPDX-FileContributor: Sophie Kernchen
-->

# Write a plugin for HERMES
 

This tutorial will present the basic steps for writing an additional harvester.
At the moment only the harvest architecture is stable.
The full code and structure is available at  [harvest-git](https://github.com/hermes-hmc/hermes-git).
This plugin extracts information from the local git history.
The harvest-git plugin will help to gather contributing and branch metadata.
```{note}
For this tutorial you should be familiar with HERMES. 
If you never used HERMES before, you might want to check the tutorial: [Automated Publication with HERMES](https://docs.software-metadata.pub/en/latest/tutorials/automated-publication-with-ci.html).
```

## Plugin Architecture

HERMES uses a plugin architecture. Therefore, users are invited to contribute own features.
The structure for every plugin follows the same schema.
There is a base class for every plugin. In this HermesPlugin class there is one abstract method __ call __ which needs to be overwritten.
Furthermore, the HermesCommand class provides all needs for writing a plugin used in a HERMES command.
So the HermesPlugins call method uses an Instance of the HermesCommand that triggered this plugin to run.
In our case this will be the HermesHarvestCommand which calls all harvest plugins.
The Plugin class also uses a derivative of HermesSettings to add parameters.
HermesSettings are the base class for command specific settings.
It uses pydantic settings to specify and validate the parameters.
The user can either set the parameters in the hermes.toml or overwrite them in the command line.
To overwrite the configuration, you use the -O operator with the dotted parameter name and the value.

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
 
The Code uses the HermesHarvestPlugin as base class and pydantics Basemodel for the Settings. In the GitHarvestSettings you
can see that one setting is made. The Parameter from_branch is specific for this plugin and can be reached through self.settings.harvest.git.git_branch as long as our plugin will be named git.
In the hermes.toml this would be achieved by [harvest.{plugin_name}].
The GitHarvestSettings are assigned to the GitHarvestPlugin. In the plugin you need to overwrite the __ call __ method.
For now a simple Hello World will do. The method return two dictionaries. These will later depict the harvested data in codemeta (json-ld) and information for generating hermes metadata.
That is the basic structure for the plugins source code.

To integrate this code, you have to register it as a plugin in the pyproject.toml. To learn more about the pyproject.toml check https://python-poetry.org/docs/pyproject/.
We will just look at the important places for this plugin. There are two ways to integrate this plugin. First we will show how to use the plugin environment as the running base with HERMES as a dependency.
Then we say how to integrate this plugin in HERMES itself.

### Include HERMES as Dependency
```{code-block} toml
...
[tool.poetry.dependencies]
python = "^3.10"
hermes = "^0.8.0"
...
...
[tool.poetry.plugins."hermes.harvest"]
git = "hermes_git.harvest:GitHarvestPlugin"
...
```
### Write Plugin to be included in HERMES
```{code-block} toml
...
[tool.poetry.dependencies]
...
pydantic-settings = "^2.1.0"
hermes-git = { git = "https://github.com/hermes-hmc/hermes-git.git", branch = "main" }
...
...
[tool.poetry.plugins."hermes.harvest"]
cff = "hermes.commands.harvest.cff:CffHarvestPlugin"
codemeta = "hermes.commands.harvest.codemeta:CodeMetaHarvestPlugin"
git = "hermes_git.harvest:GitHarvestPlugin"
...
```

```{admonition} Congratulations!
You can now write plugins for HERMES.
```
