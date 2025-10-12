from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class DataSource(Base):
    __tablename__ = "data_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    competitor_id = Column(Integer, ForeignKey("competitors.id"), nullable=False)
    source_type = Column(String, nullable=False)  # website, blog, social_media, news
    url = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    last_scraped = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    competitor = relationship("Competitor", back_populates="data_sources")
    raw_contents = relationship("RawContent", back_populates="data_source")