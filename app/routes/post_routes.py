from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from app.db import get_db
from app.models.post import Post
from app.models.vote import Vote
from app.schemas.post_schema import PostCreate, PostRead, UpvoteRequest
from typing import List, Annotated, Optional
from datetime import datetime, timedelta
from app.dependencies import get_current_user

from math import radians, cos, sin, acos

router = APIRouter()

@router.get("/posts")
def get_posts(
    db: Session = Depends(get_db),
    user: Optional[dict] = Depends(get_current_user),
    user_lat: float = Query(..., description="User latitude"),
    user_lng: float = Query(..., description="User longitude"),
    radius_feet: float = Query(1500, description="Search radius in feet (min 1500, max 15840)")
):
    # Step 1: Clean up old posts
    threshold = datetime.utcnow() - timedelta(hours=24)
    db.query(Post).filter(Post.timestamp < threshold).delete()
    db.commit()

    # Step 2: Convert feet to miles
    radius_miles = radius_feet / 5280

    # Step 3: Manually filter by distance
    all_posts = (
    db.query(Post)
    .options(joinedload(Post.comments))
    .filter(Post.timestamp >= threshold)
    .all()
)
    posts = []
    for post in all_posts:
        if post.latitude is None or post.longitude is None:
            continue

        # Haversine formula (simplified)
        lat1, lon1 = radians(user_lat), radians(user_lng)
        lat2, lon2 = radians(post.latitude), radians(post.longitude)
        earth_radius = 3958.8  # miles

        distance = earth_radius * acos(
            sin(lat1) * sin(lat2) +
            cos(lat1) * cos(lat2) * cos(lon2 - lon1)
        )

        if distance <= radius_miles:
            posts.append(post)

    # user_has_upvoted flag
    post_with_flags = []
    for post in posts:
        has_voted = False
        if user:
            has_voted = (
                db.query(Vote)
                .filter_by(post_id=post.id, user_id=user["id"])
                .first()
                is not None
            )
        post_dict = post.__dict__.copy()
        post_dict["user_has_upvoted"] = has_voted
        post_dict["comment_count"] = len(post.comments)
        post_dict["username"] = post.user.username if post.user else "Unknown"

        post_with_flags.append(post_dict)

    return post_with_flags


@router.post("/posts", response_model=PostRead)
def create_post(
    post: PostCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    new_post = Post(
        text=post.text,
        establishment=post.establishment,
        user_id=user["id"],
        latitude=post.latitude,
        longitude=post.longitude,
        username=user.get("username")  # ✅ store username in the Post
)
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    print("✅ Created post:", new_post.__dict__)  # 👈 debug log

    return new_post


@router.post("/posts/{post_id}/upvote", status_code=status.HTTP_200_OK)
def upvote_post(
    post_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    existing_vote = db.query(Vote).filter_by(user_id=user["id"], post_id=post_id).first()

    if existing_vote:
        db.delete(existing_vote)
        post.upvotes = max(0, post.upvotes - 1)
        db.commit()
        return {"message": "Upvote removed", "upvotes": post.upvotes}

    vote = Vote(user_id=user["id"], post_id=post_id)
    db.add(vote)
    post.upvotes += 1
    db.commit()

    return {"message": "Upvoted", "upvotes": post.upvotes}


@router.delete("/posts/{post_id}")
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.user_id != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this post")

    db.delete(post)
    db.commit()
    return {"message": "Post deleted"}

