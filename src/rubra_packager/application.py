from __future__ import annotations

import argparse
import hmac
import json
import mimetypes
import os
import secrets
import sys
import threading
import traceback
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

import tkinter as tk
from tkinter import filedialog
import webview

from . import __version__
from .build_android import AndroidBuilder
from .build_windows import WindowsBuilder
from .config import APP_NAME, reports_dir
from .io_utils import atomic_write_json
from .models import ProjectRecord
from .preflight import run_preflight
from .profiles import ProfileRegistry
from .project_store import ProjectStore
from .security import ValidationError, require_existing_dir, safe_identifier
from .source import locate_static_output

STATIC_DIR = Path(__file__).resolve().parent / "static"


class Runtime:
    def __init__(self) -> None:
        self.token = secrets.token_urlsafe(32)
        self.store = ProjectStore()
        self.profiles = ProfileRegistry()
        self.window = None
        self.origin = ""

    def project_payload(self, record: ProjectRecord) -> dict[str, object]:
        payload = record.to_dict()
        payload["sourceExists"] = Path(record.source_path).is_dir()
        payload["staticReady"] = locate_static_output(Path(record.source_path)) is not None if payload["sourceExists"] else False
        return payload


class Handler(BaseHTTPRequestHandler):
    runtime: Runtime
    server_version = "RubraPackager/0.4"
    max_body = 72 * 1024 * 1024

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass

    def send_json(self, payload: object, status: int = 200) -> None:
        self._send(status, json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _authorized(self) -> bool:
        token = self.headers.get("X-RP-Token", "")
        if not hmac.compare_digest(token, self.runtime.token):
            self.send_json({"success": False, "error": "Unauthorized local request"}, 401)
            return False
        origin = self.headers.get("Origin")
        if origin and origin != self.runtime.origin:
            self.send_json({"success": False, "error": "Untrusted request origin"}, 403)
            return False
        return True

    def _body(self) -> dict[str, object]:
        raw_length = self.headers.get("Content-Length", "0")
        length = int(raw_length)
        if length < 0 or length > self.max_body:
            raise ValueError("Request body exceeds the local API limit")
        raw = self.rfile.read(length)
        if not raw:
            return {}
        value = json.loads(raw.decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("JSON body must be an object")
        return value

    def _serve_static(self, request_path: str) -> None:
        relative = "index.html" if request_path in {"/", "/index.html"} else request_path.lstrip("/")
        if relative not in {"index.html", "app.css", "app.js"}:
            self.send_error(404)
            return
        path = STATIC_DIR / relative
        if not path.is_file():
            self.send_error(404)
            return
        data = path.read_bytes()
        if relative == "index.html":
            data = data.replace(b"__RP_SESSION_TOKEN__", self.runtime.token.encode("ascii"))
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type in {"application/javascript"}:
            content_type += "; charset=utf-8"
        self._send(200, data, content_type)

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if not path.startswith("/api/"):
            self._serve_static(path)
            return
        if not self._authorized():
            return
        try:
            endpoint = path.removeprefix("/api/")
            if endpoint == "health":
                self.send_json({"success": True, "version": __version__, "python": sys.version.split()[0]})
            elif endpoint == "projects":
                self.send_json({"success": True, "projects": [self.runtime.project_payload(item) for item in self.runtime.store.list()]})
            elif endpoint == "profiles":
                profiles = []
                for profile in self.runtime.profiles.list():
                    profiles.append({
                        "id": profile.profile_id,
                        "label": profile.label,
                        "description": profile.description,
                        "entryPoint": profile.entry_point,
                        "orientation": profile.orientation,
                        "defaultVariant": profile.default_variant,
                        "variants": [asdict(item) for item in profile.variants],
                    })
                self.send_json({"success": True, "profiles": profiles})
            elif endpoint == "android/prerequisites":
                self.send_json({"success": True, "prerequisites": AndroidBuilder.prerequisites()})
            else:
                self.send_json({"success": False, "error": "Unknown endpoint"}, 404)
        except Exception as exc:
            self.send_json({"success": False, "error": str(exc)}, 500)

    def do_POST(self) -> None:
        path = urlsplit(self.path).path
        if not path.startswith("/api/"):
            self.send_error(404)
            return
        if not self._authorized():
            return
        try:
            data = self._body()
            endpoint = path.removeprefix("/api/")
            if endpoint == "dialog/folder":
                root = tk.Tk()
                root.withdraw()
                root.attributes("-topmost", True)
                selected = filedialog.askdirectory(title="Choose a web project folder", initialdir=str(Path.home()))
                root.destroy()
                self.send_json({"success": bool(selected), "path": selected})
                return
            if endpoint == "projects/import":
                source = require_existing_dir(str(data.get("sourcePath", "")), "project source")
                project_id = safe_identifier(str(data.get("projectId", source.name)), "project id")
                profile_id = str(data.get("profileId", "generic-web-game"))
                self.runtime.profiles.get(profile_id)
                record = self.runtime.store.upsert(ProjectRecord(
                    project_id=project_id,
                    name=str(data.get("name", source.name)).strip() or source.name,
                    source_path=str(source),
                    description=str(data.get("description", "")),
                    author=str(data.get("author", "")),
                    version=str(data.get("version", "1.0.0")),
                    profile_id=profile_id,
                ))
                self.send_json({"success": True, "project": self.runtime.project_payload(record)})
                return
            if endpoint == "projects/delete":
                changed = self.runtime.store.delete(str(data.get("projectId", "")))
                self.send_json({"success": True, "deleted": changed})
                return
            if endpoint == "projects/import-legacy":
                imported = self.runtime.store.import_legacy()
                self.send_json({"success": True, "imported": imported})
                return
            if endpoint == "preflight":
                project = self.runtime.store.get(str(data.get("projectId", "")))
                profile = self.runtime.profiles.get(str(data.get("profileId", project.profile_id)))
                source = locate_static_output(Path(project.source_path)) or Path(project.source_path)
                report = run_preflight(source, profile, str(data.get("variantId", profile.default_variant)))
                report_path = reports_dir() / f"{project.project_id}-{profile.profile_id}-{report.variant_id}.json"
                atomic_write_json(report_path, report.to_dict())
                self.send_json({"success": True, "report": report.to_dict(), "reportPath": str(report_path)})
                return
            if endpoint == "build/windows":
                project = self.runtime.store.get(str(data.get("projectId", "")))
                profile = self.runtime.profiles.get(str(data.get("profileId", project.profile_id)))
                result = WindowsBuilder().build(
                    project_root=Path(project.source_path),
                    app_name=str(data.get("appName", project.name)),
                    profile=profile,
                    variant_id=str(data.get("variantId", profile.default_variant)),
                    icon_data=str(data.get("iconData")) if data.get("iconData") else None,
                    allow_source_build=bool(data.get("allowSourceBuild", False)),
                )
                self.send_json(result, 200 if result.get("success") else 500)
                return
            if endpoint == "build/android":
                project = self.runtime.store.get(str(data.get("projectId", "")))
                profile = self.runtime.profiles.get(str(data.get("profileId", project.profile_id)))
                result = AndroidBuilder().build(
                    project_root=Path(project.source_path),
                    app_name=str(data.get("appName", project.name)),
                    package_name=str(data.get("packageName", "com.example.app")),
                    profile=profile,
                    variant_id=str(data.get("variantId", profile.default_variant)),
                    icon_data=str(data.get("iconData")) if data.get("iconData") else None,
                    icon_background=str(data.get("iconBackground", "#071426")),
                    allow_source_build=bool(data.get("allowSourceBuild", False)),
                )
                self.send_json(result, 200 if result.get("success") else 500)
                return
            self.send_json({"success": False, "error": "Unknown endpoint"}, 404)
        except (ValidationError, ValueError, KeyError) as exc:
            self.send_json({"success": False, "error": str(exc)}, 400)
        except Exception as exc:
            traceback.print_exc()
            self.send_json({"success": False, "error": str(exc)}, 500)


def launch(port: int = 0) -> None:
    runtime = Runtime()
    Handler.runtime = runtime
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    runtime.origin = f"http://127.0.0.1:{server.server_address[1]}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        runtime.window = webview.create_window(
            APP_NAME,
            runtime.origin,
            width=1380,
            height=860,
            min_size=(1040, 680),
            resizable=True,
            background_color="#071426",
        )
        webview.start(debug=False)
    finally:
        server.shutdown()
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description=APP_NAME)
    parser.add_argument("--port", type=int, default=0, help="Local UI port; 0 chooses an available port")
    args = parser.parse_args()
    launch(args.port)
