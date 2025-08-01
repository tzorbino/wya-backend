from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db import Base
from app.models.user import User
from app.models.post import Post

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String(500), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  # ✅ now String
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)

    establishment = Column(String, nullable=True)
    username = Column(String, nullable=True)

    user = relationship("User", back_populates="comments")
    post = relationship("Post", back_populates="comments")
