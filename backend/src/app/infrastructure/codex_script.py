import httpx


class CodexScript:
    model = "gpt-5.3-codex"

    def __init__(self, key: str):
        self.key = key

    def generate(self, instructions: str, text: str, images: list[str]) -> str:
        content = [{"type": "input_text", "text": text}]
        content.extend(
            {"type": "input_image", "image_url": "data:image/jpeg;base64," + image}
            for image in images
        )
        response = httpx.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": "Bearer " + self.key},
            json={
                "model": self.model,
                "store": False,
                "instructions": instructions,
                "input": [{"role": "user", "content": content}],
                "max_output_tokens": 6000,
            },
            timeout=90,
        )
        response.raise_for_status()
        data = response.json()
        if data["status"] != "completed":
            raise ValueError("Incomplete response")
        return "".join(
            part["text"]
            for item in data["output"]
            if item["type"] == "message" and item.get("phase") != "commentary"
            for part in item["content"]
            if part["type"] == "output_text"
        )
