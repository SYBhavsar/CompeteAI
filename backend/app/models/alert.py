from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Alert(Base):
    """Alert configuration for monitoring competitors"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    competitor_id = Column(Integer, ForeignKey("competitors.id"), nullable=True)
    alert_type = Column(String(50), nullable=False)  # sentiment_change, new_content, keyword_match
    conditions = Column(JSON, nullable=True)  # Alert conditions
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="alerts")
    competitor = relationship("Competitor", backref="alerts")
    notifications = relationship("Notification", back_populates="alert", cascade="all, delete-orphan")


class Notification(Base):
    """Notification triggered by alerts"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=True)
    message = Column(String(500), nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", backref="notifications")
    alert = relationship("Alert", back_populates="notifications")