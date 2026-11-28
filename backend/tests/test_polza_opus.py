import json
from uuid import uuid4

import httpx
import pytest
from app import container
from app.infrastructure.providers.text.astra_script import AstraCli
from app.infrastructure.providers.text.polza_opus import PolzaOpus


def test_montage_selection_and_assembly_preflight(monkeypatch):
    astra = AstraCli("codex-test")
    monkeypatch.setattr(
        container, "text_models", lambda: ({astra.model: astra}, astra.model)
    )
    monkeypatch.delenv("CONTENT_MILL_MONTAGE_PROVIDER", raising=False)
    assert container.video_production().model is astra
    monkeypatch.setenv("CONTENT_MILL_MONTAGE_PROVIDER", "polza")
    monkeypatch.setenv("POLZA_API_KEY", "test")
    assert isinstance(container.video_production().model, PolzaOpus)
    assert container.video_service().generator.model is astra
    assert not container.video_service().assembly_error
    monkeypatch.delenv("POLZA_API_KEY")
    assert "POLZA_API_KEY" in container.video_service().assembly_error
    worker = container.video_production()
    assert worker.model is None and worker.missing_model_error == "polza_key"
    monkeypatch.setenv("CONTENT_MILL_MONTAGE_PROVIDER", "other")
    with pytest.raises(ValueError, match="CONTENT_MILL_MONTAGE_PROVIDER"):
        container.video_service()


def test_opus_inspects_material_and_returns_final_edit(monkeypatch):
    ref = str(uuid4())
    requests = []
    timeline = '{"cuts":[{"scene":1,"start_ms":0,"end_ms":3175}]}'

    def post(client, url, *, json):
        assert url == "https://polza.ai/api/v1/messages"
        assert client.headers["Authorization"] == "Bearer test"
        assert json["model"] == "anthropic/claude-opus-5.5"
        assert json["system"] == "edit"
        requests.append(len(json["messages"]))
        if len(requests) == 1:
            assert {tool["name"] for tool in json["tools"]} == {
                "inspect_material",
                "inspect_frame",
                "listen",
                "openmotion_get_template",
            }
            assert json["messages"][0]["content"][1]["source"]["data"] == "anBlZw=="
            body = {
                "stop_reason": "tool_use",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "tool1",
                        "name": "inspect_material",
                        "input": {"version_id": ref},
                    }
                ],
            }
        else:
            (result,) = json["messages"][-1]["content"]
            assert result == {
                "type": "tool_result",
                "tool_use_id": "tool1",
                "content": [{"type": "text", "text": timeline}],
            }
            body = {
                "stop_reason": "end_turn",
                "content": [{"type": "text", "text": timeline}],
            }
        return httpx.Response(200, request=httpx.Request("POST", url), json=body)

    monkeypatch.setattr(httpx.Client, "post", post)
    assert (
        PolzaOpus("test").generate_edit(
            "edit",
            json.dumps({"motion_template": "story"}),
            ["anBlZw=="],
            [b"local clip"],
            [(ref, "plain", timeline.encode())],
        )
        == timeline
    )
    assert requests == [1, 3]


def test_truncated_output_does_not_become_an_edit(monkeypatch):
    def post(client, url, *, json):
        assert "tools" not in json
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={
                "stop_reason": "max_tokens",
                "content": [{"type": "text", "text": "{}"}],
            },
        )

    monkeypatch.setattr(httpx.Client, "post", post)
    with pytest.raises(ValueError, match="Incomplete Polza"):
        PolzaOpus("test").generate("plan", "example", [])
