from io import BytesIO

from PIL import Image

from app.infrastructure.providers.media.fal_media import FalMedia, data_uri


class NanoBanana21:
    def __init__(self, api: FalMedia):
        self.api = api

    def generate(self, prompt: str, references: list[bytes]) -> bytes:
        endpoint = "https://fal.run/google/nano-banana-2.1"
        payload = {
            "prompt": prompt,
            "aspect_ratio": "9:16",
            "resolution": "1K",
            "output_format": "png",
            "num_images": 1,
        }
        if references:
            endpoint += "/edit"
            payload["image_urls"] = [
                data_uri("image/jpeg", image) for image in references
            ]
        result = self.api.request("POST", endpoint, payload)
        data = self.api.download(result["images"][0]["url"], 8_000_000)
        with Image.open(BytesIO(data), formats=["PNG"]) as image:
            image.verify()
        return data
