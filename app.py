"""Cloud Café: a small, stateless Flask application for AWS lessons."""

import os
import socket

from flask import Flask, Response, make_response, render_template

from menu import get_menu

app = Flask(__name__)
app.config["DEBUG"] = False


@app.get("/")
def home():
    # SERVER_NAME is a display label, not Flask's SERVER_NAME routing setting.
    response = make_response(
        render_template(
            "index.html",
            menu=get_menu(),
            server_name=os.environ.get("SERVER_NAME") or socket.gethostname(),
            app_version=os.environ.get("APP_VERSION") or "1.0",
        )
    )
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.get("/health")
def health():
    # Keep this independent of the menu, templates, network, and any future database.
    return Response("OK", status=200, mimetype="text/plain")


if __name__ == "__main__":
    # Local preview only. The EC2 service runs Gunicorn instead.
    app.run(host="127.0.0.1", port=8080, debug=False, use_reloader=False)
