<!--
SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR), Forschungszentrum Jülich, Helmholtz-Zentrum Dresden-Rossendorf

SPDX-License-Identifier: CC-BY-SA-4.0
-->
# Standardized provenance recording

* Status: proposed
* Deciders: sdruskat, skernchen, notactuallyfinn
* Date: 2025-10-17

Technical story: 
* https://github.com/softwarepub/hermes/pull/442
* https://github.com/softwarepub/hermes/issues/363

## Context and Problem Statement

To consolidate traceability of the metadata, and resolution based on metadata sources in case of duplicates, etc., we need to record the provenance of metadata values in a __standardized__ way.
Additionally we use the [PROV-O ontology](https://www.w3.org/TR/prov-o/) and [JSON-LD](https://www.w3.org/TR/json-ld/) and want that HERMES records as much of the provenance as possible to not overcomplicate plugin development.

To do this, we need to specify what provenance information is recorded and how it can be implemented in HERMES to make it easy to use.

## Considered Options

* Provide HERMES API-methods that also document themselves

## Decision Outcome

Chosen option: "Provide HERMES API-methods that also document themselves", because comes out best.

## Pros and Cons of the Options

### Provide HERMES API-methods that also document themselves

Provide API-methods for loading, writing, making web requests, etc. that document themselves.<br>
Those methods take also the function that should be used for the task at hand and just define a framework in which we implement the provenance-data recording.<br>
Like so:
```python
class HermesPlugin():
    def load(func, path: str, *args, **kwargs):
        # TODO: handle and record byte formats properly
        with open(path) as fi:
            data = func(fi, *args, **kwargs)
        prov.record("load", path, func.__name__, data) # also module of func
        return data

    def write(func, path: str, data, *args, **kwargs):
        # TODO: handle and record byte formats properly
        with open(path) as fi:
            func(fi, data, *args, **kwargs)
        prov.record("write", path, func.__name__, data) # also module of func
```

* Good, because allows for recording of provenance information of the plugins
* Good, because it isn't making plugin development harder
* Bad, because API methods may not cover all I/O functionality python provides
* Bad, because it doesn't cover merging, mapping, etc.  

All provenance information should be recorded in the following format where addtional properties of agents, activites and entities are values of schema and codemeta fields:

![](./hermes-prov-diagram/hermes-prov.svg)<br>
source: [hermes-prov.drawio](./hermes-prov-diagram/hermes-prov.drawio)
