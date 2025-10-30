"""FastAPI integration helpers for vibesafe."""

from __future__ import annotations

from fastapi import APIRouter, FastAPI

from vibesafe.config import get_config

FastAPIApp = FastAPI | APIRouter


def mount(target: FastAPIApp, *, prefix: str = "/_vibesafe") -> None:
    """Mount health and version routes onto a FastAPI router or application.

    Args:
        target: The FastAPI ``FastAPI`` app or ``APIRouter`` to augment.
        prefix: URL prefix for the management endpoints (default ``/_vibesafe``).
    """

    if not prefix.startswith("/"):
        prefix = f"/{prefix}"

    router = APIRouter()

    @router.get("/health", tags=["vibesafe"], summary="Vibesafe health check")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @router.get("/version", tags=["vibesafe"], summary="Vibesafe version info")
    async def version() -> dict[str, str]:
        from vibesafe import __version__

        config = get_config()
        return {
            "version": __version__,
            "env": config.project.env,
        }

    target.include_router(router, prefix=prefix.rstrip("/"))
