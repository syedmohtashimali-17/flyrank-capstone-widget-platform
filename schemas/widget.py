from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator


class FormField(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    label: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., pattern="^(text|email|tel|textarea|select|checkbox|radio)$")
    required: bool = False
    options: Optional[List[str]] = None  # For select, checkbox, radio fields


class WidgetCreate(BaseModel):
    type: str = Field(..., pattern="^(signup|contact|cta)$")
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    form_fields: List[FormField] = Field(..., min_length=1, max_length=20)
    button_text: str = Field(default="Submit", max_length=50)
    display_options: Optional[Dict[str, Any]] = None

    @field_validator('form_fields')
    @classmethod
    def validate_form_fields(cls, fields):
        field_names = [field.name for field in fields]
        if len(field_names) != len(set(field_names)):
            raise ValueError("Form field names must be unique")
        return fields


class WidgetUpdate(BaseModel):
    type: Optional[str] = Field(None, pattern="^(signup|contact|cta)$")
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    form_fields: Optional[List[FormField]] = Field(None, min_length=1, max_length=20)
    button_text: Optional[str] = Field(None, max_length=50)
    display_options: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

    @field_validator('form_fields')
    @classmethod
    def validate_form_fields(cls, fields):
        if fields:
            field_names = [field.name for field in fields]
            if len(field_names) != len(set(field_names)):
                raise ValueError("Form field names must be unique")
        return fields


class WidgetResponse(BaseModel):
    id: str
    owner_id: int
    type: str
    title: str
    description: Optional[str]
    form_fields: List[Dict[str, Any]]
    button_text: str
    display_options: Optional[Dict[str, Any]]
    is_active: bool
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WidgetConfig(BaseModel):
    """Public configuration for widget rendering."""
    id: str
    type: str
    title: str
    description: Optional[str]
    form_fields: List[Dict[str, Any]]
    button_text: str
    display_options: Optional[Dict[str, Any]]
    version: int


class EmbedSnippet(BaseModel):
    widget_id: str
    snippet: str