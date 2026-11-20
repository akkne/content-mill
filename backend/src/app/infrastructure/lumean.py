from uuid import UUID

import httpx
from pydantic import BaseModel, ValidationError

from app.application.speech import SpeechProvider, SpeechResult
from app.application.voice_catalog import (
    CatalogError,
    CatalogVoice,
    VoiceCatalog,
    VoicePage,
)


class VoiceItem(BaseModel):
    voice_id: str
    name: str | None = None
    description: str | None = None
    language: str | None = None
    languages: list[str] | None = None
    gender: str | None = None
    preview_url: str | None = None


class CataloguePage(BaseModel):
    items: list[VoiceItem]
    has_more: bool


class LumeanElevenLabs(VoiceCatalog, SpeechProvider):
    def __init__(self, key: str, client: httpx.Client):
        self.key = key
        self.client = client

    def _request(self, method: str, path: str, **kwargs) -> dict:
        if not self.key:
            raise CatalogError(
                503, "Lumean не подключён. Добавьте LUMEAN_API_KEY на сервере."
            )
        try:
            response = self.client.request(
                method,
                "https://api.lumean.app/api/public/" + path,
                headers={"X-API-KEY": self.key, "Accept": "application/json"},
                **kwargs,
            )
            errors = {
                401: (503, "Проверьте ключ Lumean."),
                403: (503, "Недостаточно прав ключа Lumean."),
                402: (402, "Недостаточно средств или квоты Lumean."),
                404: (404, "Ресурс недоступен в Lumean."),
                422: (
                    422,
                    "Lumean отклонил параметры запроса. Проверьте голос и текст.",
                ),
                429: (429, "Достигнут лимит Lumean. Повторите позже."),
            }
            if response.status_code in errors:
                raise CatalogError(*errors[response.status_code])
            response.raise_for_status()
            body = response.json()
            if (
                not isinstance(body, dict)
                or body.get("success") is not True
                or not isinstance(body.get("data"), dict)
            ):
                raise ValueError
            return body["data"]
        except (ValueError, httpx.HTTPError) as error:
            raise CatalogError(502, "Не удалось получить ответ Lumean.") from error

    def search(
        self, query: str, exact: bool, language: str, gender: str, cursor: str
    ) -> VoicePage:
        if cursor and (
            not cursor.isascii()
            or not cursor.isdigit()
            or len(cursor) > 9
            or int(cursor) < 1
        ):
            raise CatalogError(422, "Некорректная страница каталога.")
        if exact and not query:
            return VoicePage([], None)
        if len(language) > 32 or (exact and len(query) > 128):
            raise CatalogError(422, "Слишком длинный язык или ID голоса.")
        page = int(cursor or 1)
        params = {"provider": "elevenlabs", "page": str(page), "per_page": "20"}
        for key, value in (
            ("voice_id" if exact else "search", query),
            ("language", language),
            ("gender", gender),
        ):
            if value:
                params[key] = value
        try:
            data = CataloguePage.model_validate(
                self._request("GET", "voices", params=params)
            )
        except ValidationError as error:
            raise CatalogError(502, "Некорректный ответ каталога Lumean.") from error
        items = [
            CatalogVoice(
                v.voice_id,
                v.name or v.voice_id,
                v.description or "",
                list(dict.fromkeys(filter(None, [v.language, *(v.languages or [])]))),
                v.gender if v.gender in ("male", "female") else None,
                v.preview_url
                if v.preview_url and v.preview_url.startswith("https://")
                else None,
            )
            for v in data.items
            if not exact or v.voice_id == query
        ]
        return VoicePage(items, str(page + 1) if data.has_more and not exact else None)

    def _create(self, path: str, payload: dict) -> UUID:
        data = self._request("POST", path, json=payload)
        try:
            return UUID(str(data["id"]))
        except (KeyError, ValueError) as error:
            raise CatalogError(502, "Lumean не вернул идентификатор.") from error

    def template(self, voice: str) -> UUID:
        return self._create(
            "templates",
            {
                "name": f"Content Mill {voice}",
                "service_key": "elevenlabs",
                "config": {
                    "tts_settings": {
                        "mode": "mode_v1",
                        "model_id": "eleven_multilingual_v2",
                        "voice_id": voice,
                        "advanced_voice_settings": True,
                        "voice_settings": {
                            "stability": 0.5,
                            "similarity_boost": 0.75,
                            "use_speaker_boost": True,
                            "speed": 1.0,
                        },
                    }
                },
            },
        )

    def submit(self, template: UUID, voice: str, text: str, request: UUID) -> UUID:
        return self._create(
            "orders",
            {
                "template_id": str(template),
                "input_text": text,
                "name": str(request),
                "config_override": {"tts_settings": {"voice_id": voice}},
            },
        )

    def result(self, order: UUID) -> SpeechResult:
        data = self._request("GET", f"orders/{order}")
        if data.get("files_expired"):
            return SpeechResult("expired")
        status = data.get("status")
        if status in ("partially_completed", "failed", "cancelled", "compensated"):
            return SpeechResult("failed")
        if not isinstance(status, str):
            raise CatalogError(502, "В ответе Lumean отсутствует статус.")
        if status not in ("completed", "result_delivered"):
            return SpeechResult("processing")
        files = (
            (data.get("result") or {}).get("files")
            if isinstance(data.get("result"), dict)
            else None
        )
        if not isinstance(files, list) or not files or not isinstance(files[0], str):
            raise CatalogError(502, "Lumean не вернул итоговую дорожку.")
        url = self._request(
            "POST", "storage/url", json={"path": files[0], "download": False}
        ).get("url")
        if not isinstance(url, str) or not url.startswith("https://"):
            raise CatalogError(502, "Lumean не вернул ссылку на аудио.")
        return SpeechResult("completed", url)
