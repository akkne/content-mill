from fastapi import FastAPI

app = FastAPI(title="Content Mill API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
