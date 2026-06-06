"""Aggregate v1 API router. Endpoint modules are included as phases land."""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    analytics,
    articles,
    auth,
    benchmarks,
    companies,
    health,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["meta"])
api_router.include_router(auth.router)
api_router.include_router(articles.router)
api_router.include_router(companies.router)
api_router.include_router(benchmarks.router)
api_router.include_router(analytics.router)
