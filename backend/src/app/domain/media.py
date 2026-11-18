from app.domain.knowledge import InvalidNodeOperation

MAX_MEDIA_BYTES = 64 * 1024 * 1024
MEDIA_TYPES = {
    "image/png": "image",
    "image/jpeg": "image",
    "image/webp": "image",
    "audio/mp4": "audio",
    "audio/mpeg": "audio",
    "audio/wav": "audio",
    "video/mp4": "video",
    "video/webm": "video",
    "application/pdf": "file",
}


def verify_media(content: bytes, mime: str) -> None:
    signatures = {
        "image/png": content.startswith(b"\x89PNG\r\n\x1a\n"),
        "image/jpeg": content.startswith(b"\xff\xd8\xff"),
        "image/webp": content.startswith(b"RIFF") and content[8:12] == b"WEBP",
        "audio/mp4": content[4:8] == b"ftyp",
        "video/mp4": content[4:8] == b"ftyp",
        "audio/mpeg": content.startswith(b"ID3")
        or (len(content) >= 2 and content[0] == 255 and content[1] & 224 == 224),
        "audio/wav": content.startswith(b"RIFF") and content[8:12] == b"WAVE",
        "video/webm": content.startswith(b"\x1a\x45\xdf\xa3"),
        "application/pdf": content.startswith(b"%PDF-"),
    }
    if not signatures.get(mime):
        raise InvalidNodeOperation("Содержимое не соответствует типу файла")
