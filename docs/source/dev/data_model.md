<!--
SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)

SPDX-License-Identifier: CC-BY-SA-4.0
-->

<!--
SPDX-FileContributor: Stephan Druskat <stephan.druskat@dlr.de>
-->

# Data model

`hermes`' internal data model acts like a contract between `hermes` and plugins.
It is based on [**JSON-LD (JSON Linked Data)**](https://json-ld.org/), and
the public API simplifies interaction with the data model through Python code.

Output of the different `hermes` commands consequently is valid JSON-LD, serialized as JSON, that is cached in 
subdirectories of the `.hermes/` directory that is created in the root of the project directory.

The cache is purely for internal purposes, its data should not be interacted with.

Depending on whether you develop a plugin for `hermes`, or you develop `hermes` itself, you need to know either [_some_](#json-ld-for-plugin-developers),
or _quite a few_ things about JSON-LD.

The following sections provide documentation of the data model.
They aim to help you get started with `hermes` plugin and core development,
even if you have no previous experience with JSON-LD.

## The data model for plugin developers

If you develop a plugin for `hermes`, you will only need to work with a single Python class and the public API 
it provides: {class}`hermes.model.SoftwareMetadata`.

To work with this class, it is necessary that you know _some_ things about JSON-LD.

### JSON-LD for plugin developers

```{attention}
Work in progress.
```


### Working with the `hermes` data model in plugins 

> **Goal**  
> Understand how plugins access the `hermes` data model and interact with it.

`hermes` aims to hide as much of the data model as possible behind a public API
to avoid that plugin developers have to deal with some of the more complex features of JSON-LD.

#### Model instances in different types of plugin

You can extend `hermes` with plugins for three different commands: `harvest`, `curate`, `deposit`.

The commands differ in how they work with instances of the data model.

- `harvest` plugins _create_ a single new model instance and return it.
- `curate` plugins are passed a single existing model instance (the output of `process`),
and return a single model instance.
- `deposit` plugins are passed a single existing model instance (the output of `curate`),
and return a single model instance.

#### How plugins work with the API

```{important}
Plugins access the data model _exclusively_ through the API class {class}`hermes.model.SoftwareMetadata`.
```
 
The following sections show how this class works. 

##### Creating a data model instance

Model instances are primarily created in `harvest` plugins, but may also be created in other plugins to map
existing data into.

To create a new model instance, initialize {class}`hermes.model.SoftwareMetadata`:

```{code-block} python
:caption: Initializing a default data model instance
from hermes.model import SoftwareMetadata

data = SoftwareMetadata()
```

`SoftwareMetadata` objects initialized without arguments provide the default _context_
(see [_JSON-LD for plugin developers_](#json-ld-for-plugin-developers)).
This means that now, you can use terms from the schemas included in the default context to describe software metadata.

Terms from [_CodeMeta_](https://codemeta.github.io/terms/) can be used without a prefix:

```{code-block} python
:caption: Using terms from the default schema
data["readme"] = ...
```

Terms from [_Schema.org_](https://schema.org/) can be used with the prefix `schema`:

```{code-block} python
:caption: Using terms from a non-default schema
data["schema:copyrightNotice"] = ...
```

You can also use other linked data vocabularies. To do this, you need to identify them with a prefix and register them
with the data model by passing it `extra_vocabs` as a `dict` mapping prefixes to URLs where the vocabularies are
provided as JSON-LD:

```{code-block} python
:caption: Injecting additional schemas
from hermes.model import SoftwareMetadata

# Contents served at https://bar.net/schema.jsonld:
# {
#    "@context":
#    {
#       "name": "https://schema.org/name"
#    }
# }

data = SoftwareMetadata(extra_vocabs={"foo": "https://bar.net/schema.jsonld"})

data["foo:name"] = ...
```

##### Adding data

Once you have an instance of {class}`hermes.model.SoftwareMetadata`, you can add data to it,
i.e., metadata that describes software:

```{code-block} python
:caption: Setting data values
data["name"] = "My Research Software"  # A simple "Text"-type value
# → Simplified model representation : { "name": [ "My Research Software" ] }
# Cf. "Accessing data" below
data["author"] = {"name": "Shakespeare"}  # An object value that uses terms available in the defined context
# → Simplified model representation : { "name": [ "My Research Software" ], "author": [ { "name": "Shakespeare" } ] }
# Cf. "Accessing data" below
```

##### Accessing data

You need to be able to access data in the data model instance to add, edit or remove data.
Data can be accessed by using term strings, similar to how values in Python `dict`s are accessed by keys.

```{important}
When you access data from a data model instance,
it will always be returned in a **list**-like object!
```

The reason for providing data in list-like objects is that JSON-LD treats all property values as arrays.
Even if you add "single value" data to a `hermes` data model instance via the API, the underlying JSON-LD model
will treat it as an array, i.e., a list-like object:

```{code-block} python
:caption: Internal data values are arrays
data["name"] = "My Research Software"  # → [ "My Research Software" ]
data["author"] = {"name": "Shakespeare"}       # → [ { "name": [ "Shakespeare" ] } ]
```

Therefore, you access data in the same way you would access data from a Python `list`:

1. You access single values using indices, e.g., `data["name"][0]`.
2. You can use a list-like API to interact with data objects, e.g.,
`data["name"].append("Hamilton")`, `data["name"].extend(["Hamilton", "Knuth"])`, `for name in data["name"]: ...`, etc.

##### Interacting with data

The following longer example shows different ways that you can interact with `SoftwareMetadata` objects and the data API.

```{code-block} python
:caption: Building the data model
from hermes.model import SoftwareMetadata

# Create the model object with the default context
data = SoftwareMetadata()

# Let's create author metadata for our software!
# Below each line of code, the value of `data["author"]` is given.

data["author"] = {"name": "Shakespeare"}
# → [{'name': ['Shakespeare']}]

data["author"].append({"name": "Hamilton"})
# [{'name': ['Shakespeare']}, {'name': ['Hamilton']}]

data["author"][0]["email"] = "Shakespeare@baz.net"
# [{'name': ['Shakespeare'], 'email': ['shakespeare@baz.net']}, {'name': ['Hamilton']}]

data["author"][1]["email"].append("Hamilton@baz.net")
# [{'name': ['Shakespeare'], 'email': ['shakespeare@baz.net']}, {'name': ['Hamilton'], 'email': ['hamilton@baz.net']}]

data["author"][1]["email"].extend(["hamilton@spam.org", "hamilton@eggs.com"])
# [
#   {'name': ['Shakespeare'], 'email': ['shakespeare@baz.net']},
#   {'name': ['Hamilton'], 'email': ['hamilton@baz.net', 'hamilton@spam.org', 'hamilton@eggs.com']}
# ]
```

The example continues to show how to iterate through data. 

```{code-block} python
:caption: for-loop, containment check
for i, author in enumerate(data["author"], start=1):
    if author["name"][0] in ["Shakespeare", "Hamilton"]:
        print(f"Author {i} has expected name.")
    else:
        raise ValueError("Unexpected author name found!", author["name"][0])

# Mock output:
# $> Author 1 has expected name.
# $> Author 2 has expected name.
```

```{code-block} python
:caption: Value check 
for email in data["author"][0]["email"]:
    if email.endswith(".edu"):
        print("Author has an email address at an educational institution.")
    else:
        print("Cannot confirm affiliation with educational institution for author.")

# Mock output
# $> Cannot confirm affiliation with educational institution for author.
```

```{code-block} python
:caption: Value check and list comprehension 
if all(["hamilton" in email for email in data["author"][1]["email"]]):
    print("Author has only emails with their name in it.")

# Mock output
# $> Author has only emails with their name in it.
```

The example continues to show how to assert data values.

As mentioned in the [introduction to the data model](#data-model), 
`hermes` uses a JSON-LD-like internal data model. 
The API class {class}`hermes.model.SoftwareMetadata` hides many
of the more complex aspects of JSON-LD and makes it easy to work
with the data model.

Assertions, however, operate on the internal model objects.
Therefore, they may not work as you would expect from plain
Python data:

```{code-block} python
:caption: Naive containment assertion that raises
:emphasize-lines: 5,13 
try:
    assert (
            {'name': ['Shakespeare'], 'email': ['shakespeare@baz.net']}
            in
            data["author"]
    )
    print("The author was found!")
except AssertionError:
    print("The author could not be found.")
    raise

# Mock output
# $> The author could not be found.
# $> AssertionError:
#    assert
#    {'email': ['shakespeare@baz.net'], 'name': ['Shakespeare']}
#    in
#    _LDList(
#        {'@list': [
#            {
#                'http://schema.org/name': [{'@value': 'Shakespeare'}],
#                'http://schema.org/email': [{'@value': 'shakespeare@baz.net'}]
#            },
#            {
#                'http://schema.org/name': [{'@value': 'Hamilton'}],
#                'http://schema.org/email': [
#                    {'@list': [
#                        {'@value': 'hamilton@baz.net'}, {'@value': 'hamilton@spam.org'}, {'@value': 'hamilton@eggs.com'}
#                    ]}
#                ]
#            }]
#        }
#    )
```

The mock output in the example above shows the inequality of the expected and the actual value.
The actual value is an internal data type wrapping the more complex JSON-LD data.

The complex data structure of JSON-LD is internally constructed in the `hermes` data
model, and to make it possible to work with only the data that is important - the actual terms
and their values - the internal data model types provide a function `.to_python()`.
This function can be used in assertions to assert full data integrity:

```{code-block} python
:caption: Containment assertion with `to_python()`
:emphasize-lines: 5,13 
try:
    assert (
            {'name': ['Shakespeare'], 'email': ['Shakespeare@baz.net']}
            in
            data["author"].to_python()
    )
    print("The author was found!")
except AssertionError:
    print("The author could not be found.")
    raise

# Mock output
# $> The author was found!
```

---

## See Also

- API reference: {class}`hermes.model.SoftwareMetadata`
