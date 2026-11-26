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


def test_expressive_speed_overrides_cached_templates_and_keeps_voice():
    import json

    requests = []

    def handle(req):
        requests.append(json.loads(req.content))
        return httpx.Response(200, json={"success": True, "data": {"id": str(uuid4())}})

    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        provider = LumeanElevenLabs("key", client)
        provider.template("selected-voice")
        previous = uuid4()
        provider.submit(previous, "selected-voice", "Точный текст.", uuid4())
    template = requests[0]["config"]["tts_settings"]
    order = requests[1]["config_override"]["tts_settings"]
    assert requests[1]["template_id"] == str(previous)
    assert order["advanced_voice_settings"] and order["voice_id"] == "selected-voice"
    assert template["voice_settings"] == order["voice_settings"]
    assert (
        order["voice_settings"]["speed"] == 1.1
        and order["voice_settings"]["style"] == 0.4
    )


def test_cast_synthesis_uses_its_saved_delivery():
    import json

    calls = []

    def handle(request):
        calls.append(json.loads(request.content))
        return httpx.Response(200, json={"success": True, "data": {"id": str(uuid4())}})

    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        voice = {
            "elevenlabs_voice_id": "speaker",
            "model_id": "eleven_multilingual_v2",
            "speed": 0.85,
            "style": 0.0,
        }
        LumeanElevenLabs("test", client).submit_line(voice, "Проверка", uuid4())
    delivery = calls[-1]["config_override"]["tts_settings"]["voice_settings"]
    assert (delivery["speed"], delivery["style"]) == (0.85, 0.0)
