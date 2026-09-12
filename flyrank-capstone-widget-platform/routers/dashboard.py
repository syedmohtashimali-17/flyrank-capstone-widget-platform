from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from core.database import get_db
from models.user import User
from routers.auth import get_current_user
from schemas.submission import SubmissionResponse
from schemas.dashboard import DashboardStats, SubmissionStats
from services.submission_service import SubmissionService
from services.analytics_service import AnalyticsService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/submissions", response_model=List[SubmissionResponse])
def get_submissions(
    widget_id: Optional[str] = Query(None, description="Filter by widget ID"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get submissions for the authenticated user with optional widget filtering."""
    service = SubmissionService(db)
    submissions = service.get_submissions_for_tenant(
        tenant_id=current_user.id,
        widget_id=widget_id,
        limit=limit,
        offset=offset
    )
    return submissions


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive dashboard statistics for the authenticated user."""
    service = AnalyticsService(db)
    stats = service.get_dashboard_stats(current_user.id)
    return stats


@router.get("/widgets/{widget_id}/stats", response_model=SubmissionStats)
def get_widget_stats(
    widget_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analytics for a specific widget."""
    service = AnalyticsService(db)
    stats = service.get_widget_analytics(current_user.id, widget_id)
    return stats