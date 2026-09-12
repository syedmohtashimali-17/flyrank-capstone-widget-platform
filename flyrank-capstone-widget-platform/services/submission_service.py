from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from models.submission import Submission
from models.widget import Widget
from schemas.submission import SubmissionCreate
from core.errors import NotFoundError, ValidationError
from services.spam_service import SpamService
from services.geo_service import geo_service
from services.side_effect_service import side_effect_service
import logging

logger = logging.getLogger(__name__)


class SubmissionService:
    def __init__(self, db: Session):
        self.db = db
    
    def validate_submission_data(self, widget: Widget, submitted_data: Dict[str, Any]) -> None:
        """Validate submitted data against widget configuration."""
        form_fields = {field['name']: field for field in widget.form_fields}
        
        # Check required fields
        for field_name, field_config in form_fields.items():
            if field_config.get('required', False):
                if field_name not in submitted_data or not submitted_data[field_name]:
                    raise ValidationError(f"Required field '{field_name}' is missing or empty")
        
        # Check for unexpected fields
        for field_name in submitted_data.keys():
            if field_name not in form_fields:
                raise ValidationError(f"Unknown field '{field_name}' in submission")
        
        # Validate field types and values
        for field_name, value in submitted_data.items():
            field_config = form_fields[field_name]
            field_type = field_config.get('type', 'text')
            
            # Convert to string and check length
            str_value = str(value)
            if len(str_value) > 1000:  # Max field length
                raise ValidationError(f"Field '{field_name}' exceeds maximum length")
            
            # Email validation
            if field_type == 'email' and value:
                if '@' not in str_value or '.' not in str_value.split('@')[-1]:
                    raise ValidationError(f"Invalid email format for field '{field_name}'")
    
    async def create_submission(
        self, 
        widget_id: str, 
        submitted_data: Dict[str, Any],
        ip_address: str,
        user_agent: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        hp_field: str = ""
    ) -> Submission:
        """Create a new submission with validation and enrichment."""
        
        # Get widget (public access - no tenant restriction)
        widget = self.db.query(Widget).filter(
            Widget.id == widget_id,
            Widget.is_active == True
        ).first()
        
        if not widget:
            raise NotFoundError("Widget not found or inactive")
        
        # Check for spam
        if SpamService.is_spam_submission(submitted_data, hp_field):
            # Silently drop spam - return success but don't store
            logger.info(f"Spam submission dropped for widget {widget_id}")
            # Return a dummy submission (not persisted)
            return Submission(
                id=0,  # Dummy ID
                widget_id=widget_id,
                tenant_id=widget.owner_id,
                submitted_data=submitted_data,
                ip_address=ip_address
            )
        
        # Validate submission data
        self.validate_submission_data(widget, submitted_data)
        
        # Check for duplicate idempotency key
        if idempotency_key:
            existing = self.db.query(Submission).filter(
                Submission.idempotency_key == idempotency_key,
                Submission.widget_id == widget_id
            ).first()
            
            if existing:
                logger.info(f"Duplicate submission ignored - idempotency key: {idempotency_key}")
                return existing
        
        # Geo enrichment (async with fallback)
        country, city = await geo_service.get_location(ip_address)
        
        # Create submission
        submission = Submission(
            widget_id=widget_id,
            tenant_id=widget.owner_id,
            submitted_data=submitted_data,
            ip_address=ip_address,
            country=country,
            city=city,
            user_agent=user_agent,
            idempotency_key=idempotency_key
        )
        
        self.db.add(submission)
        self.db.commit()
        self.db.refresh(submission)
        
        logger.info(f"Submission created: {submission.id} for widget {widget_id}")
        
        # Trigger background side effects (fire and forget)
        await side_effect_service.process_submission_side_effects(
            submission.id, 
            submitted_data
        )
        
        return submission
    
    def get_submissions_for_tenant(
        self, 
        tenant_id: int, 
        widget_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Submission]:
        """Get submissions for a tenant with optional widget filtering."""
        query = self.db.query(Submission).filter(Submission.tenant_id == tenant_id)
        
        if widget_id:
            query = query.filter(Submission.widget_id == widget_id)
        
        return query.order_by(desc(Submission.created_at)).offset(offset).limit(limit).all()
    
    def count_submissions_for_tenant(self, tenant_id: int, widget_id: Optional[str] = None) -> int:
        """Count total submissions for a tenant."""
        query = self.db.query(func.count(Submission.id)).filter(Submission.tenant_id == tenant_id)
        
        if widget_id:
            query = query.filter(Submission.widget_id == widget_id)
        
        return query.scalar()