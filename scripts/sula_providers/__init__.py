from __future__ import annotations

from pathlib import Path

from .base import ProviderAdapterError, ProviderSnapshot
from .google_drive import GoogleDriveProviderAdapter, create_google_drive_adapter


def create_provider_adapter(
    storage_provider: str,
    *,
    oauth_store_path: Path | None = None,
    oauth_fallback_paths: list[Path] | None = None,
):
    normalized = storage_provider.strip().lower()
    if normalized == "google-drive":
        return create_google_drive_adapter(
            oauth_store_path=oauth_store_path,
            oauth_fallback_paths=oauth_fallback_paths,
        )
    raise ProviderAdapterError(code="provider-unsupported", message=f"Unsupported storage provider: {storage_provider}")


__all__ = [
    "GoogleDriveProviderAdapter",
    "ProviderAdapterError",
    "ProviderSnapshot",
    "create_google_drive_adapter",
    "create_provider_adapter",
]
