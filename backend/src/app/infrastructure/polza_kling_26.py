from app.infrastructure.polza_media import PolzaMedia, image_input


class PolzaKling26:
    def __init__(self, api: PolzaMedia):
        self.api = api

    def submit(self, prompt: str, frame: bytes) -> str:
        return self.api.submit(
            "kling/v2.6",
            {
                "prompt": prompt,
                "duration": "10",
                "sound": "true",
                "aspect_ratio": "9:16",
                "images": [image_input(frame, "image/png")],
            },
        )

    def collect(self, operation: str) -> bytes | None:
        return self.api.collect(operation, 64 * 1024 * 1024, "clip_rejected")
