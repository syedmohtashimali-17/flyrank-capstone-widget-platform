from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from core.database import Base


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    widget_id = Column(String, ForeignKey("widgets.id"), nullable=False, index=True)
    tenant_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    submitted_data = Column(JSON, nullable=False)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    user_agent = Column(Text, nullable=True)
    idempotency_key = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    widget = relationship("Widget", back_populates="submissions")
    tenant = relationship("User", back_populates="submissions")

    # Indexes
    __table_args__ = (
        Index("idx_tenant_created", "tenant_id", "created_at"),
        Index("idx_widget_tenant", "widget_id", "tenant_id"),
        Index("idx_idempotency_widget", "idempotency_key", "widget_id", unique=True),
    )