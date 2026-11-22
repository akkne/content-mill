import httpx


def download_result(url: str, limit: int) -> bytes:
    if httpx.URL(url).scheme != "https":
        raise ValueError("Expected signed HTTPS result URL")
    with httpx.stream("GET", url, timeout=90) as response:
        response.raise_for_status()
        data = bytearray()
        for chunk in response.iter_bytes():
            data.extend(chunk)
            if len(data) > limit:
                raise ValueError("Provider result too large")
        return bytes(data)
