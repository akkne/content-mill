import asyncio
import logging
from collections.abc import Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.container import knowledge_service, script_writer, video_production
from app.presentation.mcp import create_mcp


async def cleanup_loop():
    while True:
        await asyncio.sleep(60)
        try:
            await asyncio.to_thread(knowledge_service().clean_uploads)
        except Exception:
            logging.getLogger(__name__).exception("Failed to clean expired uploads")


async def queue_loop(run_next: Callable[[], bool]):
    while True:
        try:
            worked = await asyncio.to_thread(run_next)
        except Exception:
            logging.getLogger(__name__).exception("Job queue unavailable")
            worked = False
        await asyncio.sleep(0 if worked else 5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    writer = script_writer()
    mcp = create_mcp()
    app.state.mcp_app = mcp.streamable_http_app()
    async with mcp.session_manager.run():
        tasks = [
            asyncio.create_task(cleanup_loop()),
            asyncio.create_task(queue_loop(writer.run_next)),
            asyncio.create_task(queue_loop(video_production().run_next)),
        ]
        try:
            yield
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
