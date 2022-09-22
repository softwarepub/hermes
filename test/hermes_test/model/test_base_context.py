# SPDX-FileCopyrightText: 2022 Michael Meinel
# SPDX-FileCopyrightText: 2022 Stephan Druskat
#
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from hermes.model.context import HermesContext


def test_context_hermes_dir_default():
    ctx = HermesContext()
    assert ctx.hermes_dir == Path('.') / '.hermes'


def test_context_hermes_dir_custom():
    ctx = HermesContext('spam')
    assert ctx.hermes_dir == Path('spam') / '.hermes'


def test_context_get_cache_default():
    ctx = HermesContext()
    assert ctx.get_cache('spam', 'eggs') == Path('.') / '.hermes' / 'spam' / 'eggs'


def test_context_get_cache_cached():
    ctx = HermesContext()
    ctx._caches[('spam', 'eggs')] = Path('spam_and_eggs')
    assert ctx.get_cache('spam', 'eggs') == Path('spam_and_eggs')


def test_context_get_cache_create(tmpdir):
    ctx = HermesContext(tmpdir)
    subdir = Path(tmpdir) / '.hermes' / 'spam'

    assert ctx.get_cache('spam', 'eggs', create=True) == subdir / 'eggs'
    assert subdir.exists()
