from pydantic import BaseModel
from pydantic import StringConstraints
from typing import Annotated, Optional
from datetime import datetime

# ✅ Use Annotated to declare constraints
PostText = Annotated[str, StringConstraints(max_length=200)]

class PostCreate(BaseModel):
    text: PostText
    establishment: str
    latitude: float
    longitude: float

class PostRead(BaseModel):
    id: int
    text: str
    establishment: str
    latitude: Optional[float]
    longitude: Optional[float]
    timestamp: datetime
    upvotes: int
    user_id: str
    username: str
    user_has_upvoted: Optional[bool] = False

    class Config:
        from_attributes = True


class UpvoteRequest(BaseModel):
    user_id: str
