import httpx


class ClaudeScript:
    model = "claude-sonnet-4-6"

    def __init__(self, key: str):
        self.key = key

    def generate(self, instructions: str, text: str, images: list[str]) -> str:
        content = [{"type": "text", "text": text}]
        content.extend(
            {
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg", "data": image},
            }
            for image in images
        )
        response = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": self.key, "anthropic-version": "2023-06-01"},
            json={
                "model": self.model,
                "system": instructions,
                "max_tokens": 6000,
                "messages": [{"role": "user", "content": content}],
            },
            timeout=90,
        )
        response.raise_for_status()
        data = response.json()
        if data["stop_reason"] != "end_turn":
            raise ValueError("Incomplete response")
        return "".join(
            part["text"] for part in data["content"] if part["type"] == "text"
        )
