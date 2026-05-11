"""
SQLAlchemy model for student result monitoring registrations.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.db.database import Base


class Registration(Base):
    __tablename__ = "registrations"

    id = Column(Integer, primary_key=True, index=True)
    receiver_email = Column(String(255), nullable=False, index=True)
    symbol_number = Column(String(20), nullable=False, index=True)
    date_of_birth = Column(String(20), nullable=False)  # stored as string e.g. "2065/05/15"

    # Monitoring state
    is_active = Column(Boolean, default=True, nullable=False)
    result_found = Column(Boolean, default=False, nullable=False)
    result_data = Column(Text, nullable=True)         # JSON string of result when found
    email_sent = Column(Boolean, default=False, nullable=False)

    # Retry tracking
    check_count = Column(Integer, default=0, nullable=False)
    last_checked_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    def __repr__(self):
        return f"<Registration symbol={self.symbol_number} email={self.receiver_email}>"
