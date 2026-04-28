"""
Local onboarding wizard server.

Run from the repository root:
    python agents/debrief/src/onboarding.py
    python agents/debrief/src/onboarding.py --tenant aerocore

This is intentionally small and file-backed. In Corvus Cloud, the request's
authenticated tenant can replace the CLI tenant slug while the UI contract stays
the same: GET/POST /api/onboarding.
"""

import argparse
import json
import os
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import yaml

_THIS_FILE = os.path.abspath(__file__)
_SRC_DIR = os.path.dirname(_THIS_FILE)
_AGENT_ROOT = os.path.dirname(_SRC_DIR)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_AGENT_ROOT))
_SHARED_DIR = os.path.join(_PROJECT_ROOT, "shared")

sys.path.insert(0, _SRC_DIR)
sys.path.insert(0, _SHARED_DIR)
sys.path.insert(0, _PROJECT_ROOT)

from utils.tenants import get_tenant_context

UI_PATH = Path(_PROJECT_ROOT) / "docs" / "onboarding-ui.html"
DEFAULT_ONBOARDING_PATH = Path(_AGENT_ROOT) / "config" / "onboarding.yaml"
ONBOARDING_FIELDS = {
    "schema_version",
    "company",
    "site",
    "timezone",
    "manufacturing_type",
    "terminology",
    "thresholds",
    "shifts",
    "teams",
}


def read_yaml(path: Path) -> dict:
    if not path.exists():
        return {"schema_version": "1.0", "company": "", "site": "", "teams": []}
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Onboarding YAML must be a mapping: {path}")
    return data


def write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)


def merge_onboarding(existing: dict, incoming: dict) -> dict:
    """
    Update wizard-owned onboarding fields while preserving connector data.
    CSV/schema mappings belong to a separate future data-source flow.
    """
    merged = dict(existing)
    for field in ONBOARDING_FIELDS:
        if field in incoming:
            merged[field] = incoming[field]
    merged.setdefault("schema_version", "1.0")
    return merged


def resolve_onboarding_path(args) -> tuple[Path, str | None]:
    if args.tenant:
        context = get_tenant_context(args.tenant)
        return Path(context["onboarding_path"]), context["slug"]
    if args.onboarding:
        return Path(args.onboarding).expanduser().resolve(), None
    return DEFAULT_ONBOARDING_PATH, None


def make_handler(onboarding_path: Path, tenant: str | None):
    class OnboardingHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            route = urlparse(self.path).path
            if route in ("/", "/onboarding-ui.html"):
                return self.send_ui()
            if route == "/api/onboarding":
                return self.send_onboarding()
            self.send_error(404, "Not found")

        def do_POST(self):
            route = urlparse(self.path).path
            if route == "/api/onboarding":
                return self.save_onboarding()
            self.send_error(404, "Not found")

        def log_message(self, format, *args):
            print(
                f"[CORVUS ONBOARDING] {self.address_string()} - {format % args}",
                flush=True,
            )

        def send_json(self, payload: dict, status: int = 200):
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def send_ui(self):
            body = UI_PATH.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def send_onboarding(self):
            try:
                data = read_yaml(onboarding_path)
                self.send_json({
                    "tenant": tenant,
                    "path": str(onboarding_path),
                    "data": data,
                })
            except Exception as exc:
                self.send_json({"error": str(exc)}, status=500)

        def save_onboarding(self):
            try:
                length = int(self.headers.get("Content-Length", "0"))
                incoming = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(incoming, dict):
                    raise ValueError("Request body must be a JSON object.")
                existing = read_yaml(onboarding_path)
                merged = merge_onboarding(existing, incoming)
                write_yaml(onboarding_path, merged)
                self.send_json({
                    "tenant": tenant,
                    "path": str(onboarding_path),
                    "data": merged,
                })
            except Exception as exc:
                self.send_json({"error": str(exc)}, status=400)

    return OnboardingHandler


def parse_args():
    parser = argparse.ArgumentParser(description="Launch Corvus onboarding wizard")
    parser.add_argument("--tenant", help="Tenant slug under shared/tenants/<tenant>")
    parser.add_argument("--onboarding", help="Explicit onboarding.yaml path")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-open", action="store_true", help="Do not open a browser")
    return parser.parse_args()


def main():
    args = parse_args()
    onboarding_path, tenant = resolve_onboarding_path(args)
    handler = make_handler(onboarding_path, tenant)
    server = ThreadingHTTPServer((args.host, args.port), handler)
    url = f"http://{args.host}:{args.port}/"

    print("[CORVUS ONBOARDING] Serving wizard", flush=True)
    print(f"[CORVUS ONBOARDING] URL: {url}", flush=True)
    print(f"[CORVUS ONBOARDING] Target: {onboarding_path}", flush=True)
    if tenant:
        print(f"[CORVUS ONBOARDING] Tenant: {tenant}", flush=True)
    print("[CORVUS ONBOARDING] Press Ctrl+C to stop", flush=True)

    if not args.no_open:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[CORVUS ONBOARDING] Stopped", flush=True)
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
