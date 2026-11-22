"""Attach an administrator-verified Polza order to a stopped scene, without submitting work."""

import argparse
import os
import re
from datetime import UTC, datetime
from uuid import UUID

from app.infrastructure.database.transactions.projects import (
    SqlAlchemyProjectUnitOfWork,
)
from app.infrastructure.providers.media.polza_media import PolzaMedia


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=UUID)
    parser.add_argument("video", type=UUID)
    parser.add_argument("scene", type=int, help="Scene number, starting at 1")
    parser.add_argument(
        "order", help="Polza generation ID from the verified history entry"
    )
    args = parser.parse_args()
    if not re.fullmatch(r"gen_[A-Za-z0-9_-]{1,190}", args.order):
        parser.error("Invalid Polza order ID")
    api = PolzaMedia(os.environ["POLZA_API_KEY"])
    order = api.request("GET", "/" + args.order)
    if order.get("id") != args.order or order.get("status") not in {
        "completed",
        "processing",
        "pending",
    }:
        parser.error("The order is unavailable or rejected")
    with SqlAlchemyProjectUnitOfWork() as work:
        video = work.videos.get(args.project, args.video, lock=True)
        if video is None or not video.needs_order_check():
            parser.error("The video has no unresolved submission")
        state = video.settings["production"]
        if state.get("index", 0) + 1 != args.scene:
            parser.error("The stopped scene has changed")
        frame = state["stage"] == "frame"
        model = state["failure"].get("model") or (
            "google/gemini-nano-banana-2.1" if frame else "kling/v2.6"
        )
        if order.get("model") != model:
            parser.error("The order belongs to another model")
        state.update(
            operation="polza:" + args.order,
            stage="collect_frame" if frame else "collect",
            submitted=datetime.now(UTC).isoformat(),
        )
        if not frame:
            state["clip_model"] = model
        work.videos.save(video)
        work.commit()
    print("Order linked. Resume from the video card to retrieve the result.")


if __name__ == "__main__":
    main()
