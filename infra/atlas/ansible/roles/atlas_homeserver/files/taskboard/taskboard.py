#!/usr/bin/env python3
import base64
import hmac
import json
import mimetypes
import os
import re
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from taskboard_board import build_board
from taskboard_runtime import TaskCommandError
from taskboard_service import (
    TaskConflictError,
    add_task,
    bulk_update,
    create_dependency,
    delete_task,
    move_task,
    sync_and_board,
    update_task,
)
from taskboard_validation import env_bool

APP_NAME = "Sisyphus"
STATIC_DIR = Path(os.environ.get("TASKBOARD_STATIC_DIR", Path(__file__).with_name("static")))


def json_response(handler, status, payload):
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def text_response(handler, status, body, content_type="text/plain; charset=utf-8", write_body=True):
    encoded = body.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(encoded)))
    handler.end_headers()
    if write_body:
        handler.wfile.write(encoded)


def read_json(handler):
    length = int(handler.headers.get("Content-Length", "0") or "0")
    if length > 65536:
        raise ValueError("request body too large")
    if length == 0:
        return {}
    data = handler.rfile.read(length)
    return json.loads(data.decode("utf-8"))


def unauthorized(handler):
    handler.send_response(HTTPStatus.UNAUTHORIZED)
    handler.send_header("WWW-Authenticate", f'Basic realm="{APP_NAME}", charset="UTF-8"')
    handler.send_header("Content-Length", "0")
    handler.end_headers()


def is_authorized(handler):
    if env_bool("TASKBOARD_ALLOW_NO_AUTH", default=False):
        return True
    password = os.environ.get("TASKBOARD_PASSWORD", "")
    username = os.environ.get("TASKBOARD_USERNAME", "mbastakis")
    header = handler.headers.get("Authorization", "")
    if not header.startswith("Basic "):
        return False
    try:
        decoded = base64.b64decode(header[6:], validate=True).decode("utf-8")
    except Exception:
        return False
    supplied_username, sep, supplied_password = decoded.partition(":")
    if sep != ":":
        return False
    return hmac.compare_digest(supplied_username, username) and hmac.compare_digest(
        supplied_password, password
    )


def content_type_for(path):
    if path.name == "manifest.json":
        return "application/manifest+json; charset=utf-8"
    guess, _ = mimetypes.guess_type(str(path))
    if guess in {"text/html", "text/css", "application/javascript"}:
        return f"{guess}; charset=utf-8"
    return guess or "application/octet-stream"


def static_file_for_path(path):
    if path == "/":
        return STATIC_DIR / "index.html"
    if path == "/manifest.json":
        return STATIC_DIR / "manifest.json"
    if not path.startswith("/static/"):
        return None

    static_root = STATIC_DIR.resolve()
    candidate = (STATIC_DIR / unquote(path.removeprefix("/static/")).lstrip("/")).resolve()
    try:
        candidate.relative_to(static_root)
    except ValueError:
        return None
    return candidate


def static_response(handler, path, write_body=True):
    target = static_file_for_path(path)
    if target is None or not target.is_file():
        return False

    body = target.read_bytes()
    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", content_type_for(target))
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    if write_body:
        handler.wfile.write(body)
    return True


