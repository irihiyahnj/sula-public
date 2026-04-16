from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib import error, parse, request

from .base import ProviderAdapter, ProviderAdapterError, ProviderSnapshot
from .google_oauth_store import google_access_token_from_env_or_store


def _http_get_json(url: str, *, access_token: str, timeout_seconds: int) -> tuple[dict[str, Any], dict[str, str]]:
    req = request.Request(url, headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"})
    try:
        with request.urlopen(req, timeout=timeout_seconds) as response:
            payload = response.read().decode("utf-8")
            data = json.loads(payload)
            headers = {key.lower(): value for key, value in response.headers.items()}
            if not isinstance(data, dict):
                raise ProviderAdapterError(code="provider-invalid-response", message="Provider returned a non-object JSON payload.")
            return data, headers
    except error.HTTPError as exc:
        status = getattr(exc, "code", 0)
        message = exc.read().decode("utf-8", errors="ignore") if hasattr(exc, "read") else str(exc)
        if status == 401:
            raise ProviderAdapterError(code="provider-auth-expired", message=message or "Provider token is expired or invalid.") from exc
        if status == 403:
            raise ProviderAdapterError(code="provider-permission-denied", message=message or "Provider denied access.") from exc
        if status == 404:
            raise ProviderAdapterError(code="provider-item-not-found", message=message or "Provider item was not found.") from exc
        if status == 429:
            raise ProviderAdapterError(code="provider-rate-limited", message=message or "Provider rate limit reached.", retryable=True) from exc
        if status >= 500:
            raise ProviderAdapterError(code="provider-offline", message=message or "Provider backend error.", retryable=True) from exc
        raise ProviderAdapterError(code="provider-http-error", message=message or f"Provider HTTP error: {status}") from exc
    except error.URLError as exc:
        raise ProviderAdapterError(code="provider-offline", message=str(exc.reason), retryable=True) from exc
    except json.JSONDecodeError as exc:
        raise ProviderAdapterError(code="provider-invalid-response", message=f"Provider returned invalid JSON: {exc}") from exc


def _fixture_candidates(fixture_dir: Path, *, provider_item_kind: str, provider_item_id: str) -> list[Path]:
    slugged_kind = provider_item_kind.strip().lower()
    slugged_id = provider_item_id.strip()
    return [
        fixture_dir / f"{slugged_kind}--{slugged_id}.json",
        fixture_dir / f"{slugged_id}.json",
    ]


def _doc_paragraph_text(paragraph: dict[str, Any]) -> str:
    text_parts: list[str] = []
    for element in paragraph.get("elements", []):
        if not isinstance(element, dict):
            continue
        text_run = element.get("textRun")
        if isinstance(text_run, dict):
            text_parts.append(str(text_run.get("content", "")))
    return "".join(text_parts).strip()


def normalize_google_doc(document: dict[str, Any]) -> dict[str, object]:
    blocks: list[dict[str, object]] = []
    plain_text_parts: list[str] = []
    table_count = 0
    paragraph_count = 0
    for item in document.get("body", {}).get("content", []):
        if not isinstance(item, dict):
            continue
        paragraph = item.get("paragraph")
        table = item.get("table")
        if isinstance(paragraph, dict):
            text = _doc_paragraph_text(paragraph)
            if not text:
                continue
            paragraph_count += 1
            style = str(paragraph.get("paragraphStyle", {}).get("namedStyleType", ""))
            block_type = "heading" if style.startswith("HEADING_") or style == "TITLE" else "paragraph"
            blocks.append({"type": block_type, "style": style, "text": text})
            plain_text_parts.append(text)
            continue
        if isinstance(table, dict):
            rows = table.get("tableRows", [])
            row_count = len(rows) if isinstance(rows, list) else 0
            col_count = 0
            if row_count and isinstance(rows[0], dict):
                cells = rows[0].get("tableCells", [])
                col_count = len(cells) if isinstance(cells, list) else 0
            blocks.append({"type": "table", "rows": row_count, "cols": col_count})
            table_count += 1
    plain_text = "\n".join(plain_text_parts).strip()
    return {
        "kind": "google-doc",
        "title": str(document.get("title", "")),
        "blocks": blocks[:200],
        "plain_text": plain_text[:8000],
        "paragraph_count": paragraph_count,
        "table_count": table_count,
    }


def normalize_google_sheet(spreadsheet: dict[str, Any]) -> dict[str, object]:
    sheet_summaries: list[dict[str, object]] = []
    for item in spreadsheet.get("sheets", []):
        if not isinstance(item, dict):
            continue
        properties = item.get("properties", {})
        if not isinstance(properties, dict):
            properties = {}
        grid = properties.get("gridProperties", {})
        if not isinstance(grid, dict):
            grid = {}
        sheet_summaries.append(
            {
                "title": str(properties.get("title", "")),
                "index": int(properties.get("index", 0) or 0),
                "rows": int(grid.get("rowCount", 0) or 0),
                "cols": int(grid.get("columnCount", 0) or 0),
            }
        )
    return {
        "kind": "google-sheet",
        "title": str(spreadsheet.get("properties", {}).get("title", "")),
        "sheet_count": len(sheet_summaries),
        "sheets": sheet_summaries[:50],
    }


class GoogleDriveProviderAdapter(ProviderAdapter):
    def __init__(self, *, access_token: str | None, fixture_dir: Path | None, timeout_seconds: int = 10) -> None:
        self.access_token = access_token or ""
        self.fixture_dir = fixture_dir
        self.timeout_seconds = timeout_seconds

    def _load_fixture(self, *, provider_item_kind: str, provider_item_id: str) -> dict[str, Any] | None:
        if self.fixture_dir is None:
            return None
        for candidate in _fixture_candidates(self.fixture_dir, provider_item_kind=provider_item_kind, provider_item_id=provider_item_id):
            if candidate.exists():
                data = json.loads(candidate.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    raise ProviderAdapterError(code="provider-invalid-response", message=f"Fixture payload must be a JSON object: {candidate}")
                return data
        return None

    def _drive_metadata(self, *, provider_item_id: str) -> tuple[dict[str, Any], dict[str, str]]:
        if not self.access_token:
            raise ProviderAdapterError(code="provider-auth-missing", message="Missing Google provider auth for refresh. Set `SULA_GOOGLE_ACCESS_TOKEN` or configure a readable Google OAuth store.")
        query = parse.urlencode({"fields": "id,name,mimeType,modifiedTime,version,webViewLink"})
        url = f"https://www.googleapis.com/drive/v3/files/{parse.quote(provider_item_id)}?{query}"
        return _http_get_json(url, access_token=self.access_token, timeout_seconds=self.timeout_seconds)

    def _google_doc_body(self, *, provider_item_id: str) -> dict[str, Any]:
        if not self.access_token:
            raise ProviderAdapterError(code="provider-auth-missing", message="Missing Google provider auth for refresh. Set `SULA_GOOGLE_ACCESS_TOKEN` or configure a readable Google OAuth store.")
        url = f"https://docs.googleapis.com/v1/documents/{parse.quote(provider_item_id)}"
        body, _headers = _http_get_json(url, access_token=self.access_token, timeout_seconds=self.timeout_seconds)
        return body

    def _google_sheet_body(self, *, provider_item_id: str) -> dict[str, Any]:
        if not self.access_token:
            raise ProviderAdapterError(code="provider-auth-missing", message="Missing Google provider auth for refresh. Set `SULA_GOOGLE_ACCESS_TOKEN` or configure a readable Google OAuth store.")
        query = parse.urlencode({"includeGridData": "false"})
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{parse.quote(provider_item_id)}?{query}"
        body, _headers = _http_get_json(url, access_token=self.access_token, timeout_seconds=self.timeout_seconds)
        return body

    def fetch_item(self, *, provider_item_id: str, provider_item_kind: str, provider_item_url: str) -> ProviderSnapshot:
        fixture = self._load_fixture(provider_item_kind=provider_item_kind, provider_item_id=provider_item_id)
        if fixture is not None:
            metadata = fixture.get("metadata", fixture)
            if not isinstance(metadata, dict):
                raise ProviderAdapterError(code="provider-invalid-response", message="Fixture metadata must be a JSON object.")
            provider_title = str(metadata.get("name", metadata.get("title", "")))
            provider_modified_at = str(metadata.get("modifiedTime", metadata.get("modified_at", "")))
            provider_revision_id = str(metadata.get("version", metadata.get("revisionId", metadata.get("revision_id", ""))))
            provider_etag = str(metadata.get("etag", ""))
            provider_item_url = str(metadata.get("webViewLink", metadata.get("url", provider_item_url)))
            if provider_item_kind == "google-doc":
                doc_payload = fixture.get("document", fixture)
                if not isinstance(doc_payload, dict):
                    raise ProviderAdapterError(code="provider-invalid-response", message="Fixture Google Doc payload must be a JSON object.")
                normalized = normalize_google_doc(doc_payload)
            elif provider_item_kind == "google-sheet":
                sheet_payload = fixture.get("spreadsheet", fixture)
                if not isinstance(sheet_payload, dict):
                    raise ProviderAdapterError(code="provider-invalid-response", message="Fixture Google Sheet payload must be a JSON object.")
                normalized = normalize_google_sheet(sheet_payload)
            else:
                raise ProviderAdapterError(code="provider-unsupported-kind", message=f"Unsupported Google provider item kind: {provider_item_kind}")
            return ProviderSnapshot(
                provider="google-drive",
                provider_item_id=provider_item_id,
                provider_item_kind=provider_item_kind,
                provider_item_url=provider_item_url,
                provider_title=provider_title or str(normalized.get("title", "")),
                provider_revision_id=provider_revision_id,
                provider_modified_at=provider_modified_at,
                provider_etag=provider_etag,
                truth_source_reason=f"provider fixture refresh for {provider_item_kind}",
                normalized_content=normalized,
                raw_metadata=metadata,
            )
        metadata, headers = self._drive_metadata(provider_item_id=provider_item_id)
        provider_title = str(metadata.get("name", ""))
        provider_modified_at = str(metadata.get("modifiedTime", ""))
        provider_revision_id = str(metadata.get("version", ""))
        provider_etag = headers.get("etag", "")
        provider_item_url = str(metadata.get("webViewLink", provider_item_url))
        if provider_item_kind == "google-doc":
            normalized = normalize_google_doc(self._google_doc_body(provider_item_id=provider_item_id))
        elif provider_item_kind == "google-sheet":
            normalized = normalize_google_sheet(self._google_sheet_body(provider_item_id=provider_item_id))
        else:
            raise ProviderAdapterError(code="provider-unsupported-kind", message=f"Unsupported Google provider item kind: {provider_item_kind}")
        return ProviderSnapshot(
            provider="google-drive",
            provider_item_id=provider_item_id,
            provider_item_kind=provider_item_kind,
            provider_item_url=provider_item_url,
            provider_title=provider_title or str(normalized.get("title", "")),
            provider_revision_id=provider_revision_id,
            provider_modified_at=provider_modified_at,
            provider_etag=provider_etag,
            truth_source_reason=f"provider-native refresh from Google {provider_item_kind}",
            normalized_content=normalized,
            raw_metadata=metadata,
        )


def create_google_drive_adapter(*, oauth_store_path: Path | None = None, oauth_fallback_paths: list[Path] | None = None) -> GoogleDriveProviderAdapter:
    fixture_dir_raw = os.environ.get("SULA_PROVIDER_FIXTURE_DIR", "").strip()
    fixture_dir = Path(fixture_dir_raw) if fixture_dir_raw else None
    timeout_raw = os.environ.get("SULA_PROVIDER_HTTP_TIMEOUT_SECONDS", "").strip()
    timeout_seconds = int(timeout_raw) if timeout_raw.isdigit() else 10
    return GoogleDriveProviderAdapter(
        access_token=google_access_token_from_env_or_store(
            timeout_seconds=timeout_seconds,
            oauth_store_path=oauth_store_path,
            fallback_paths=oauth_fallback_paths,
        )
        or None,
        fixture_dir=fixture_dir,
        timeout_seconds=timeout_seconds,
    )
