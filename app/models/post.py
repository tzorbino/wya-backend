from sqlalchemy import Column, Integer, String, DateTime, Float
from datetime import datetime
from app.db import Base
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String(280), nullable=False)
    establishment = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    upvotes = Column(Integer, default=0)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)  # 👈 Make sure ForeignKey is here
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    username = Column(String, nullable=False)

    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    user = relationship("User", back_populates="posts")  # ✅ Add this line
