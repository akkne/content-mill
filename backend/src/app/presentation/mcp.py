import os
from contextvars import ContextVar
from typing import Annotated, Any, Literal
from urllib.parse import urlsplit
from uuid import UUID

from mcp.server.fastmcp import FastMCP, Image
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import Field
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import Receive, Scope, Send

from app.application.agents.ports import AgentScope
from app.container import agent_files

current_scope: ContextVar[AgentScope] = ContextVar("mcp_project")
Kind = Literal["document", "image", "video", "audio", "file"]


def create_mcp() -> FastMCP:
    hosts = ["localhost", "localhost:*", "127.0.0.1", "127.0.0.1:*", "[::1]", "[::1]:*"]
    origins = ["http://localhost:*", "http://127.0.0.1:*", "http://[::1]:*"]
    public_origin = os.getenv("MCP_PUBLIC_ORIGIN")
    if public_origin:
        url = urlsplit(public_origin)
        if (
            url.scheme != "https"
            or not url.hostname
            or url.username is not None
            or url.path
            or url.query
            or url.fragment
            or "*" in url.netloc
        ):
            raise ValueError("MCP_PUBLIC_ORIGIN должен быть HTTPS origin без пути")
        hosts.append(url.netloc)
        origins.append(public_origin)
    server = FastMCP(
        "Content Mill",
        stateless_http=True,
        json_response=True,
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=hosts,
            allowed_origins=origins,
        ),
    )

    @server.tool()
    async def find_assets(
        query: Annotated[str, Field(max_length=200)] = "",
        kind: Kind | None = None,
        folder_id: UUID | None = None,
        character_id: UUID | None = None,
        offset: Annotated[int, Field(ge=0)] = 0,
        limit: Annotated[int, Field(ge=1, le=50)] = 20,
    ) -> dict[str, Any]:
        """Find current file versions by project path or indexed text. Folder and avatar filters include descendants. Use next_offset for more results."""
        return await run_in_threadpool(
            agent_files().find,
            current_scope.get(),
            query,
            kind,
            folder_id,
            character_id,
            offset,
            limit,
        )

    @server.tool()
    async def read_document(
        version_id: UUID,
        offset: Annotated[int, Field(ge=0)] = 0,
        limit: Annotated[int, Field(ge=1, le=8000)] = 4000,
    ) -> dict[str, Any]:
        """Read a pinned text document version. Offset and limit count characters."""
        return await run_in_threadpool(
            agent_files().read, current_scope.get(), version_id, offset, limit
        )

    @server.tool(structured_output=False)
    async def preview_asset(version_id: UUID):
        """Return an image thumbnail or first video frame for this exact version. Other file types return metadata."""
        result = await run_in_threadpool(
            agent_files().preview, current_scope.get(), version_id
        )
        return (
            Image(data=result, format="jpeg") if isinstance(result, bytes) else result
        )

    return server


class ProjectMcpEndpoint:
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scheme, _, token = Headers(scope=scope).get("authorization", "").partition(" ")
        grant = (
            await run_in_threadpool(agent_files().resolve, token)
            if scheme.lower() == "bearer"
            else None
        )
        if grant is None:
            response = JSONResponse(
                {"detail": "Требуется действующий токен проекта"},
                401,
                headers={
                    "WWW-Authenticate": 'Bearer realm="Content Mill"',
                    "Cache-Control": "no-store",
                },
            )
            await response(scope, receive, send)
            return
        marker = current_scope.set(grant)
        try:
            await scope["app"].state.mcp_app(scope, receive, send)
        finally:
            current_scope.reset(marker)
