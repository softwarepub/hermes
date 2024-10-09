# SPDX-FileCopyrightText: 2024 Forschungszentrum Jülich
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileContributor: Nitai Heeb

from hermes.commands.init.oauth_process import OauthProcess


USING_SANDBOX_AS_DEFAULT = True


local_port = 8334
redirect_uri = 'http://localhost:' + str(local_port) + '/callback'
sandbox_client_id = 'QJ8Q9GBI78uOdNmVNK1Vd0oAOJHqmYGvxRxiSFxt'
real_client_id = 'L0d9HQVW4Ig9PnC6qh6zkOAwgvYy08GcmHJqVVvV'
sandbox_authorize_url = 'https://sandbox.zenodo.org/oauth/authorize'
sandbox_token_url = 'https://sandbox.zenodo.org/oauth/token'
real_authorize_url = 'https://zenodo.org/oauth/authorize'
real_token_url = 'https://zenodo.org/oauth/token'
scope = "deposit:write deposit:actions"

client_id = sandbox_client_id if USING_SANDBOX_AS_DEFAULT else real_client_id
authorize_url = sandbox_authorize_url if USING_SANDBOX_AS_DEFAULT else real_authorize_url
token_url = sandbox_token_url if USING_SANDBOX_AS_DEFAULT else real_token_url


def setup(using_sandbox: bool = True):
    global client_id
    global authorize_url
    global token_url
    client_id = sandbox_client_id if using_sandbox else real_client_id
    authorize_url = sandbox_authorize_url if using_sandbox else real_authorize_url
    token_url = sandbox_token_url if using_sandbox else real_token_url


def oauth_process() -> OauthProcess:
    return OauthProcess(
        name="Zenodo",
        client_id=client_id,
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
