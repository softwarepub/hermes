# SPDX-FileCopyrightText: 2024 Forschungszentrum Jülich
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileContributor: Nitai Heeb

import logging
from hermes.commands.init.oauth_process import OauthProcess

USING_SANDBOX = True

local_port = 8334
redirect_uri = 'http://localhost:' + str(local_port) + '/callback'
sandbox_client_id = 'QJ8Q9GBI78uOdNmVNK1Vd0oAOJHqmYGvxRxiSFxt'
sandbox_client_secret = 'nGuOqoDtd2tckP6lmQS3If3cY39lPLKLU8skcv72JeowNupMD2bnLparsGO9'
real_client_id = 'L0d9HQVW4Ig9PnC6qh6zkOAwgvYy08GcmHJqVVvV'
real_client_secret = '0HIvtC2D2aPvpq2W0GtfWdeivwkqvnvrOTGx14nUJA5lDXrEDSaQAnqxHbLH'
sandbox_authorize_url = 'https://sandbox.zenodo.org/oauth/authorize'
sandbox_token_url = 'https://sandbox.zenodo.org/oauth/token'
real_authorize_url = 'https://zenodo.org/oauth/authorize'
real_token_url = 'https://zenodo.org/oauth/token'
scope = "deposit:write deposit:actions"

client_id = sandbox_client_id if USING_SANDBOX else real_client_id
client_secret = sandbox_client_secret if USING_SANDBOX else real_client_secret
authorize_url = sandbox_authorize_url if USING_SANDBOX else real_authorize_url
token_url = sandbox_token_url if USING_SANDBOX else real_token_url

class StringHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.log_messages = []

    def emit(self, record):
        log_entry = self.format(record)
        self.log_messages.append(log_entry)

    def get_logs(self):
        return self.log_messages

string_handler = StringHandler()
def print_logs_for_requests():
    """Forwards all logging from the requests_oauthlib.oauth2_session module to the console so we can see the used request headers and data."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[string_handler]
    )

    module_logger = logging.getLogger('requests_oauthlib.oauth2_session')
    module_logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)

    module_logger.addHandler(console_handler)

    module_logger.addHandler(string_handler)

def oauth_process() -> OauthProcess:
    return OauthProcess(
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
    return get_tokens().setdefault('refresh_token', '')