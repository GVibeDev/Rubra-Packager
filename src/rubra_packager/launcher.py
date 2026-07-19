from __future__ import annotations

import ast
import json
from pathlib import Path


def launcher_source(config: dict[str, object]) -> str:
    config_literal = repr(json.dumps(config, ensure_ascii=False))
    source = f'''from __future__ import annotations
import hashlib
import json
import os
import sys
import threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import webview

CONFIG = json.loads({config_literal})
ROOT = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
WEB_ROOT = os.path.join(ROOT, "_web")

class QuietHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_ROOT, **kwargs)
    def log_message(self, format, *args):
        return

def create_server():
    seed = hashlib.sha256(CONFIG["appId"].encode("utf-8")).digest()
    preferred = 49152 + int.from_bytes(seed[:2], "big") % 12000
    last_error = None
    for offset in range(32):
        port = 49152 + ((preferred - 49152 + offset) % 12000)
        try:
            return ThreadingHTTPServer(("127.0.0.1", port), QuietHandler)
        except OSError as exc:
            last_error = exc
    raise RuntimeError(f"Could not reserve a stable local port: {{last_error}}")

def main():
    server = create_server()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    storage_root = os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), ".local", "share")
    storage_path = os.path.join(storage_root, CONFIG["storageName"], "webview")
    os.makedirs(storage_path, exist_ok=True)
    try:
        webview.create_window(
            CONFIG["title"],
            f"http://127.0.0.1:{{port}}/{{CONFIG['entryPoint']}}",
            width=int(CONFIG.get("width", 1280)),
            height=int(CONFIG.get("height", 800)),
            min_size=(960, 540),
            resizable=True,
            background_color="#071426",
        )
        webview.start(debug=False, private_mode=False, storage_path=storage_path)
    finally:
        server.shutdown()
        server.server_close()

if __name__ == "__main__":
    main()
'''
    ast.parse(source)
    return source


def write_launcher(path: Path, config: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(launcher_source(config), encoding="utf-8", newline="\n")
    return path
