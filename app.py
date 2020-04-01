# -*- coding: utf-8 -*-
from io import BytesIO
from logging.config import dictConfig

from flask import Flask, url_for, render_template, session, redirect, json, send_file
from flask_oauthlib.contrib.client import OAuth, OAuth2Application
from flask_session import Session

import logging_settings

dictConfig(logging_settings.default_settings)


app = Flask(__name__)
app.config.from_object("default_settings")
app.config.from_pyfile("config.py", silent=True)

Session(app)

# TODO fetch config from https://identity.xero.com/.well-known/openid-configuration #1
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
    scope="offline_access openid profile email accounting.transactions "
    "accounting.transactions.read accounting.reports.read "
    "accounting.journals.read accounting.settings accounting.settings.read "
    "accounting.contacts accounting.contacts.read accounting.attachments "
    "accounting.attachments.read",
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


@app.route("/tenants")
def tenants():
    from xero_python.accounting import AccountingApi
    from xero_python.api_client import ApiClient
    from xero_python.api_client.oauth2 import OAuth2Token
    from xero_python.api_client.configuration import Configuration
    from xero_python.identity import IdentityApi

    xero_token = obtain_xero_token()
    if not xero_token:
        return redirect(url_for("login", _external=True))

    configuration = Configuration()
    configuration.debug = app.config["DEBUG"]
    configuration.oauth2_token = OAuth2Token(
        client_id=app.config["CLIENT_ID"],
        client_secret=app.config["CLIENT_SECRET"],
        **xero_token
    )
    api_client = ApiClient(configuration, pool_threads=1)
    identity_api = IdentityApi(api_client)
    accounting_api = AccountingApi(api_client)

    available_tenants = []
    for connection in identity_api.get_connections():
        tenant = connection.to_dict()
        if connection.tenant_type == "ORGANISATION":
            organisations = accounting_api.get_organisations(
                xero_tenant_id=connection.tenant_id
            )
            tenant["organisations"] = organisations.to_dict()

        available_tenants.append(tenant)

    return render_template(
        "tenants.html",
        title="Xero Tenants",
        tenants=json.dumps(available_tenants, sort_keys=True, indent=4),
    )


@app.route("/login")
def login():
    redirect_url = url_for("oauth_callback", _external=True)
    response = xero.authorize(callback_uri=redirect_url)
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
    store_xero_token(None)
    return redirect(url_for("index", _external=True))


@app.route("/export-token")
def export_token():
    token = obtain_xero_token()
    if not token:
        return redirect(url_for("index", _external=True))

    buffer = BytesIO("token={!r}".format(token).encode("utf-8"))
    buffer.seek(0)
    return send_file(
        buffer,
        mimetype="x.python",
        as_attachment=True,
        attachment_filename="oauth2_token.py",
    )


if __name__ == "__main__":
    app.run()
