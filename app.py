# -*- coding: utf-8 -*-
import json

from flask import Flask, url_for, render_template, session, redirect
from flask_oauthlib.contrib.client import OAuth, OAuth2Application
from flask_session import Session

app = Flask(__name__)
app.config.from_object("default_settings")
app.config.from_pyfile("config.py", silent=True)

Session(app)

oauth = OAuth(app)
xero = oauth.remote_app(
    name="xero",
    version="2",
    client_id=app.config["CLIENT_ID"],
    client_secret=app.config["CLIENT_SECRET"],
    endpoint_url="https://api.xero.com/",
    authorization_url="https://login.xero.com/identity/connect/authorize",
    access_token_url="https://identity.xero.com/connect/token",
    refresh_token_url="https://identity.xero.com/connect/token",
    scope="offline_access openid profile email accounting.transactions",
)  # type: OAuth2Application


@xero.tokengetter
def obtain_xero_token():
    return session.get("token")


@xero.tokensaver
def store_xero_token(token):
    session["token"] = token
    session.modified = True


@app.route("/")
def index():
    xero_access = dict(obtain_xero_token() or {})
    return render_template(
        "index.html",
        title="Home",
        token=json.dumps(xero_access, sort_keys=True, indent=4),
    )


@app.route("/connections")
def tenants():
    response = xero.get("/connections")
    return render_template(
        "tenants.html",
        title="Xero Tenants",
        tenants=json.dumps(response.json(), sort_keys=True, indent=4),
    )


@app.route("/login")
def login():
    params = {
        "scope": "openid profile email accounting.transactions",
        "state": "123",  # todo make it dynamic and pass it to callback
    }
    redirect_url = url_for("oauth_callback", _external=True)
    print(redirect_url)
    response = xero.authorize(callback_uri=redirect_url)
    print(response.headers["Location"])
    return response


@app.route("/callback")
def oauth_callback():
    try:
        response = xero.authorized_response()
    except Exception as e:
        print(e)
        raise
    # todo validate state value
    if response is None or response.get("access_token") is None:
        return "Access denied: response=%s" % response
    store_xero_token(response)
    return redirect(url_for("index", _external=True))


@app.route("/logout")
def logout():
    session["xero_access"] = None
    session.modified = True
    return redirect(url_for("index", _external=True))


@app.route("/refresh_token")
def oauth_refresh_token():
    try:
        result = xero.generate_request_token()
    except Exception as e:
        print(e)
        raise
    session["xero_refresh"] = result
    session.modified = True
    return redirect(url_for("index", _external=True))


if __name__ == "__main__":
    app.run()
