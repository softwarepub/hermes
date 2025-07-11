# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
import pytest
from pathlib import Path

from hermes.model.context_manager import HermesContext, HermesCache


def test_context_hermes_dir_default():
    ctx = HermesContext()
    assert ctx.cache_dir == Path('./.hermes').absolute()


def test_context_hermes_dir_custom():
    ctx = HermesContext('spam')     # TODO: #367
    assert ctx.cache_dir == Path('spam') / '.hermes'


def test_get_context_default():
    ctx = HermesContext()
    ctx.prepare_step("ham")
    assert ctx["spam"]._cache_dir == Path('./.hermes/ham/spam').absolute()


def test_finalize_context():
    ctx = HermesContext()
    ctx.prepare_step("ham")  # TODO: #373 to fix, then you can delete one prepare_step
    ctx.prepare_step("spam")
    ctx.finalize_step("spam")
    assert ctx["spam"]._cache_dir == Path('./.hermes/ham/spam').absolute()


def test_finalize_context_error_list_one_element():
    ctx = HermesContext()
    ctx.prepare_step("ham")
    with pytest.raises(ValueError):     # TODO: #373 to fix, index out of range
        ctx.finalize_step("spam")


def test_finalize_context_error():
    ctx = HermesContext()
    ctx.prepare_step("ham")
    ctx.prepare_step("eggs")
    with pytest.raises(ValueError, match=f"Cannot end step spam while in eggs."):    # TODO: #373 format string and error message
        ctx.finalize_step("spam")

@pytest.mark.dev
def test_cache(tmpdir):
    ctx = HermesContext(Path(tmpdir))
    ctx.prepare_step("ham")
    with ctx["spam"] as c:
        c["bacon"] = {"data": "goose", "num": 2}

    path = Path('tmpdir/.hermes') / 'ham' / 'spam' / 'bacon.json'

    assert path.exists()
    assert c._cached_data["bacon"] == {"data": "goose", "num": 2}


def test_hermes_cache_set(tmpdir):
    cache = HermesCache(Path(tmpdir))
    cache["bacon"] = "eggs"
    assert cache._cached_data == {"bacon": "eggs"}


@pytest.mark.dev
def test_context_get_cache_create(tmpdir):
    ctx = HermesContext(tmpdir)
    subdir = Path(tmpdir) / '.hermes' / 'spam'

    assert ctx.get_cache('spam', 'eggs', create=True) == subdir / 'eggs.json'
    assert subdir.exists()
