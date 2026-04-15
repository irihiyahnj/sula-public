from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class ProviderSnapshot:
    provider: str
    provider_item_id: str
    provider_item_kind: str
    provider_item_url: str
    provider_title: str
    provider_revision_id: str
    provider_modified_at: str
    provider_etag: str
    truth_source_reason: str
    normalized_content: dict[str, object]
    raw_metadata: dict[str, object]


@dataclass
class ProviderAdapterError(Exception):
    code: str
    message: str
    retryable: bool = False

    def __str__(self) -> str:
        return self.message


class ProviderAdapter(Protocol):
    def fetch_item(self, *, provider_item_id: str, provider_item_kind: str, provider_item_url: str) -> ProviderSnapshot:
        ...
