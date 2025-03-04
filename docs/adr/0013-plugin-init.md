<!--
SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR), Forschungszentrum Jülich, Helmholtz-Zentrum Dresden-Rossendorf

SPDX-License-Identifier: CC-BY-SA-4.0
-->
# Installing plugins from the marketplace using hermes init

* Status: accepted
* Deciders: nheeb
* Date: 2025-03-04

## Context and Problem Statement

For a smooth user experience common plugins (those which are on the marketplace) should installable via `hermes init`. That however means we need to decide on a way for the plugins to ask question during that same init process.

## Considered Options

* **Full install**: Plugins are installed locally during `hermes init`, can hook into the init process, and ask questions themselves to adjust the `hermes.toml` or similar.
* **No install**: Plugins are only added to the CI pipeline as `pip install ...` lines. Additional questions for the init process could be added in the marketplace input mask along with a property name under which the answer is stored in the `hermes.toml`.
* **Partial install**: Plugins are only added to the CI pipeline as `pip install ...` lines. Additional questions for the init process are handled in a "detached" script that is downloaded, executed locally, and then deleted again (this script may only have dependencies of Hermes).

## Decision Outcome

Chosen option: "**Partial install**", because it is a good trade-off between giving plugins more controll over their init process and not being too invasive with local installs.

## Pros and Cons of the Options

### Full install
- (+) Plugins have a lot of control over how they design their own init process.
- (+) The plugin can be used locally on the device directly if the user intends to do so.
- (-) The plugin might be installed unnecessarily, as locally only the init part may be executed.
- (-) The plugin may introduce many dependencies that the user doesn’t necessarily need.
- (-) There could be environment complications (e.g., if Hermes was installed with `pipx`).

### No install
- (+) Nothing is installed locally via `hermes init`.
- (+) Overall, slightly less effort for the init command and plugin developers.
- (-) The marketplace would need input masks for an arbitrary number of such questions.
- (-) Plugins have little control over how they design their own init process.
- (-) Plugins intended for local use must be installed manually.

### Partial install
- (+) Nothing is installed locally via `hermes init`.
- (+) Plugins have relatively high control over how they design their own init process.
- (-) Plugins intended for local use must be installed manually.
