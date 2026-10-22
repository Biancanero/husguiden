"""Minimal internal customer portal with no application dependencies."""

from __future__ import annotations

import base64
import binascii
import hmac
import html
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server
from socketserver import ThreadingMixIn


DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))
DB_PATH = DATA_DIR / "portal.sqlite3"
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")


def db() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialise() -> None:
    if not ADMIN_PASSWORD:
        raise RuntimeError("ADMIN_PASSWORD must be set")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with db() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS assets (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              kind TEXT NOT NULL CHECK(kind IN ('house', 'car')),
              name TEXT NOT NULL,
              location TEXT NOT NULL DEFAULT '',
              detail TEXT NOT NULL DEFAULT '',
              notes TEXT NOT NULL DEFAULT '',
              created_at TEXT NOT NULL
            )
            """
        )


def authorised(environ: dict) -> bool:
    header = environ.get("HTTP_AUTHORIZATION", "")
    if not header.startswith("Basic "):
        return False
    try:
        supplied = base64.b64decode(header[6:], validate=True).decode("utf-8")
        user, password = supplied.split(":", 1)
    except (ValueError, UnicodeDecodeError, binascii.Error):
        return False
    return hmac.compare_digest(user, ADMIN_USER) and hmac.compare_digest(password, ADMIN_PASSWORD)


def response(start_response, status: str, body: str = "", headers: list[tuple[str, str]] | None = None):
    encoded = body.encode("utf-8")
    standard = [
        ("Content-Type", "text/html; charset=utf-8"),
        ("Content-Length", str(len(encoded))),
        ("Cache-Control", "no-store"),
        ("X-Content-Type-Options", "nosniff"),
        ("X-Frame-Options", "DENY"),
        ("Referrer-Policy", "no-referrer"),
    ]
    start_response(status, standard + (headers or []))
    return [encoded]


def redirect(start_response, location: str):
    return response(start_response, "303 See Other", "", [("Location", location)])


def page(title: str, content: str) -> str:
    return f"""<!doctype html>
