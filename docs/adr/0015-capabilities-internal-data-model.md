<!--
SPDX-FileCopyrightText: 2026 German Aerospace Center (DLR), Forschungszentrum Jülich, Helmholtz-Zentrum Dresden-Rossendorf

SPDX-License-Identifier: CC-BY-SA-4.0
-->

# Capabilities of the internal data model

* Status: proposed
* Date: 2026-03-17

## Context and Problem Statement

As decided in [ADR 2](./0002-use-a-common-data-model) the metadata that is created and manipulated by HERMES is stored as JSON-LD.
But the critical questions how it is stored and how it can be accessed are not yet discussed.
There are a few requirements though:
* The data should probably be stored in some form of expanded JSON-LD.
* Read and write access should be possible with non expanded JSON-LD (the values then have to be expanded).
* The objects should be as user friendly as possible (supply many different ways to interact with the data).

## Considered Options

* Providing our own JSON-LD wrapper classes

## Decision Outcome

Chosen option: "", because comes out best.

## Pros and Cons of the Options

### Providing our own JSON-LD wrapper classes

This includes a base class (supplying basic functions like expansion and compaction named `ld_container`), a class representing dictionaries (named `ld_dict`) and one for list-like objects (like @list and @set named `ld_list`). Additionally a wrapper class (named SoftwareMetdata) for complete sets of metadata of SoftwareSourceCode and SoftwareApplication (schema.org types) is supplied which is an `ld_dict` that has a standard context and supplies a function to load from the HERMES cache.
Furthermore for processing of JSON-LD the `JsonLdProcessor` from `jsonld` from the [pyld](https://pypi.org/project/PyLD/) package is used.

The following features will be supported:
```python
from hermes.model import SoftwareMetadata

# initializing SoftwareMetadata objects
SoftwareMetadata()  # contains no data and only standard context
SoftwareMetadata(extra_vocabs=ctx)  # contains no data but extra context (ctx is a dict mapping shortend prefixes to full iri's)
SoftwareMetadata(data)  # data can be any valid JSON-LD dictionary (where dicts and lists can be replaced by ld_dicts and ld_lists)
SoftwareMetadata(data, ctx)  # contains the given data and context additionally to the standard context

metadata = SoftwareMetadata(data)
# getting values from ld_dicts (here metadata)
# key may be compacted or expanded, returned is always an ld_list
metadata[key]  # KeyError if no value in metadata for that key
metadata.get(key, default_value)  # if default_value is given, it is returned when no entry for key is in metadata
metadata.set_default(key, default_value)  # inserts the default_value before returning metadata[key] if no entry for key is in metadata
                                          # default value may only be a value that can be inserted as a value of key
# iterating over ld_dicts
for key, value in metadata.items():  # iterating over all key, value pairs, value is metadata[key]
    # do stuff
for key in metadata.keys():  # iterating over all expanded keys
    # do stuff
for compact_key in metadata.compact_keys():  # iterating over all compacted keys
    # do stuff
# setting values in ld_dicts
# key may be compacted or expanded, value may be any valid JSON-LD value (where dicts and lists can be replaced by ld_dicts and ld_lists)
metadata[key] = value
metadata.set_default(key, value)  # sets metadata[key] to value if metadata had no entry for key before
metadata.update(values)  # values is a dict mapping keys to values (each with the same constrictions as key and value)
metadata.emplace(key)  # equivalent to metadata[key] = [] if key not in metadata
# misc functions for ld_dicts
bool(metadata)  # False if and only if metadata == {}
metadata == value  # ld_dicts are comparable to dicts and ld_dicts
metadata != value
key in metadata  # checks if there is an entry for that key
metadata.to_python()  # return a pythonized version of the contents (compacted version where all ld_dicts are dicts and ld_lists lists)
del metadata[key]  # removes the entry of key
metadata.ref  # returns {"@id": metadata["@id"]}

metadata_list = SoftwareMetadata(data)[key]
# getting values from ld_lists (here metadata_list)
# returned single values can be ld_lists, ld_dicts, ints, floats, bools, strings, dates, datetimes, times
metadata_list[index] # index may be int or slice (when slice a list of single values is returned)
# iterating over ld_lists
for item in metadata_list:  # iterating over all items
    # do stuff
for index in range(len(metadata_list)):  # iterate over all indices
    # do stuff
# setting values in ld_lists
# value may be any valid JSON-LD value (where dicts and lists can be replaced by ld_dicts and ld_lists)
metadata_list[index] = value  # index is int
metadata_list[index] = values  # index is slice and values is some iterable of values that share the constrictions of value
metadata_list.append(value)
metadata_list.extend(values)  # values is some iterable of values that share the constrictions of value
# misc functions for ld_lists
len(metadata_list)  # gives the number of elements
metadata_list == value  # ld_lists are comparable to ld_lists and lists
metadata_list != value
metadata_list.to_python()  # return a pythonized version of the contents (compacted version where all ld_dicts are dicts and ld_lists lists)
del metadata_list[index]  # removes the entry/ entries at index, where index is int or slice
value in metadata_list  # checks if a value is in the list

metadata = SoftwareMetadata(data)
# additional valuable information
metadata_list_copy = metadata_list = metadata[key] # assume metadata has an entry for key
metadata_list.append(value) # any operation here will have an effect on metadata and metadata_list_copy (this works for every nesting depth)
```

* Good, because it keeps the expanded JSON-LD data safe from getting invalidated by accidental wrong manipulation
* Good, because it offers much flexibility and easy access for the user/ plugin developers
* Good, because it could be extended to record provenance information on every manipulation
* Bad, because hard to maintain
