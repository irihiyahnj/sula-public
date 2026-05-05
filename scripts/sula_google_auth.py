#!/usr/bin/env python3

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import secrets
import threading
import webbrowser
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib import parse, request

from sula_providers.google_oauth_store import DEFAULT_GOOGLE_OAUTH_FILE, project_google_oauth_file, write_google_oauth_store


DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/drive.metadata.readonly",
    "https://www.googleapis.com/auth/documents.readonly",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Obtain and store Google OAuth tokens for Sula provider refresh.")
    parser.add_argument("--client-secrets-file", required=True, help="Path to a Google Desktop OAuth client JSON file.")
    parser.add_argument("--project-root", help="Optional Sula project root; defaults the OAuth store to PROJECT/.sula/local/google-oauth.json.")
    parser.add_argument("--output", help="Where to write the local OAuth token store. Overrides --project-root.")
    parser.add_argument("--scope", action="append", default=[], help="OAuth scope to request. Repeat for multiple scopes.")
    parser.add_argument("--timeout-seconds", type=int, default=300, help="How long to wait for the browser callback.")
    parser.add_argument("--no-open-browser", action="store_true", help="Do not try to open the system browser automatically.")
    parser.add_argument("--print-shell", action="store_true", help="Print shell exports after success.")
    return parser.parse_args()


def resolve_output_path(args: argparse.Namespace) -> Path:
    if args.output:
        return Path(args.output).expanduser()
    if args.project_root:
        return project_google_oauth_file(Path(args.project_root).expanduser())
    return DEFAULT_GOOGLE_OAUTH_FILE


def load_client_config(path: Path) -> dict[str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        root = payload.get("installed") or payload.get("web") or payload
        if isinstance(root, dict):
            return {
                "client_id": str(root.get("client_id", "") or "").strip(),
                "client_secret": str(root.get("client_secret", "") or "").strip(),
                "auth_uri": str(root.get("auth_uri", "https://accounts.google.com/o/oauth2/v2/auth") or "").strip(),
                "token_uri": str(root.get("token_uri", "https://oauth2.googleapis.com/token") or "").strip(),
            }
    raise SystemExit(f"Invalid client secrets JSON: {path}")


def code_verifier() -> str:
    return secrets.token_urlsafe(64).rstrip("=")


def code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


class OAuthCallbackServer(HTTPServer):
    authorization_code: str | None = None
    error_value: str | None = None
    event: threading.Event


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = parse.urlparse(self.path)
        params = parse.parse_qs(parsed.query)
        server = self.server
        assert isinstance(server, OAuthCallbackServer)
        if "error" in params:
            server.error_value = params["error"][0]
        if "code" in params:
            server.authorization_code = params["code"][0]
        server.event.set()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            b"<html><body><h1>Sula Google OAuth complete</h1><p>You can close this window and return to the terminal.</p></body></html>"
        )

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


def start_callback_server() -> tuple[OAuthCallbackServer, str]:
    event = threading.Event()
    server = OAuthCallbackServer(("127.0.0.1", 0), OAuthCallbackHandler)
    server.event = event
    redirect_uri = f"http://127.0.0.1:{server.server_port}/oauth2callback"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, redirect_uri


def exchange_code_for_tokens(
    *,
    token_uri: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    code: str,
    verifier: str,
) -> dict[str, object]:
    form = {
        "client_id": client_id,
        "code": code,
        "code_verifier": verifier,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }
    if client_secret:
        form["client_secret"] = client_secret
    data = parse.urlencode(form).encode("utf-8")
    req = request.Request(token_uri, data=data, headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"})
    with request.urlopen(req, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict) or not payload.get("access_token") or not payload.get("refresh_token"):
        raise SystemExit("Google token exchange did not return both access_token and refresh_token.")
    return payload


def main() -> int:
    args = parse_args()
    client_config = load_client_config(Path(args.client_secrets_file).expanduser())
    if not client_config["client_id"]:
        raise SystemExit("Client secrets file does not contain `client_id`.")
    scopes = args.scope or list(DEFAULT_SCOPES)
    verifier = code_verifier()
    challenge = code_challenge(verifier)
    server, redirect_uri = start_callback_server()
    query = {
        "client_id": client_config["client_id"],
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes),
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = f"{client_config['auth_uri']}?{parse.urlencode(query)}"
    print("Open this URL and complete Google consent:")
    print(auth_url)
    if not args.no_open_browser:
        webbrowser.open(auth_url)
    if not server.event.wait(timeout=args.timeout_seconds):
        server.shutdown()
        raise SystemExit("Timed out waiting for Google OAuth callback.")
    server.shutdown()
    if server.error_value:
        raise SystemExit(f"Google OAuth failed: {server.error_value}")
    if not server.authorization_code:
        raise SystemExit("Google OAuth callback did not include an authorization code.")
    token_payload = exchange_code_for_tokens(
        token_uri=client_config["token_uri"],
        client_id=client_config["client_id"],
        client_secret=client_config["client_secret"],
        redirect_uri=redirect_uri,
        code=server.authorization_code,
        verifier=verifier,
    )
    expires_in = int(token_payload.get("expires_in", 0) or 0)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    store = {
        "provider": "google-drive",
        "client_id": client_config["client_id"],
        "client_secret": client_config["client_secret"],
        "auth_uri": client_config["auth_uri"],
        "token_uri": client_config["token_uri"],
        "scope": str(token_payload.get("scope", " ".join(scopes))),
        "token_type": str(token_payload.get("token_type", "Bearer")),
        "access_token": str(token_payload["access_token"]),
        "refresh_token": str(token_payload["refresh_token"]),
        "access_token_issued_at": now.isoformat().replace("+00:00", "Z"),
        "access_token_expires_at": (now + timedelta(seconds=expires_in)).isoformat().replace("+00:00", "Z"),
        "issued_via": "sula_google_auth_loopback_pkce",
    }
    output_path = write_google_oauth_store(store, resolve_output_path(args))
    print(f"Wrote Google OAuth store to {output_path}")
    if args.print_shell:
        print(f'export SULA_GOOGLE_OAUTH_FILE="{output_path}"')
        print(f'export SULA_GOOGLE_ACCESS_TOKEN="{store["access_token"]}"')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
