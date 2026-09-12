import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from models.widget import Widget
from models.user import User
from schemas.widget import WidgetCreate, WidgetUpdate
from core.errors import NotFoundError
from core.config import settings


class WidgetService:
    def __init__(self, db: Session):
        self.db = db

    def create_widget(self, widget_data: WidgetCreate, owner_id: int) -> Widget:
        """Create a new widget for the authenticated user."""
        widget_id = str(uuid.uuid4())
        
        db_widget = Widget(
            id=widget_id,
            owner_id=owner_id,
            type=widget_data.type,
            title=widget_data.title,
            description=widget_data.description,
            form_fields=[field.model_dump() for field in widget_data.form_fields],
            button_text=widget_data.button_text,
            display_options=widget_data.display_options or {},
            is_active=True,
            version=1
        )
        
        self.db.add(db_widget)
        self.db.commit()
        self.db.refresh(db_widget)
        return db_widget

    def get_user_widgets(self, owner_id: int) -> List[Widget]:
        """Get all widgets for a specific user (tenant isolation)."""
        return self.db.query(Widget).filter(Widget.owner_id == owner_id).all()

    def get_widget_by_id(self, widget_id: str, owner_id: int) -> Widget:
        """Get a specific widget by ID with tenant isolation."""
        widget = self.db.query(Widget).filter(
            Widget.id == widget_id,
            Widget.owner_id == owner_id
        ).first()
        
        if not widget:
            raise NotFoundError("Widget not found")
        
        return widget

    def get_widget_public(self, widget_id: str) -> Optional[Widget]:
        """Get widget for public access (no tenant restriction)."""
        return self.db.query(Widget).filter(
            Widget.id == widget_id,
            Widget.is_active == True
        ).first()

    def update_widget(self, widget_id: str, widget_data: WidgetUpdate, owner_id: int) -> Widget:
        """Update a widget with tenant isolation."""
        widget = self.get_widget_by_id(widget_id, owner_id)
        
        update_data = widget_data.model_dump(exclude_unset=True)
        
        if 'form_fields' in update_data and update_data['form_fields']:
            update_data['form_fields'] = [field.model_dump() for field in widget_data.form_fields]
        
        for field, value in update_data.items():
            setattr(widget, field, value)
        
        self.db.commit()
        self.db.refresh(widget)
        return widget

    def delete_widget(self, widget_id: str, owner_id: int) -> None:
        """Delete a widget with tenant isolation."""
        widget = self.get_widget_by_id(widget_id, owner_id)
        self.db.delete(widget)
        self.db.commit()

    def generate_embed_snippet(self, widget_id: str) -> str:
        """Generate embed snippet for a widget."""
        return f'<script src="{settings.base_url}/static/widget.v1.js?id={widget_id}"></script>'