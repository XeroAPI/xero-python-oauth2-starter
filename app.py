# -*- coding: utf-8 -*-
from io import BytesIO

from flask import Flask, url_for, render_template, session, redirect, json, send_file
from flask_oauthlib.contrib.client import OAuth, OAuth2Application
from flask_session import Session

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
    import xero_python

    response = xero.get("/connections")
    available_tenants = response.json()

    configuration = xero_python.Configuration()
    configuration.client_id = app.config["CLIENT_ID"]
    configuration.client_secret = app.config["CLIENT_SECRET"]
    client = xero.make_client(obtain_xero_token())
    api_instance = xero_python.AccountingApi(
        xero_python.ApiClient(client, configuration)
    )

    for tenant in available_tenants:
        if tenant["tenantType"] == "ORGANISATION":
            response2 = api_instance.get_organisations(
                xero_tenant_id=tenant["tenantId"]
            )
            tenant["organisations"] = response2.to_dict()

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
