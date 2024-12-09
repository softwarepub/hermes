# SPDX-FileCopyrightText: 2024 Forschungszentrum Jülich
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileContributor: Nitai Heeb


import pytest
from hermes.commands.init.base import convert_remote_url


@pytest.mark.parametrize(
    "url,expected",
    [
        ("git@github.com:softwarepub/showcase.git", "https://github.com/softwarepub/showcase"),
        ("https://github.com/softwarepub/hermes.git", "https://github.com/softwarepub/hermes"),
        ("git@github.com:a/b", "https://github.com/a/b"),
        ("https://github.com/a/b", "https://github.com/a/b"),
    ]
)
def test_url_parsing(url, expected):
    assert convert_remote_url(url) == expected
