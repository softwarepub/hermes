# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Sophie Kernchen
import pytest
from pathlib import Path

from hermes.model.context_manager import HermesContext, HermesCache, HermesContexError


def test_context_hermes_dir_default():
    ctx = HermesContext()
    assert ctx.cache_dir == Path('./.hermes').absolute()


def test_context_hermes_dir_custom():
    ctx = HermesContext(Path('spam'))
    assert ctx.cache_dir == Path('spam') / '.hermes'


def test_get_context_default():
    ctx = HermesContext()
    ctx.prepare_step("ham")
    assert ctx["spam"]._cache_dir == Path('./.hermes/ham/spam').absolute()


def test_context_get_error():
    ctx = HermesContext()
    ctx.prepare_step("ham")
    ctx.finalize_step("ham")
    with pytest.raises(HermesContexError, match="Prepare a step first."):
        ctx["spam"]._cache_dir == Path('./.hermes/spam').absolute()


def test_finalize_context_one_item():
    ctx = HermesContext()
    ctx.prepare_step("ham")
    ctx.finalize_step("ham")
    assert ctx._current_step == []


def test_finalize_context():
    ctx = HermesContext()
    ctx.prepare_step("ham")
    ctx.prepare_step("spam")
    ctx.finalize_step("spam")
    assert ctx["spam"]._cache_dir == Path('./.hermes/ham/spam').absolute()
    assert ctx._current_step == ["ham"]


def test_finalize_context_error_no_item():
    ctx = HermesContext()
    with pytest.raises(ValueError, match="There is no step to end."):
        ctx.finalize_step("spam")


def test_finalize_context_error():
    ctx = HermesContext()
    ctx.prepare_step("ham")
    with pytest.raises(ValueError, match="Cannot end step spam while in ham."):
        ctx.finalize_step("spam")


def test_cache(tmpdir):
    ctx = HermesContext(Path(tmpdir))
    ctx.prepare_step("ham")
    with ctx["spam"] as c:
        c["bacon"] = {"data": "goose", "num": 2}

    path = tmpdir / Path('.hermes') / 'ham' / 'spam' / 'bacon.json'
    assert path.exists()
    assert path.read() == '{"data": "goose", "num": 2}'
    assert c._cached_data["bacon"] == {"data": "goose", "num": 2}


def test_hermes_cache_set(tmpdir):
    cache = HermesCache(Path(tmpdir))
    cache["bacon"] = "eggs"
    assert cache._cached_data == {"bacon": "eggs"}


def test_hermes_cache_get(tmpdir):
    cache = HermesCache(Path(tmpdir))
    cache._cached_data = {"bacon": "eggs"}
    assert cache["bacon"] == "eggs"
