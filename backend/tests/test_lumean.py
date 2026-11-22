from uuid import uuid4

import httpx
import pytest
from app.application.voices.catalog import CatalogError
from app.infrastructure.providers.speech.lumean import LumeanElevenLabs


def test_catalog_search_and_pagination():
    def handle(req):
        assert req.headers["X-API-KEY"] == "server"
        assert dict(req.url.params) == {
            "provider": "elevenlabs",
            "page": "2",
            "per_page": "20",
            "language": "ru",
            "gender": "female",
            "search": "Анна",
        }
        return httpx.Response(
            200,
            json={
                "success": True,
                "data": {
                    "total": None,
                    "has_more": True,
                    "items": [
                        {
                            "voice_id": "id",
                            "name": None,
                            "language": "ru",
                            "languages": ["ru", "en"],
                            "preview_url": "http://invalid.test",
                        }
                    ],
                },
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        page = LumeanElevenLabs("server", client).search(
            "Анна", False, "ru", "female", "2"
        )
        assert page.next_cursor == "3"
        assert page.items[0].languages == ["ru", "en"]
        assert page.items[0].name == "id" and page.items[0].preview_url is None


@pytest.mark.parametrize(("status", "expected"), [(401, 503), (429, 429), (500, 502)])
def test_provider_failure(status, expected):
    with httpx.Client(
        transport=httpx.MockTransport(lambda _: httpx.Response(status))
    ) as client:
        with pytest.raises(CatalogError) as error:
            LumeanElevenLabs("key", client).result(uuid4())
        assert error.value.status == expected


def test_missing_key_does_not_contact_provider():
    with (
        httpx.Client(
            transport=httpx.MockTransport(lambda _: pytest.fail("unexpected request"))
        ) as client,
        pytest.raises(CatalogError, match="LUMEAN_API_KEY"),
    ):
        LumeanElevenLabs("", client).search("", False, "", "", "")
