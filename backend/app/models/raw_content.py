from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class RawContent(Base):
    __tablename__ = "raw_content"
    
    id = Column(Integer, primary_key=True, index=True)
    data_source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=False)
    content = Column(Text, nullable=False)
    content_type = Column(String)  # text/html, application/json, text/plain
    url = Column(String, nullable=False)
    content_hash = Column(String, index=True)  # For deduplication
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    data_source = relationship("DataSource", back_populates="raw_contents")
    processed_insights = relationship("ProcessedInsights", back_populates="raw_content", uselist=False)