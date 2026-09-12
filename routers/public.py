from typing import Optional
from fastapi import APIRouter, Depends, Request, Response, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from core.database import get_db
from core.errors import NotFoundError
from schemas.widget import WidgetConfig
from schemas.submission import PublicSubmissionRequest, SubmissionSuccess
from services.widget_service import WidgetService
from services.submission_service import SubmissionService
from services.rate_limit_service import rate_limiter
from services.spam_service import SpamService
import logging

router = APIRouter(tags=["public"])
logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> str:
    """Get client IP address from request."""
    # Check for forwarded IP headers (for load balancers/proxies)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the list
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to direct connection IP
    return request.client.host if request.client else "127.0.0.1"


@router.get("/widgets/{widget_id}/config", response_model=WidgetConfig)
def get_widget_config(
    widget_id: str,
    response: Response,
    db: Session = Depends(get_db)
):
    """Get public widget configuration for rendering."""
    service = WidgetService(db)
    widget = service.get_widget_public(widget_id)
    
    if not widget:
        raise NotFoundError("Widget not found or inactive")
    
    # Set cache headers for public config
    response.headers["Cache-Control"] = "public, max-age=300"
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    
    return WidgetConfig(
        id=widget.id,
        type=widget.type,
        title=widget.title,
        description=widget.description,
        form_fields=widget.form_fields,
        button_text=widget.button_text,
        display_options=widget.display_options or {},
        version=widget.version
    )


@router.options("/submissions")
def preflight_submissions():
    """Handle CORS preflight for submissions."""
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Idempotency-Key",
        "Access-Control-Max-Age": "86400"  # 24 hours
    }
    return JSONResponse(content={}, headers=headers)


@router.post("/submissions", response_model=SubmissionSuccess)
async def create_submission(
    submission_data: PublicSubmissionRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new submission (public endpoint)."""
    
    # Get client information
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent")
    idempotency_key = request.headers.get("Idempotency-Key")
    
    # Rate limiting
    try:
        rate_limiter.check_rate_limits(client_ip, submission_data.widget_id)
    except Exception as e:
        logger.warning(f"Rate limit exceeded for IP {client_ip}, widget {submission_data.widget_id}")
        raise e
    
    # Create submission through service
    service = SubmissionService(db)
    
    submission = await service.create_submission(
        widget_id=submission_data.widget_id,
        submitted_data=submission_data.data,
        ip_address=client_ip,
        user_agent=user_agent,
        idempotency_key=idempotency_key,
        hp_field=submission_data.hp_field
    )
    
    # Set CORS headers
    response_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Idempotency-Key"
    }
    
    # Check if this was a spam submission (ID will be 0 for dropped spam)
    if submission.id == 0:
        logger.info("Spam submission handled - returning success without storage")
    else:
        logger.info(f"Submission created successfully: {submission.id}")
    
    return JSONResponse(
        content={"success": True, "message": "Submission received successfully"},
        headers=response_headers
    )