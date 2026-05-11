"""
SQLAlchemy model for admin activity logs.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from app.db.database import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    registration_id = Column(Integer, ForeignKey("registrations.id"), nullable=True, index=True)
    event_type = Column(String(50), nullable=False)   # e.g. "CHECK_STARTED", "RESULT_FOUND", "EMAIL_SENT", "ERROR"
    message = Column(Text, nullable=False)
    symbol_number = Column(String(20), nullable=True)
    source_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<ActivityLog event={self.event_type} symbol={self.symbol_number}>"
