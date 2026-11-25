"""Versioned catalog of executable OpenMotion guides."""

import json
from pathlib import Path

STYLES = {
    item["id"]: item
    for item in json.loads(Path(__file__).with_name("styles.json").read_text())
}
DEFAULT_STYLE = "motion-be2a4af0-0183-4979-ab05-2a68413c0890"
