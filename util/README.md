<!--
SPDX-FileCopyrightText: 2022 Stephan Druskat
-->

# Development utilities

## `add-copyright-headers.py`

This script adds copyright headers to files with the help of the [reuse helper tool](https://git.fsfe.org/reuse/tool), depending on who has contributed to a file as
recorded in the git tree.
For details, please see the script itself.

### Requirements

- `git` (should be available when you're working in this repository)
- `GitPython` Python package (available as a dev dependency via `pyproject.toml`)
- `reuse` Python CLI (available as a dev dependency via `pyproject.toml`)

### Usage

```bash
# Enter a Poetry shell with activated virtual environment
poetry shell

cd util/
python add-copyright-headers.py

# Inspect the changes to see if everything worked out as expected
```

