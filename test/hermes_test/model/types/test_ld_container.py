# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Sophie Kernchen

from hermes.model.types.ld_container import ld_container

'''we expect user of this class to give the right input data types

example extendeed json ld:
        {
      "http://schema.org/name": [{"@value": "bacon"}],
      "eggs": [{"@id": "spam"}],
      "green": [{"@id": "png"}]
        }
'''


def test_container_basic():
    cont = ld_container({"spam": [{"@value": "bacon"}]})

    assert cont.key is None
    assert cont.context == []
    assert cont._data == {"spam": [{"@value": "bacon"}]}