<html lang="sv"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · Kundportal</title><style>
:root {{ color-scheme: dark; --bg:#151716; --card:#20231f; --ink:#eef1eb; --muted:#aeb4aa; --line:#3a4038; --accent:#a8c99f; --danger:#eea09a; }}
* {{ box-sizing:border-box }} body {{ margin:0; background:var(--bg); color:var(--ink); font:16px/1.5 system-ui,sans-serif }}
main {{ max-width:980px; margin:auto; padding:38px 20px 80px }} header {{ display:flex; justify-content:space-between; gap:18px; align-items:end; flex-wrap:wrap; border-bottom:1px solid var(--line); padding-bottom:22px }}
h1,h2 {{ margin:0; line-height:1.15 }} h1 {{ font-size:clamp(28px,5vw,46px) }} h2 {{ font-size:20px }} p {{ color:var(--muted) }}
.actions,.types {{ display:flex; flex-wrap:wrap; gap:10px }} a.btn,button {{ background:var(--accent); color:#172116; border:0; padding:10px 14px; font:600 14px system-ui,sans-serif; text-decoration:none; cursor:pointer }}
a.btn.alt {{ background:transparent; color:var(--ink); border:1px solid var(--line) }} .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:14px; margin-top:26px }}
.card,form {{ border:1px solid var(--line); background:var(--card); padding:18px }} .card header {{ border:0; padding:0; align-items:start }} .meta {{ color:var(--muted); font-size:14px; margin:9px 0 }}
.tag {{ color:var(--accent); font-size:12px; letter-spacing:.11em; text-transform:uppercase }} label {{ display:grid; gap:5px; margin-top:14px; color:var(--muted); font-size:14px }} input,textarea,select {{ width:100%; padding:10px; background:#151716; color:var(--ink); border:1px solid var(--line); font:inherit }} textarea {{ min-height:110px; resize:vertical }}
.danger {{ background:transparent; color:var(--danger); padding:0; font-size:13px }} .empty {{ border:1px dashed var(--line); padding:28px; margin-top:26px; color:var(--muted) }}
</style></head><body><main>{content}</main></body></html>"""


def dashboard() -> str:
    with db() as connection:
        assets = connection.execute("SELECT * FROM assets ORDER BY created_at DESC, id DESC").fetchall()
    cards = []
    for asset in assets:
        label = "Hus" if asset["kind"] == "house" else "Bil"
        cards.append(
            f"<article class='card'><header><div><div class='tag'>{label}</div><h2>{html.escape(asset['name'])}</h2></div>"
            f"<form method='post' action='/assets/{asset['id']}/delete'><button class='danger'>Ta bort</button></form></header>"
            f"<div class='meta'>{html.escape(asset['location'])}</div><div class='meta'>{html.escape(asset['detail'])}</div>"
            f"<p>{html.escape(asset['notes']).replace(chr(10), '<br>')}</p></article>"
        )
    body = "<div class='grid'>" + "".join(cards) + "</div>" if cards else "<div class='empty'>Inga hus eller bilar är tillagda ännu.</div>"
    return page(
        "Översikt",
        "<header><div><div class='tag'>Kundportal</div><h1>Hus & bilar</h1><p>En privat översikt för kundens objekt.</p></div>"
        "<div class='actions'><a class='btn alt' href='/new?kind=house'>+ Hus</a><a class='btn' href='/new?kind=car'>+ Bil</a></div></header>" + body,
    )


def new_asset(kind: str) -> str:
    if kind not in {"house", "car"}:
        kind = "house"
    label = "hus" if kind == "house" else "bil"
    location = "Adress" if kind == "house" else "Registreringsnummer"
    detail = "Fastighetsbeteckning / typ" if kind == "house" else "Märke, modell och årsmodell"
    return page(
        f"Nytt {label}",
        f"<header><div><div class='tag'>Nytt objekt</div><h1>Lägg till {label}</h1></div><a class='btn alt' href='/'>Avbryt</a></header>"
        f"<form method='post' action='/assets'><input type='hidden' name='kind' value='{kind}'>"
        "<label>Namn<input name='name' required maxlength='120' placeholder='Exempel: Sommarhuset'></label>"
        f"<label>{location}<input name='location' maxlength='160'></label>"
        f"<label>{detail}<input name='detail' maxlength='200'></label>"
        "<label>Anteckningar<textarea name='notes' maxlength='4000'></textarea></label>"
        "<div class='actions' style='margin-top:18px'><button>Spara objekt</button></div></form>",
    )


def app(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    if path == "/health":
        return response(start_response, "200 OK", "ok", [("Content-Type", "text/plain; charset=utf-8")])
    if not authorised(environ):
        return response(start_response, "401 Unauthorized", "Inloggning krävs.", [("WWW-Authenticate", 'Basic realm="Kundportal", charset="UTF-8"')])
    if method == "GET" and path == "/":
        return response(start_response, "200 OK", dashboard())
    if method == "GET" and path == "/new":
        kind = parse_qs(environ.get("QUERY_STRING", "")).get("kind", ["house"])[0]
        return response(start_response, "200 OK", new_asset(kind))
    if method == "POST" and path == "/assets":
        length = int(environ.get("CONTENT_LENGTH") or 0)
        fields = parse_qs(environ["wsgi.input"].read(length).decode("utf-8"), keep_blank_values=True)
        kind = fields.get("kind", [""])[0]
        name = fields.get("name", [""])[0].strip()
        if kind not in {"house", "car"} or not name:
            return response(start_response, "400 Bad Request", page("Ogiltigt objekt", "<h1>Fyll i namn och objekttyp.</h1>"))
        values = [fields.get(key, [""])[0].strip() for key in ("location", "detail", "notes")]
        with db() as connection:
            connection.execute(
                "INSERT INTO assets(kind,name,location,detail,notes,created_at) VALUES(?,?,?,?,?,?)",
                (kind, name, *values, datetime.now(timezone.utc).isoformat()),
            )
        return redirect(start_response, "/")
    if method == "POST" and path.startswith("/assets/") and path.endswith("/delete"):
        try:
            asset_id = int(path.split("/")[2])
        except (IndexError, ValueError):
            return response(start_response, "404 Not Found", page("Saknas", "<h1>Objektet hittades inte.</h1>"))
        with db() as connection:
            connection.execute("DELETE FROM assets WHERE id = ?", (asset_id,))
        return redirect(start_response, "/")
    return response(start_response, "404 Not Found", page("Saknas", "<h1>Sidan hittades inte.</h1>"))


class ThreadingServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True


class QuietHandler(WSGIRequestHandler):
    def log_message(self, *_args):
        pass


if __name__ == "__main__":
    initialise()
    with make_server("0.0.0.0", 8080, app, server_class=ThreadingServer, handler_class=QuietHandler) as server:
        server.serve_forever()
