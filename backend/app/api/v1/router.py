"""Aggregate v1 API router. Endpoint modules are included as phases land."""
from fastapi import APIRouter

from app.api.v1.endpoints import health

api_router = APIRouter()
api_router.include_router(health.router, tags=["meta"])
