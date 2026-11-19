from io import BytesIO

import av
from PIL import Image, ImageOps, UnidentifiedImageError

from app.domain.knowledge import InvalidNodeOperation


def check_size(width: int, height: int) -> None:
    if not width or not height or width * height > 32_000_000:
        raise InvalidNodeOperation("Размер кадра превышает предел предпросмотра")


class AssetPreview:
    def render(self, data: bytes, mime: str) -> bytes:
        try:
            if mime.startswith("video/"):
                fmt = {"video/mp4": "mov", "video/webm": "matroska"}[mime]
                with av.open(
                    BytesIO(data), format=fmt, options={"protocol_whitelist": "pipe"}
                ) as container:
                    stream = container.streams.video[0]
                    check_size(stream.width, stream.height)
                    frame = next(container.decode(stream))
                    check_size(frame.width, frame.height)
                    picture = frame.to_image()
            else:
                with Image.open(
                    BytesIO(data), formats=["PNG", "JPEG", "WEBP"]
                ) as source:
                    check_size(*source.size)
                    source.thumbnail((768, 768))
                    picture = ImageOps.exif_transpose(source)
            picture.thumbnail((768, 768))
            output = BytesIO()
            picture.convert("RGB").save(output, "JPEG", quality=80)
            return output.getvalue()
        except (
            av.FFmpegError,
            UnidentifiedImageError,
            OSError,
            ValueError,
            KeyError,
            IndexError,
            StopIteration,
            Image.DecompressionBombError,
        ) as error:
            raise InvalidNodeOperation(
                "Не удалось получить кадр для предпросмотра"
            ) from error
