# SPDX-FileCopyrightText: 2024 Forschungszentrum Jülich
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileContributor: Nitai Heeb
# SPDX-FileContributor: David Pape

import os
import threading
import time
import webbrowser
from threading import Event
from requests_oauthlib import OAuth2Session
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse


class OauthProcess:
    def __init__(self, client_id: str, client_secret: str, authorize_url: str, token_url: str, scope: str,
                 local_port: int = 5333):
        self.local_port = local_port
        self.scope = scope
        self.client_id = client_id
        self.client_secret = client_secret
        self.authorize_url = authorize_url
        self.token_url = token_url
        self.redirect_uri = 'http://localhost:' + str(local_port) + '/callback'
        self.shutdown_event = Event()
        self.tokens = {}

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

    def get_tokens(self) -> dict[str: str]:
        server_thread = threading.Thread(target=self.start_server)
        server_thread.daemon = True
        server_thread.start()
        time.sleep(.8)
        if self.open_browser():
            self.shutdown_event.wait()
        self.kill_server()
        time.sleep(.2)
        return self.tokens


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
