from sqlalchemy import Column, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ScrapingSchedule(Base):
    __tablename__ = "scraping_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    data_source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=False, unique=True)
    frequency_minutes = Column(Integer, nullable=False)  # How often to scrape in minutes
    next_run = Column(DateTime(timezone=True), nullable=False)  # When to run next
    last_run = Column(DateTime(timezone=True))  # When it was last run
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship (one-to-one with DataSource)
    data_source = relationship("DataSource", back_populates="scraping_schedule")