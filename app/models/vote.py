from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, UniqueConstraint
from datetime import datetime
from app.db import Base

class Vote(Base):
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)  # Removed ForeignKey
    post_id = Column(Integer, nullable=False)  # Removed ForeignKey
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "post_id", name="unique_user_post_vote"),
        {"extend_existing": True}  # Allows extending existing table definitions
    )
