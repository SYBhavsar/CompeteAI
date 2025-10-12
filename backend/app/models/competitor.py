from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Competitor(Base):
    __tablename__ = "competitors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    domain = Column(String)
    industry = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="competitors")
    data_sources = relationship("DataSource", back_populates="competitor")