import os
import re
import webbrowser
from flask import Flask, request, redirect
from requests_oauthlib import OAuth2Session
from threading import Timer, Thread, Event
from waitress import serve
import logging

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

app = Flask(__name__)
shutdown_event = Event()

@app.route("/")
def index():
    zenodo = OAuth2Session(client_id, scope=scope)
    authorization_url, state = zenodo.authorization_url(authorize_url)
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
    return redirect(authorization_url)


@app.route("/callback")
def callback():
    auth_code = re.search('code=([^&\\s]*).*$', str(request.query_string)).group(1)
    get_token_from_auth_code(auth_code)
    shutdown_event.set()
    # shutdown_func = request.environ.get('werkzeug.server.shutdown')
    # if shutdown_func is None:
    #     raise RuntimeError('Not running with the Werkzeug Server')
    # shutdown_func()
    return "You have successfully logged in with Zenodo! You can close this window now."


def open_browser():
    webbrowser.open(f"http://localhost:{local_port}")


def run_flask():
    serve(app, host='0.0.0.0', port=local_port)


def kill_flask_thread(flask_thread: Thread):
    flask_thread.join(timeout=2)


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


def start_oauth():
    """Starts the oauth procedure and saves collected tokens in env variables"""
    #print_logs_for_requests()

    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    Timer(1, open_browser).start()

    shutdown_event.wait()
    kill_flask_thread(flask_thread)

    token = os.environ.get('ZENODO_TOKEN')
    if token:
        print("Access Token:", token)
    else:
        print("No token collected")

    refresh_token = os.environ.get('ZENODO_TOKEN_REFRESH')
    if token:
        print("Refresh Token:", refresh_token)
    else:
        print("No refresh token collected")


def get_token_from_refresh_token(refresh_token):
    """Gets access and refresh token using a refresh token and saves those in env variables"""
    zenodo_session = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope)
    token = zenodo_session.refresh_token(token_url, refresh_token=refresh_token, client_secret=client_secret,
                                 include_client_id=True, client_id=client_id)
    os.environ['ZENODO_TOKEN'] = token['access_token']
    os.environ['ZENODO_TOKEN_REFRESH'] = token['refresh_token']


def get_token_from_auth_code(auth_code):
    """Gets access and refresh token using an auth-code and saves those in env variables"""
    zenodo_session = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope)
    token = zenodo_session.fetch_token(token_url, client_secret=client_secret, include_client_id=True,
                               authorization_response=request.url, code=auth_code)
    os.environ['ZENODO_TOKEN'] = token['access_token']
    os.environ['ZENODO_TOKEN_REFRESH'] = token['refresh_token']


if __name__ == "__main__":
    start_oauth()

