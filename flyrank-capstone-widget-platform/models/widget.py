from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from core.database import Base


class Widget(Base):
    __tablename__ = "widgets"

    id = Column(String, primary_key=True, index=True)  # UUID string
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String(20), nullable=False)  # signup, contact, cta
    title = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    form_fields = Column(JSON, nullable=False)  # List of field definitions
    button_text = Column(String(50), default="Submit", nullable=False)
    display_options = Column(JSON, nullable=True)  # Position, styling etc
    is_active = Column(Boolean, default=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    owner = relationship("User", back_populates="widgets")
    submissions = relationship("Submission", back_populates="widget", cascade="all, delete-orphan")