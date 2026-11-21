from app.infrastructure.polza_media import PolzaMedia, image_input


class PolzaVeoFast:
    def __init__(self, api: PolzaMedia):
        self.api = api

    def submit(self, prompt: str, frame: bytes) -> str:
        return self.api.submit(
            "google/veo3_fast",
            {
                "prompt": prompt,
                "aspect_ratio": "9:16",
                "images": [image_input(frame, "image/png")],
                "generationType": "FIRST_AND_LAST_FRAMES_2_VIDEO",
                "enableTranslation": "false",
            },
        )

    def collect(self, operation: str) -> bytes | None:
        return self.api.collect(operation, 64 * 1024 * 1024, "clip_rejected")
