from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib import error, parse, request

from .base import ProviderAdapterError


DEFAULT_GOOGLE_OAUTH_FILE = Path.home() / ".config" / "sula" / "google-oauth.json"
PROJECT_LOCAL_GOOGLE_OAUTH_FILE = Path(".sula") / "local" / "google-oauth.json"


def current_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_optional_timestamp(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    candidate = text.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(candidate)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def default_google_oauth_file() -> Path:
    raw = os.environ.get("SULA_GOOGLE_OAUTH_FILE", "").strip()
    if raw:
        return Path(raw).expanduser()
    return DEFAULT_GOOGLE_OAUTH_FILE


def project_google_oauth_file(project_root: Path) -> Path:
    return project_root.resolve() / PROJECT_LOCAL_GOOGLE_OAUTH_FILE


def load_google_oauth_store(path: Path | None = None, *, fallback_paths: list[Path] | None = None) -> dict[str, Any] | None:
    candidates: list[Path] = []
    if path is not None:
        candidates.append(path)
    if fallback_paths:
        candidates.extend(fallback_paths)
    default_candidate = default_google_oauth_file()
    if not any(candidate.expanduser() == default_candidate for candidate in candidates):
        candidates.append(default_candidate)
    target = None
    for candidate in candidates:
        resolved = candidate.expanduser()
        if resolved.exists():
            target = resolved
            break
    if target is None:
        return None
    data = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ProviderAdapterError(code="provider-auth-invalid", message=f"OAuth store is not a JSON object: {target}")
    data["_path"] = str(target)
    return data


def write_google_oauth_store(payload: dict[str, Any], path: Path | None = None) -> Path:
    target = path or default_google_oauth_file()
    target.parent.mkdir(parents=True, exist_ok=True)
    clean_payload = dict(payload)
    clean_payload.pop("_path", None)
    target.write_text(json.dumps(clean_payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return target


def access_token_is_valid(payload: dict[str, Any], *, skew_seconds: int = 60) -> bool:
    access_token = str(payload.get("access_token", "") or "").strip()
    expires_at = normalize_optional_timestamp(payload.get("access_token_expires_at", ""))
    if not access_token or not expires_at:
        return False
    expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    return expiry > datetime.now(timezone.utc) + timedelta(seconds=skew_seconds)


def google_refresh_access_token(payload: dict[str, Any], *, timeout_seconds: int = 10) -> dict[str, Any]:
    client_id = str(payload.get("client_id", "") or "").strip()
    refresh_token = str(payload.get("refresh_token", "") or "").strip()
    client_secret = str(payload.get("client_secret", "") or "").strip()
    token_uri = str(payload.get("token_uri", "https://oauth2.googleapis.com/token") or "").strip()
    if not client_id or not refresh_token:
        raise ProviderAdapterError(code="provider-auth-missing", message="OAuth store is missing `client_id` or `refresh_token`.")
    form = {
        "client_id": client_id,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    if client_secret:
        form["client_secret"] = client_secret
    data = parse.urlencode(form).encode("utf-8")
    req = request.Request(token_uri, data=data, headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"})
    try:
        with request.urlopen(req, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        message = exc.read().decode("utf-8", errors="ignore") if hasattr(exc, "read") else str(exc)
        raise ProviderAdapterError(code="provider-auth-refresh-failed", message=message or "Failed to refresh Google access token.") from exc
    except error.URLError as exc:
        raise ProviderAdapterError(code="provider-auth-refresh-offline", message=str(exc.reason), retryable=True) from exc
    try:
        refreshed = json.loads(body)
    except json.JSONDecodeError as exc:
        raise ProviderAdapterError(code="provider-auth-invalid", message=f"Token endpoint returned invalid JSON: {exc}") from exc
    if not isinstance(refreshed, dict):
        raise ProviderAdapterError(code="provider-auth-invalid", message="Token endpoint returned a non-object payload.")
    access_token = str(refreshed.get("access_token", "") or "").strip()
    expires_in = int(refreshed.get("expires_in", 0) or 0)
    if not access_token or expires_in <= 0:
        raise ProviderAdapterError(code="provider-auth-invalid", message="Token endpoint did not return a usable access token.")
    updated = dict(payload)
    updated["access_token"] = access_token
    updated["token_type"] = str(refreshed.get("token_type", updated.get("token_type", "Bearer")) or "Bearer")
    updated["scope"] = str(refreshed.get("scope", updated.get("scope", "")) or "")
    updated["access_token_issued_at"] = current_utc_iso()
    updated["access_token_expires_at"] = (
        datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    ).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return updated


def google_access_token_from_env_or_store(*, timeout_seconds: int = 10, oauth_store_path: Path | None = None, fallback_paths: list[Path] | None = None) -> str:
    direct = os.environ.get("SULA_GOOGLE_ACCESS_TOKEN", "").strip()
    if direct:
        return direct
    payload = load_google_oauth_store(oauth_store_path, fallback_paths=fallback_paths)
    if payload is None:
        return ""
    if access_token_is_valid(payload):
        return str(payload.get("access_token", "") or "").strip()
    refreshed = google_refresh_access_token(payload, timeout_seconds=timeout_seconds)
    write_google_oauth_store(refreshed, Path(str(payload.get("_path", default_google_oauth_file()))))
    return str(refreshed.get("access_token", "") or "").strip()
