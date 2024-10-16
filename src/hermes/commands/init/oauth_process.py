# SPDX-FileCopyrightText: 2024 Forschungszentrum Jülich
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileContributor: Nitai Heeb
# SPDX-FileContributor: David Pape

from __future__ import annotations
import os
import threading
import time
import webbrowser
import requests
import json
from threading import Event
from requests_oauthlib import OAuth2Session
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
import hermes.commands.init.slim_click as sc

PREFER_DEVICE_FLOW = True
DEACTIVATE_BROWSER_OPENING = False


def parse_response_to_dict(response_text: str) -> dict:
    try:
        response_dict = json.loads(response_text)
        return response_dict
    except json.JSONDecodeError:
        return dict(parse_qs(response_text))


def extract_value(value):
    if isinstance(value, list):
        return value[0] if value else None
    return value


class OauthProcess:
    def __init__(self, name: str, client_id: str = "", client_secret: str = "", authorize_url: str = "",
                 token_url: str = "", scope: str = "", local_port: int = 5333, device_code_url: str = ""):
        self.name = name
        self.local_port = local_port
        self.scope = scope
        self.client_id = client_id
        self.client_secret = client_secret
        self.authorize_url = authorize_url
        self.token_url = token_url
        self.redirect_uri = 'http://localhost:' + str(local_port) + '/callback'
        self.shutdown_event = Event()
        self.tokens = {}
        self.device_code_url = device_code_url

    def create_handler_constructor(self):
        def handler(*args, **kwargs):
            return Handler(*args, oauth_process=self, **kwargs)
        return handler

    def start_server(self, port: int = None):
        port = port or self.local_port
        with HTTPServer(("127.0.0.1", port), self.create_handler_constructor()) as server:
            server.serve_forever()

    def kill_server(self):
        pass

    def open_browser(self, port: int = None) -> bool:
        if DEACTIVATE_BROWSER_OPENING:
            return False
        port = port or self.local_port
        return webbrowser.open(f'http://localhost:{port}')

    def get_tokens_from_refresh_token(self, refresh_token: str) -> dict[str: str]:
        """Returns access and refresh token as dict using a refresh token"""
        oa_session = OAuth2Session(self.client_id, redirect_uri=self.redirect_uri, scope=self.scope)
        return oa_session.refresh_token(self.token_url, refresh_token=refresh_token, client_secret=self.client_secret,
                                        include_client_id=True, client_id=self.client_id)

    def get_tokens_from_auth_code(self, auth_code: str) -> dict[str: str]:
        """Returns access and refresh token as dict using an auth-code"""
        oa_session = OAuth2Session(self.client_id, redirect_uri=self.redirect_uri, scope=self.scope)
        return oa_session.fetch_token(self.token_url, client_secret=self.client_secret, include_client_id=True,
                                      code=auth_code)

    def get_tokens_from_device_flow(self) -> dict[str: str]:
        if self.device_code_url == "" or self.token_url == "":
            sc.echo(f"Device-Flow is not available for {self.name}")
            return {}
        sc.echo(f"Using Device-Flow to authorize with {self.name}")
        sc.echo(f"Device URL = {self.device_code_url}", debug=True)

        # Getting the device code
        data = {
            "client_id": self.client_id,
            "scope": self.scope
        }

        response = requests.post(self.device_code_url, data=data)
        if response.status_code != 200:
            sc.echo(f"Error while requesting device code: {response.status_code}. {response.text}")
            sc.debug_info(str(response.__dict__))
            return {}

        sc.debug_info(f"Response Text: {response.text}")

        response_data = parse_response_to_dict(response.text)

        device_code = extract_value(response_data['device_code'])
        user_code = extract_value(response_data['user_code'])
        verification_uri = extract_value(response_data['verification_uri'])
        verification_uri_complete = ""
        if 'verification_uri_complete' in response_data.keys():
            verification_uri_complete = extract_value(response_data['verification_uri_complete'])
        interval = float(extract_value(response_data['interval']))

        # User has to open the url and enter the code
        if verification_uri_complete:
            sc.echo(f"Open {verification_uri_complete} and confirm the code ({user_code})")
        else:
            sc.echo(f"Open {verification_uri} and enter this code: {user_code}")

        # Wait for the tokens
        while True:
            token_data = {
                "client_id": self.client_id,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
            }

            token_response = requests.post(self.token_url, data=token_data, headers={"Accept": "application/json"})
            token_response_data = token_response.json()

            if "access_token" in token_response_data:
                return token_response_data
            elif "error" in token_response_data and token_response_data["error"] != "authorization_pending":
                sc.echo(f"Error: {token_response_data['error']}")
                return {}

            time.sleep(interval)

    def get_tokens_from_oauth(self) -> dict[str: str]:
        if self.authorize_url == "":
            sc.echo(f"OAuth is not available for {self.name}")
            return {}
        sc.echo(f"Opening browser to log into your {self.name} account...")
        self.tokens = {}
        server_thread = threading.Thread(target=self.start_server)
        server_thread.daemon = True
        server_thread.start()
        time.sleep(.8)
        if self.open_browser():
            self.shutdown_event.wait()
        else:
            sc.echo("Browser can't be opened from this terminal.")
        self.kill_server()
        time.sleep(.2)
        return self.tokens

    def get_tokens(self) -> dict[str: str]:
        if PREFER_DEVICE_FLOW:
            return self.get_tokens_from_device_flow() or self.get_tokens_from_oauth() or {}
        else:
            return self.get_tokens_from_oauth() or self.get_tokens_from_device_flow() or {}


class Handler(BaseHTTPRequestHandler):
    def __init__(self, *args, oauth_process: OauthProcess = None, **kwargs):
        self.oauth_process = oauth_process
        super().__init__(*args, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        is_callback = parsed.path == "/callback"

        if is_callback:
            self.callback()
        else:
            self.index()

    def index(self):
        oa_session = OAuth2Session(self.oauth_process.client_id, scope=self.oauth_process.scope)
        authorization_url, state = oa_session.authorization_url(self.oauth_process.authorize_url)
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

        self.send_response(302)
        self.send_header("Location", authorization_url)
        self.end_headers()

    def callback(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")

        # Parse Query String
        parsed = urlparse(self.path)
        # print(parse_qs(parsed.query))
        auth_code = parse_qs(parsed.query)["code"][0]

        tokens = self.oauth_process.get_tokens_from_auth_code(auth_code)
        self.oauth_process.tokens = tokens
        self.oauth_process.shutdown_event.set()

        self.end_headers()
        self.wfile.write(b"You can close this window now.")

    def log_request(self, code="-", size="-"):
        pass
