from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User
from app.schemas.comment_schema import CommentCreate, CommentResponse
from app.db import get_db
from app.dependencies import get_current_user
from typing import List


router = APIRouter(prefix="/comments", tags=["Comments"])

@router.post("/", response_model=CommentResponse)
def create_comment(
    comment: CommentCreate,
    db: Session = Depends(get_db),
    user_info: dict = Depends(get_current_user)
):
    if user_info is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    user = db.query(User).filter_by(id=user_info["id"]).first()
    if not user:
        user = User(
            id=user_info["id"],
            email=user_info["email"],
            username=user_info["username"]
        )
        db.add(user)
        db.commit()

    post = db.query(Post).filter(Post.id == comment.post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    new_comment = Comment(
        text=comment.text,
        user_id=user_info["id"],
        post_id=comment.post_id,
        establishment=post.establishment
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    # ✅ Re-fetch the comment with joins
    enriched_comment = (
        db.query(Comment)
        .filter(Comment.id == new_comment.id)
        .options(joinedload(Comment.user), joinedload(Comment.post))
        .first()
    )

    return {
        "id": enriched_comment.id,
        "text": enriched_comment.text,
        "timestamp": enriched_comment.timestamp,
        "user_id": enriched_comment.user_id,
        "post_id": enriched_comment.post_id,
        "username": enriched_comment.user.username,
        "establishment": enriched_comment.post.establishment,
    }


@router.get("/post/{post_id}", response_model=List[CommentResponse])
def get_comments_for_post(post_id: int, db: Session = Depends(get_db)):
    comments = (
        db.query(Comment)
        .filter(Comment.post_id == post_id)
        .options(
            joinedload(Comment.user),
            joinedload(Comment.post)
        )
        .all()
    )

    enriched = []
    for c in comments:
        if not c.user or not c.post:
            raise HTTPException(status_code=404, detail="Missing user or post")

        enriched.append({
            "id": c.id,
            "text": c.text,
            "timestamp": c.timestamp,
            "user_id": c.user_id,
            "post_id": c.post_id,
            "username": c.user.username,
            "establishment": c.post.establishment
        })

    return enriched


@router.delete("/{comment_id}", status_code=204)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    user_info: dict = Depends(get_current_user)
):
    if user_info is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.user_id != user_info["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")

    db.delete(comment)
    db.commit()
    

