from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from core.database import get_db
from models.user import User
from routers.auth import get_current_user
from schemas.widget import WidgetCreate, WidgetUpdate, WidgetResponse, EmbedSnippet
from services.widget_service import WidgetService

router = APIRouter(prefix="/widgets", tags=["widgets"])


@router.post("", response_model=WidgetResponse, status_code=status.HTTP_201_CREATED)
def create_widget(
    widget_data: WidgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new widget."""
    service = WidgetService(db)
    widget = service.create_widget(widget_data, current_user.id)
    return widget


@router.get("", response_model=List[WidgetResponse])
def list_widgets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all widgets for the authenticated user."""
    service = WidgetService(db)
    widgets = service.get_user_widgets(current_user.id)
    return widgets


@router.get("/{widget_id}", response_model=WidgetResponse)
def get_widget(
    widget_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific widget by ID."""
    service = WidgetService(db)
    widget = service.get_widget_by_id(widget_id, current_user.id)
    return widget


@router.put("/{widget_id}", response_model=WidgetResponse)
def update_widget(
    widget_id: str,
    widget_data: WidgetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a widget."""
    service = WidgetService(db)
    widget = service.update_widget(widget_id, widget_data, current_user.id)
    return widget


@router.delete("/{widget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_widget(
    widget_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a widget."""
    service = WidgetService(db)
    service.delete_widget(widget_id, current_user.id)


@router.get("/{widget_id}/embed", response_model=EmbedSnippet)
def get_embed_snippet(
    widget_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the embed snippet for a widget."""
    service = WidgetService(db)
    # Verify widget exists and belongs to user
    widget = service.get_widget_by_id(widget_id, current_user.id)
    
    snippet = service.generate_embed_snippet(widget_id)
    return EmbedSnippet(widget_id=widget_id, snippet=snippet)