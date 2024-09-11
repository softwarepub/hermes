# SPDX-FileCopyrightText: 2024 Forschungszentrum Jülich
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileContributor: Nitai Heeb

from hermes.commands.init.oauth_process import OauthProcess


local_port = 8333
client_id = 'Ov23ctl0gNzr9smeVIHR'
client_secret = 'd516303374f7e55189fe74fb2af77f31a965ad57'
authorization_base_url = 'https://github.com/login/oauth/authorize'
token_url = 'https://github.com/login/oauth/access_token'
redirect_uri = 'http://localhost:' + str(local_port) + '/callback'
scope = "repo"


def oauth_process() -> OauthProcess:
    return OauthProcess(
        client_id=client_id,
        client_secret=client_secret,
        token_url=token_url,
        authorize_url=authorization_base_url,
        scope=scope,
        local_port=local_port
    )


def get_tokens() -> dict[str: str]:
    """Starts the oauth procedure and returns collected tokens as dict"""
    return oauth_process().get_tokens()


def get_access_token() -> str:
    return get_tokens().get('access_token', '')
