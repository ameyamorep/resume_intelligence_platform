from fastapi import APIRouter

from app.models.schemas import HealthStatus
from app.services.ai.analyzer import resolve_provider
from app.services.matching import embedding_engine

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthStatus)
def health() -> HealthStatus:
    provider = resolve_provider()
    return HealthStatus(
        embedding_backend=embedding_engine.backend_name(),
        claude_configured=provider != "none",
        ai_provider=provider,
    )
