from pydantic import BaseModel, StringConstraints
from typing import Annotated
from datetime import datetime

# ✅ Enforce 100-character max on comment text
CommentText = Annotated[str, StringConstraints(max_length=100)]

class CommentCreate(BaseModel):
    text: CommentText  # ✅ apply the constraint here
    post_id: int

class CommentResponse(BaseModel):
    id: int
    text: str
    timestamp: datetime
    user_id: str
    post_id: int
    establishment: str
    username: str

    class Config:
        from_attributes = True

CommentResponse.update_forward_refs()
