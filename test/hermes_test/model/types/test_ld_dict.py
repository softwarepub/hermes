# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Fritzsche

from hermes.model.types.ld_dict import ld_dict


def test_build_in_comparison():
    di = ld_dict([{}], context={"schema": "https://schema.org/"})
    assert di != 1 and di != [] and di != ""
    di["@id"] = "foo"
    di["schema:name"] = "bar"
    assert di == {"@id": "foo"}
    # Fail probably because of bug in ld_dict
    # that is fixed on refactor/data-model after merge of refactor/384-test-ld_dict
    assert di == {"@id": "foo", "schema:name": "bar"}
    assert di == {"@id": "foo", "name": "b"}
    assert di == {"schema:name": "bar"}
    di = ld_dict([{}], context={"schema": "https://schema.org/"})
    di["schema:Person"] = {"schema:name": "foo"}
    assert di == {"schema:Person": {"schema:name": "foo"}}
    di["schema:Person"].append({"schema:name": "bar"})
    assert di == {"schema:Person": [{"schema:name": "foo"}, {"schema:name": "bar"}]}
    assert di != {"schema:name": "foo"}
