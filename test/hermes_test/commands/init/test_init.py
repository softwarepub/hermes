# SPDX-FileCopyrightText: 2024 Forschungszentrum Jülich
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileContributor: Nitai Heeb

import json
import pytest
from hermes.commands.init.base import convert_remote_url, is_git_installed, string_in_file, download_file_from_url
from unittest.mock import patch, MagicMock
import hermes.commands.init.util.oauth_process as oauth_process


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


@patch("subprocess.run")
def test_is_git_installed(mock_subprocess):
    mock_subprocess.return_value.returncode = 0
    assert is_git_installed()


def test_string_in_file(tmp_path):
    test_file = tmp_path / "test.txt"
    with open(test_file, "w") as f:
        f.write("Test\nContent\nTest")
    assert string_in_file(test_file, "Content") is True
    assert string_in_file(test_file, "Nothing") is False


@patch("requests.get")
def test_download_file_from_url(mock_get, tmp_path):
    mock_get.return_value.__enter__.return_value.iter_content.return_value = [b"test_content"]
    mock_get.return_value.__enter__.return_value.raise_for_status = MagicMock()

    test_file = tmp_path / "downloaded.txt"
    download_file_from_url("https://test.com/file.txt", test_file)

    with open(test_file, "r", encoding="utf-8") as f:
        assert f.read() == "test_content"


@pytest.mark.parametrize(
    "response,d",
    [
        ('{"access_token": "abc123", "test": "200"}', {"access_token": "abc123", "test": "200"}),
        ("access_token=abc123&test=200", {"access_token": "abc123", "test": "200"}),
        ("example", {})
    ]
)
def test_parse_response_to_dict(response: str, d: dict):
    assert oauth_process.parse_response_to_dict(response) == d


@pytest.fixture
def oauth():
    return oauth_process.OauthProcess(
        name="TestService",
        client_id="test_client",
        client_secret="test_secret",
        authorize_url="https://example.com/oauth/authorize",
        token_url="https://example.com/oauth/token",
        device_code_url="https://example.com/oauth/authorize_device",
        scope="xxx",
        local_port=1234
    )


@patch("requests.post")
def test_get_tokens_from_device_flow(mock_post, oauth):
    mock_post.side_effect = [
        MagicMock(
            status_code=200,
            json=lambda: {
                "device_code": "test_device_code",
                "user_code": "test_user_code",
                "verification_uri": "https://example.com/device",
                "interval": 1
            },
            text=json.dumps({
                "device_code": "test_device_code",
                "user_code": "test_user_code",
                "verification_uri": "https://example.com/device",
                "interval": 1
            })
        ),
        MagicMock(status_code=200, json=lambda: {"access_token": "test_access_token"})
    ]

    result = oauth.get_tokens_from_device_flow()
    assert result == {"access_token": "test_access_token"}
