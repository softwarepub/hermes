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

Output of the different `hermes` subcommands consequently are valid JSON-LD files that are cached in
subdirectories of the `.hermes/` directory that is created in the root of the project directory (see following diagram).
```
.hermes
│  audit.log
├──curate
│  └──result
│     ├──codemeta.json
│     ├──context.json
│     └──expanded.json
├──harvest
│  └──cff <- for every plugin one folder
│     ├──codemeta.json
|     ├──context.json
│     └──expanded.json
└──process
   └──result
      ├──codemeta.json
      ├──context.json
      └──expanded.json
```

The cache should only be interacted with via the `hermes` libraries.

Depending on whether you develop a plugin for `hermes`, or you develop `hermes` itself, you need to know either [_some_](#json-ld-for-plugin-developers),
or _quite a few_ things about JSON-LD.

The following sections provide documentation of the data model.
They aim to help you get started with `hermes` plugin and core development,
even if you have no previous experience with JSON-LD.

## The data model for plugin developers

If you develop a plugin for `hermes`, you will only need to work with three Python classes and the public API 
they provide: {class}`hermes.model.api.SoftwareMetadata`, {class}`hermes.model.types.ld_dict.ld_dict` and {class}`hermes.model.types.ld_list.ld_list`

To work with those classes, it is necessary that you know _some_ things about JSON-LD.

### JSON-LD for plugin developers

```{attention}
Work in progress.
```


### Working with the `hermes` data model in plugins 

> **Goal**  
> Understand how plugins access the `hermes` data model and interact with it.

`hermes` aims to hide as much of the data model as possible behind a public API
to avoid that plugin developers have to deal with some of the more complex features of JSON-LD.

You can extend `hermes` with plugins for all five different commands: `harvest`, `process`, `curate`, `deposit`, `postprocess`.

The commands differ in how they work with instances of the data model.

- `harvest` plugins _create_ a single new model instance and return it.
- `process` plugins to _do not_ interact with any model instance and only supply Hermes with strategies to do so.
- `curate` plugins _are passed_ a single existing model instance (the output of `process`),
and _return_ a single model instance.
- `deposit` plugins _are passed_ a single existing model instance (the output of `curate`),
but currently _do not return_ a model instance but instead JSON in their own format.
- `postprocess` plugins currently _do not_ interact with any model instance
but only with the JSON data of the associated `deposit` plugin

```{important}
Plugins access the data model _exclusively_ through the API provided by the three classes {class}`~hermes.model.api.SoftwareMetadata`, {class}`~hermes.model.types.ld_dict.ld_dict` and {class}`~hermes.model.types.ld_list.ld_list`.
```
 
The following sections show how those classes work (together). 

#### Creating a data model instance

Model instances are primarily created in `harvest` plugins, but may also be created in other plugins to map
existing data into.

To create a new model instance, initialize {class}`~hermes.model.api.SoftwareMetadata`:

```{code-block} python
:caption: Initializing a default data model instance
from hermes.model import SoftwareMetadata

data = SoftwareMetadata()
```

The {meth}`~.hermes.model.api.SoftwareMetadata.__init__` method takes two arguments `data` and `extra_vocabs` (in this positional order).

If the `SoftwareMetadata` object is initialized without a value for `data` it is empty.
Passing a value to the argument `data` initialized the model instance with passed data.
This data must be a native python object that resembles valid JSON-LD data:

```{code-block} python
:caption: Initializing a model instance with data
from hermes.model import SoftwareMetadata

value = {
    "schema:name": "My software",
    "schema:description": [{"@value": "This is software."}],
    "http://schema.org/author": {"@type": "schema:Person", "schema:email": "test@example.com"}
}

data = SoftwareMetadata(value)
```

If the object is initialized without a value for `extra_vocabs` the default _context_
(see [_JSON-LD for plugin developers_](#json-ld-for-plugin-developers)) is used.
This means that, you can only use terms from the schemas included in the default context to describe software metadata.
That means terms from [_CodeMeta_](https://codemeta.github.io/terms/) can be used without a prefix, i.e. only `readme`, while terms from [_Schema.org_](https://schema.org/) can be used with the prefix `schema`, e.g. `schema:copyrightNotice`.
Of course the absolute IRI can be used too, e.g. `https://codemeta.github.io/terms/readme` and `https://schema.org/copyrightNotice`.

You can also use other linked data vocabularies. To do this, you need to identify them with a prefix and register them
with the data model by passing it `extra_vocabs` as a `dict` mapping prefixes to URLs where the vocabularies are
provided as JSON-LD:

```{code-block} python
:caption: Injecting additional schemas
from hermes.model import SoftwareMetadata

# Contents served at https://example.com/schema.jsonld:
# {
#    "@context":
#    {
#       "name": "https://schema.org/name"
#    }
# }

data = SoftwareMetadata(extra_vocabs={"foo": "https://example.com/schema.jsonld"})

data["foo:name"] = ...
```

#### Adding data

Once you have an instance of {class}`~hermes.model.types.ld_dict.ld_dict` or its subclass {class}`~hermes.model.api.SoftwareMetadata` (cf. for {class}`~hermes.model.types.ld_list.ld_list` below),
you can add data to it, i.e., metadata that describes software:

```{code-block} python
:caption: Setting data values in ld_dicts
from datetime import datetime
from hermes.model import SoftwareMetadata

data = SoftwareMetadata()
data["name"] = "My Research Software"  # A simple "Text"-type value (int, float and bool are supported too)
data["author"] = {"name": "Shakespeare"}  # An object value that uses terms available in the defined context
data["schema:description"] = ["software for research", "more descriptions", "Why so many descriptions?"]  # lists of values
data["schema:dateCreated"] = datetime.now()  # A datetime object (time and date are also supported)
# → Simplified representation of data:
#{
#    "name": ["My Research Software"],
#    "author": [{"name": "Shakespeare"}],
#    "schema:description": ["software for research", "more descriptions", "Why so many descriptions?"],
#    "schema:dateCreated": ["{Iso format string}"]
#}
# Cf. "Accessing data" below
```

Other methods to add data are:
```{code-block} python
:caption: Setting data values in ld_dicts (advanced)
from hermes.model import SoftwareMetadata

data = SoftwareMetadata()
data.emplace("name")  # similar to data["name"]=[] but does not overwrite
data.setdefault("schema:description", "my description")  # similar to data["schema:description"]="my description" but does not overwrite data and returns the value after the operation
data.update({"name": "foo", "schema:dateCreated": []})  # just like dict.update()
```

Adding data to {class}`~hermes.model.types.ld_list.ld_list` can be done like that:

```{code-block} python
:caption: Setting data values in ld_lists
from datetime import datetime

data_list.append("bits")  # appending
data_list.extend(["apples", "paper"])  # extending
data_list[1] = "foo"  # replacing value
data_list[1:3] = ["bytes", "silicon"]  # replacing values
# → Simplified representation of data_list: ["bits", "bytes", "silicon"]
# Cf. "Accessing data" below
```

#### Accessing data

You need to be able to access data in the data model instance to add, edit or remove data.
Data can be accessed by using term strings, similar to how values in Python `dict`s are accessed by keys.

```{important}
When you access data from a data model instance or a {class}`~hermes.model.types.ld_dict.ld_dict`,
it will always be returned in a **list**-like object (of class {class}`~hermes.model.types.ld_list.ld_list`)!
```

The reason for providing data in list-like objects is that exapnded JSON-LD treats all property values as arrays ([source](https://www.w3.org/TR/json-ld11-api/#expansion-algorithm:~:text=or%20keywords%20and-,all%20JSON%2DLD%20values%20are%20expressed%20in%20arrays%20in%20expanded%20form.,-5.1.1%20Overview)).
Even if you add "single value" data to a `hermes` data model instance via the API, the underlying JSON-LD model
will treat it as an array, i.e., returns it as an object of {class}`~hermes.model.types.ld_list.ld_list`:

```{code-block} python
:caption: Accessing data from ld_dicts
# → Simplified representation of data: {"name": ["My Research Software"]}
# All following statements return an ld_list whose simplified representation is [ "My Research Software" ]
data["name"]
data.get("name")
data.setdefault("name", value)  # where data["name"]=value would be evoked, if data hadn't contained a value for "name", and then data["name"] returned anyways
```

{class}`~hermes.model.types.ld_dict.ld_dict` also implements {meth}`~hermes.model.types.ld_dict.ld_dict.keys` and {meth}`~hermes.model.types.ld_dict.ld_dict.compact_keys` that return a iterator-like view on the expanded or compacted keys respectively.
{meth}`~hermes.model.types.ld_dict.ld_dict.items` works like `items()` from `dict` but returns the keys in their expanded version.

Accessing data from a {class}`~hermes.model.types.ld_list.ld_list` can be done similar but returns {class}`~hermes.model.types.ld_dict.ld_dict`s, {class}`~hermes.model.types.ld_list.ld_list`s, strings, int, bool, `datetime` (or `time` or `date`) objects.
Therefore, you access data in the same way you would access data from a Python `list`:

1. You access single values using indices and slices, e.g., `data["name"][0]`.
2. You can use a list-like API to interact with data objects, e.g. `for name in data["name"]: ...`.

#### Interacting with data

The following longer example shows different ways that you can interact with `SoftwareMetadata` objects and the data API.

```{code-block} python
:caption: Building the data model
from hermes.model import SoftwareMetadata

# Create the model object with the default context
data = SoftwareMetadata()

# Let's create author metadata for our software!
# Below each line of code, the value of `data["author"]` is given.

data["author"] = {"name": "Shakespeare"}
# [{'name': ['Shakespeare']}]

data["author"].append({"name": "Hamilton"})
# [{'name': ['Shakespeare']}, {'name': ['Hamilton']}]

data["author"][0]["email"] = "shakespeare@example.net"
# [{'name': ['Shakespeare'], 'email': ['shakespeare@example.net']}, {'name': ['Hamilton']}]

data["author"][1].emplace("email") # instead of testing whether a key is contained in the ld_dict and setting or appending, just emplace the key
# [{'name': ['Shakespeare'], 'email': ['shakespeare@example.net']}, {'name': ['Hamilton'], 'email': []}]

data["author"][1]["email"].append("hamilton@example.net")
# [{'name': ['Shakespeare'], 'email': ['shakespeare@example.net']}, {'name': ['Hamilton'], 'email': ['hamilton@example.net']}]

data["author"][1]["email"].extend(["hamilton@example.org", "hamilton@example.com"])
# [
#   {'name': ['Shakespeare'], 'email': ['shakespeare@example.net']},
#   {'name': ['Hamilton'], 'email': ['hamilton@example.net', 'hamilton@example.org', 'hamilton@example.com']}
# ]
```

The example continues to show how to iterate through data and test whether a value is contained.

```{code-block} python
:caption: for-loop, containment check
for i, author in enumerate(data["author"], start=1):
    if any(name in author["name"][0] for name in ["Shakespeare", "Hamilton"]):
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
        print("Shakespeare has an email address at an educational institution.")
        break
else:
    print("Cannot confirm affiliation with educational institution for Shakespeare.")

# Mock output
# $> Cannot confirm affiliation with educational institution for Shakespeare.
```

```{code-block} python
:caption: Value check and list comprehension
if all(["hamilton" in email for email in data["author"][1]["email"]]):
    print("Author has only emails with their name in it.")

# Mock output
# $> Author has only emails with their name in it.
```

The example continues to show how to assert data values.

The API class hides the internal model objects.
Therefore you can use many different values (compacted, expanded, some mix of them, etc.) that will be treated as the same object.

```{code-block} python
:caption: Containment assertion
:emphasize-lines: 5,13 
try:
    assert (
        {'name': [{'@value': 'Shakespeare'}], 'http://schema.org/email': ['shakespeare@example.net']}
        in
        data["author"]
    )
    print("The author was found!")
except AssertionError:
    print("The author could not be found.")
    raise

# Mock output
# $> The author was found!
#
#
# Internal Model from data["author"]:
# {'@list': [
#     {
#         'http://schema.org/name': [{'@value': 'Shakespeare'}],
#         'http://schema.org/email': [{'@value': 'shakespeare@example.net'}]
#     },
#     {
#         'http://schema.org/name': [{'@value': 'Hamilton'}],
#         'http://schema.org/email': [
#                 {'@value': 'hamilton@example.net'}, {'@value': 'hamilton@example.org'}, {'@value': 'hamilton@example.com'}
#         ]
#     }
# ]}
```

The classes also support complex equality checks that work just like the presented containment checks.

---

## See Also

- API reference: {class}`~hermes.model.api.SoftwareMetadata`, {class}`~hermes.model.types.ld_dict.ld_dict` and {class}`~hermes.model.types.ld_list.ld_list`
