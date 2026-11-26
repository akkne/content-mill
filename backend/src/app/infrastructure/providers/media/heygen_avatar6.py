from app.application.videos.production import ProductionError
from app.infrastructure.providers.media.heygen_api import HeyGenAPI


class HeyGenAvatar6(HeyGenAPI):
    model = "heygen-avatar-6-turbo"

    def submit(self, image: bytes, audio: bytes) -> str:
        def asset(name, data, mime):
            if len(data) > 50_000_000:
                raise ProductionError("lipsync_input")
            uploaded = self.request(
                "POST", "assets", files={"file": (name, data, mime)}
            )
            return {"type": "asset_id", "asset_id": uploaded["asset_id"]}

        payload = {
            "model": self.model,
            "reference_images": [asset("presenter.png", image, "image/png")],
            "audio": asset("speech.wav", audio, "audio/wav"),
            "resolution": "1080p",
        }
        return self.create_video("models/avatars", payload)

    def collect(self, operation: str) -> bytes | None:
        return self.collect_video(operation, "lipsync_failed")