class TaskboardHandler(BaseHTTPRequestHandler):
    server_version = f"{APP_NAME}/0.1"

    def log_message(self, fmt, *args):
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        print(f"{timestamp} {self.address_string()} {fmt % args}", flush=True)

    def route_requires_auth(self):
        return urlparse(self.path).path not in {"/healthz", "/manifest.json"}

    def dispatch(self):
        if self.route_requires_auth() and not is_authorized(self):
            unauthorized(self)
            return

        parsed = urlparse(self.path)
        path = parsed.path
        if self.command == "GET" and path == "/healthz":
            text_response(self, HTTPStatus.OK, "ok\n")
        elif self.command == "GET" and static_response(self, path):
            return
        elif self.command == "GET" and path == "/api/board":
            json_response(self, HTTPStatus.OK, build_board(sync=True))
        elif self.command == "POST" and path == "/api/sync":
            json_response(self, HTTPStatus.OK, sync_and_board())
        elif self.command == "POST" and path == "/api/tasks":
            json_response(self, HTTPStatus.OK, add_task(read_json(self)))
        elif self.command == "POST" and path == "/api/tasks/bulk":
            json_response(self, HTTPStatus.OK, bulk_update(read_json(self)))
        elif self.command == "POST" and path.endswith("/dependencies"):
            match = re.match(r"^/api/tasks/([^/]+)/dependencies$", path)
            if not match:
                text_response(self, HTTPStatus.NOT_FOUND, "not found\n")
                return
            json_response(self, HTTPStatus.OK, create_dependency(match.group(1), read_json(self)))
        elif self.command == "POST" and path.endswith("/move"):
            match = re.match(r"^/api/tasks/([^/]+)/move$", path)
            if not match:
                text_response(self, HTTPStatus.NOT_FOUND, "not found\n")
                return
            payload = read_json(self)
            json_response(
                self,
                HTTPStatus.OK,
                move_task(match.group(1), payload.get("column", ""), payload),
            )
        elif self.command == "PATCH":
            match = re.match(r"^/api/tasks/([^/]+)$", path)
            if not match:
                text_response(self, HTTPStatus.NOT_FOUND, "not found\n")
                return
            json_response(self, HTTPStatus.OK, update_task(match.group(1), read_json(self)))
        elif self.command == "DELETE":
            match = re.match(r"^/api/tasks/([^/]+)$", path)
            if not match:
                text_response(self, HTTPStatus.NOT_FOUND, "not found\n")
                return
            json_response(self, HTTPStatus.OK, delete_task(match.group(1), read_json(self)))
        else:
            text_response(self, HTTPStatus.NOT_FOUND, "not found\n")

    def do_GET(self):
        self.safe_dispatch()

    def do_HEAD(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/healthz":
            text_response(self, HTTPStatus.OK, "ok\n", write_body=False)
            return
        if self.route_requires_auth() and not is_authorized(self):
            unauthorized(self)
            return
        if static_response(self, path, write_body=False):
            return
        text_response(self, HTTPStatus.NOT_FOUND, "not found\n", write_body=False)

    def do_POST(self):
        self.safe_dispatch()

    def do_PATCH(self):
        self.safe_dispatch()

    def do_DELETE(self):
        self.safe_dispatch()

    def safe_dispatch(self):
        try:
            self.dispatch()
        except (BrokenPipeError, ConnectionResetError):
            pass
        except json.JSONDecodeError:
            json_response(self, HTTPStatus.BAD_REQUEST, {"error": "invalid json"})
        except TaskConflictError as error:
            json_response(
                self,
                HTTPStatus.CONFLICT,
                {"error": str(error), "current_task": error.current_task},
            )
        except ValueError as error:
            json_response(self, HTTPStatus.BAD_REQUEST, {"error": str(error)})
        except TaskCommandError as error:
            json_response(
                self,
                HTTPStatus.BAD_GATEWAY,
                {
                    "error": str(error),
                    "task_stdout": error.stdout.strip(),
                    "task_stderr": error.stderr.strip(),
                },
            )


def main():
    if not env_bool("TASKBOARD_ALLOW_NO_AUTH", default=False) and not os.environ.get(
        "TASKBOARD_PASSWORD"
    ):
        raise SystemExit("TASKBOARD_PASSWORD is required unless TASKBOARD_ALLOW_NO_AUTH=1")
    host = os.environ.get("TASKBOARD_HOST", "0.0.0.0")
    port = int(os.environ.get("TASKBOARD_PORT", "8080"))
    server = ThreadingHTTPServer((host, port), TaskboardHandler)
    print(f"{APP_NAME.lower()} listening on {host}:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
