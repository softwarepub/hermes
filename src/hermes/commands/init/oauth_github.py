import os
import webbrowser
from flask import Flask, request, redirect
from requests_oauthlib import OAuth2Session
from threading import Timer, Thread, Event
from waitress import serve

local_port = 8333
client_id = 'Ov23ctl0gNzr9smeVIHR'
client_secret = 'd516303374f7e55189fe74fb2af77f31a965ad57'
authorization_base_url = 'https://github.com/login/oauth/authorize'
token_url = 'https://github.com/login/oauth/access_token'
redirect_uri = 'http://localhost:' + str(local_port) + '/callback'
scope = "repo"

app = Flask(__name__)
shutdown_event = Event()

@app.route("/")
def index():
    github = OAuth2Session(client_id, scope=scope)
    authorization_url, state = github.authorization_url(authorization_base_url)

    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
    return redirect(authorization_url)


@app.route("/callback")
def callback():
    github = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope)
    token = github.fetch_token(token_url, client_secret=client_secret,
                               authorization_response=request.url)

    os.environ['GITHUB_TOKEN'] = token['access_token']

    shutdown_event.set()

    return "You have successfully logged in with GitHub! You can close this window now."


def open_browser():
    webbrowser.open(f"http://localhost:{local_port}")


def run_flask():
    serve(app, host='0.0.0.0', port=local_port)


def kill_flask_thread(flask_thread: Thread):
    flask_thread.join(timeout=2)


def start_oauth():
    """Starts the oauth procedure and saves collected tokens in env variables"""
    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    Timer(1, open_browser).start()

    shutdown_event.wait()
    kill_flask_thread(flask_thread)

    token = os.environ.get('GITHUB_TOKEN')
    if token:
        print("Access Token:", token)
    else:
        print("No token collected")


if __name__ == "__main__":
    start_oauth()

