# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Sophie Kernchen

import pytest

from hermes.model.types.ld_list import ld_list


def test_undefined_list():
    with pytest.raises(ValueError):
        li = ld_list([{"spam": [{"@value": "bacon"}]}])

@pytest.mark.dev
def test_list_basics():
    li = ld_list([{"@list": [0], "spam": [{"@value": "bacon"}]}])
    assert li._data == [{"@list": [0], "spam": [{"@value": "bacon"}]}]
    assert li.container == '@list'
    assert li.item_list == [0]

