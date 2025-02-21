# SPDX-FileCopyrightText: 2024 Forschungszentrum Jülich GmbH
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileContributor: Nitai Heeb

import time
import requests
import oauthlib.oauth2.rfc6749.errors

from . import slim_click as sc
from .oauth_process import OauthProcess

# NOTE: We are currently not using the public Zenodo OAuth2 client. This has two reasons:
# 1. We need a non-expiring access token like the ones you create manually so that Hermes can always access the
# account later on.
# 2. Using the refresh token mechanism to compensate for that is currently not an option since it only works on
# the real Zenodo (not the sandbox) until they fix it. see test_if_refresh_token_authorization_works()

USING_SANDBOX_AS_DEFAULT = True

local_port = 8334
sandbox_client_id = 'QJ8Q9GBI78uOdNmVNK1Vd0oAOJHqmYGvxRxiSFxt'
sandbox_client_secret = 'nGuOqoDtd2tckP6lmQS3If3cY39lPLKLU8skcv72JeowNupMD2bnLparsGO9'
sandbox_base_url = 'https://sandbox.zenodo.org'
real_client_id = 'L0d9HQVW4Ig9PnC6qh6zkOAwgvYy08GcmHJqVVvV'
real_client_secret = '0HIvtC2D2aPvpq2W0GtfWdeivwkqvnvrOTGx14nUJA5lDXrEDSaQAnqxHbLH'
real_base_url = 'https://zenodo.org'
url_suffix_authorize = '/oauth/authorize'
url_suffix_token = '/oauth/token'
url_suffix_api_list = '/api/deposit/depositions'
scope = 'deposit:write deposit:actions'

client_id = client_secret = base_url = authorize_url = token_url = api_list_url = name = ""


def setup(using_sandbox: bool = USING_SANDBOX_AS_DEFAULT):
    global client_id
    global client_secret
    global base_url
    global authorize_url
    global token_url
    global api_list_url
    global name
    client_id = sandbox_client_id if using_sandbox else real_client_id
    client_secret = sandbox_client_secret if using_sandbox else real_client_secret
    base_url = sandbox_base_url if using_sandbox else real_base_url
    authorize_url = base_url + url_suffix_authorize
    token_url = base_url + url_suffix_token
    api_list_url = base_url + url_suffix_api_list
    name = "Zenodo (Sandbox)" if using_sandbox else "Zenodo"


setup()


def oauth_process() -> OauthProcess:
    return OauthProcess(
        name=name,
        client_id=client_id,
        client_secret=client_secret,
        token_url=token_url,
        authorize_url=authorize_url,
        scope=scope,
        local_port=local_port
    )


def get_tokens() -> dict[str: str]:
    """Starts the oauth procedure and returns collected tokens as dict"""
    return oauth_process().get_tokens()


def get_refresh_token(with_prefix: bool = True) -> str:
    return get_tokens().get('refresh_token', '')


def test_if_token_is_valid(token: str) -> bool:
    response = requests.get(api_list_url, {'access_token': token})
    return response.status_code == 200


def test_if_refresh_token_authorization_works():
    for version in [True, False]:
        setup(version)
        sc.echo(f"Testing if the {name} refresh token mechanism works...",
                formatting=sc.Formats.BOLD+sc.Formats.WARNING)
        try:
            tokens = get_tokens()
            sc.debug_info(tokens)
            if tokens:
                sc.echo("Regular OAuth does work.", formatting=sc.Formats.OKGREEN)
            new_tokens = oauth_process().get_tokens_from_refresh_token(tokens["refresh_token"])
            sc.debug_info(new_tokens)
            if new_tokens:
                sc.echo(f"Refresh token auth does work for {name}.",
                        formatting=sc.Formats.OKGREEN+sc.Formats.BOLD)
        except oauthlib.oauth2.rfc6749.errors.InvalidGrantError:
            sc.echo(f"Refresh token auth does not work for {name}: Invalid Grant.",
                    formatting=sc.Formats.FAIL+sc.Formats.BOLD)
        time.sleep(2)
