from io import BytesIO

from PIL import Image

from app.application.videos.production import ProductionError
from app.infrastructure.providers.media.polza_media import PolzaMedia, image_input


class PolzaNanoBanana21:
    def __init__(self, api: PolzaMedia):
        self.api = api

    def submit(self, prompt: str, references: list[bytes]) -> str:
        inputs = {
            "prompt": prompt,
            "aspect_ratio": "9:16",
            "image_resolution": "1K",
            "output_format": "png",
        }
        if references:
            inputs["images"] = [image_input(ref, "image/jpeg") for ref in references]
        return self.api.submit("google/gemini-nano-banana-2.1", inputs)

    def collect(self, operation: str) -> bytes | None:
        data = self.api.collect(operation, 8_000_000, "frame_rejected")
        if data is not None:
            try:
                with Image.open(BytesIO(data), formats=["PNG"]) as image:
                    image.verify()
            except (ValueError, OSError, SyntaxError) as error:
                raise ProductionError(
                    "frame_rejected", reason="invalid_frame"
                ) from error
        return data
