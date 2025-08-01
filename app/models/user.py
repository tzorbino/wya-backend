from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship  # ✅ Needed for relationship
from app.db import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="user", cascade="all, delete-orphan")  # ✅
