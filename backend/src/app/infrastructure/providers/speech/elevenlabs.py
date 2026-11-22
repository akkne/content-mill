from threading import Lock
from time import monotonic

import httpx

from app.application.voices.catalog import (
    CatalogError,
    CatalogVoice,
    VoiceCatalog,
    VoicePage,
)


def catalog_voice(data: dict, language: str) -> CatalogVoice:
    labels = data.get("labels") or {}
    verified = data.get("verified_languages") or []
    languages = [labels.get("language"), *(item.get("language") for item in verified)]
    previews = [
        item.get("preview_url") for item in verified if item.get("language") == language
    ]
    previews.extend(
        [data.get("preview_url"), *(item.get("preview_url") for item in verified)]
    )
    return CatalogVoice(
        data["voice_id"],
        data.get("name") or data["voice_id"],
        data.get("description") or labels.get("description") or "",
        list(dict.fromkeys(lang for lang in languages if lang)),
        labels.get("gender") if labels.get("gender") in ("male", "female") else None,
        next((url for url in previews if url and url.startswith("https://")), None),
    )


# Legacy direct integration. Do not use it in the application; use Lumean instead.
class ElevenLabsCatalog(VoiceCatalog):
    def __init__(self, key: str, client: httpx.Client):
        self.key = key
        self.client = client
        self.cache: dict[tuple, tuple[float, VoicePage]] = {}
        self.lock = Lock()

    def search(
        self, query: str, exact: bool, language: str, gender: str, cursor: str
    ) -> VoicePage:
        if not self.key:
            raise CatalogError(
                503, "Каталог не подключён. Добавьте ELEVENLABS_API_KEY на сервере."
            )
        params = {"page_size": "20", "include_total_count": "false"}
        for name, value in (
            ("voice_ids" if exact else "search", query),
            ("language", language),
            ("gender", gender),
            ("next_page_token", cursor),
        ):
            if value:
                params[name] = value
        key = tuple(params.items())
        with self.lock:
            hit = self.cache.get(key)
            if hit and monotonic() < hit[0]:
                return hit[1]
        try:
            response = self.client.get(
                "https://api.elevenlabs.io/v2/voices",
                params=params,
                headers={"xi-api-key": self.key},
            )
            if response.status_code == 429:
                raise CatalogError(
                    429, "ElevenLabs временно ограничил запросы. Повторите позже."
                )
            if response.status_code in (401, 403):
                raise CatalogError(
                    503, "Проверьте ключ ElevenLabs и право чтения голосов."
                )
            response.raise_for_status()
            data = response.json()
            page = VoicePage(
                [
                    catalog_voice(item, language)
                    for item in data["voices"]
                    if not exact or item["voice_id"] == query
                ],
                data.get("next_page_token") if data["has_more"] else None,
            )
        except (
            httpx.HTTPError,
            KeyError,
            TypeError,
            ValueError,
            AttributeError,
        ) as exc:
            raise CatalogError(
                502, "Не удалось получить каталог ElevenLabs. Повторите позже."
            ) from exc
        with self.lock:
            if len(self.cache) >= 128:
                self.cache.pop(next(iter(self.cache)))
            self.cache[key] = (monotonic() + 60, page)
        return page
