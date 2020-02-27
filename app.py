# -*- coding: utf-8 -*-
from flask import Flask, url_for, jsonify
from flask_oauthlib.client import OAuth, OAuthException

app = Flask(__name__)
app.config.from_object("default_settings")
app.config.from_pyfile("config.py", silent=True)

oauth = OAuth(app)
xero = oauth.remote_app(
    name="xero",
    consumer_key=app.config["CLIENT_ID"],
    consumer_secret=app.config["CLIENT_SECRET"],
    base_url="https://api.xero.com/",
    authorize_url="https://login.xero.com/identity/connect/authorize",
    access_token_url="https://identity.xero.com/connect/token",
)


@app.route("/")
def hello_world():
    # todo add index html page with links different endpoints in this app
    return "Hello World!"


@app.route("/login")
def login():
    params = {
        "scope": "openid profile email accounting.transactions",
        "state": "123",  # todo make it dynamic and pass it to callback
    }
    redirect_url = url_for("oauth_callback", _external=True)
    print(redirect_url)
    response = xero.authorize(callback=redirect_url, **params)
    print(response.headers["Location"])
    return response


@app.route("/callback")
def oauth_callback():
    try:
        response = xero.authorized_response()
    except OAuthException as e:
        print(e)
        raise
    # todo validate state value
    if response is None or response.get("access_token") is None:
        return "Access denied: response=%s" % response
    return jsonify(response)


if __name__ == "__main__":
    app.run()
