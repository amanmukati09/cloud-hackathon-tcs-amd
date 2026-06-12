# backend/routers/community.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from models import get_db, User, CommunityPost, CommunityComment, PostLike, CommentLike
from auth import get_current_user

router = APIRouter()

class PostCreate(BaseModel):
    content: str

class CommentCreate(BaseModel):
    content: str

# ── Get all posts ─────────────────────────────────────
@router.get("/community/posts")
async def get_posts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    posts = db.query(CommunityPost).order_by(CommunityPost.created_at.desc()).limit(50).all()
    result = []
    for p in posts:
        like_count = db.query(PostLike).filter(PostLike.post_id == p.id).count()
        user_liked = db.query(PostLike).filter(
            PostLike.post_id == p.id, PostLike.user_id == current_user.id
        ).first() is not None
        result.append({
            "id": p.id,
            "author": p.author.email,
            "content": p.content,
            "timestamp": p.created_at.strftime("%Y-%m-%d %H:%M"),
            "likes": like_count,
            "user_liked": user_liked,
            "comment_count": db.query(CommunityComment).filter(CommunityComment.post_id == p.id).count()
        })
    return result

# ── Create post ───────────────────────────────────────
@router.post("/community/posts")
async def create_post(
    payload: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post = CommunityPost(user_id=current_user.id, content=payload.content.strip())
    db.add(post)
    db.commit()
    return {"status": "success", "post_id": post.id}

# ── Delete post ───────────────────────────────────────
@router.delete("/community/posts/{post_id}")
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied")
    db.delete(post)
    db.commit()
    return {"status": "success"}

# ── Like/unlike post ──────────────────────────────────
@router.post("/community/posts/{post_id}/like")
async def like_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing = db.query(PostLike).filter(
        PostLike.post_id == post_id, PostLike.user_id == current_user.id
    ).first()
    if existing:
        db.delete(existing)
        db.commit()
        return {"status": "unliked"}
    db.add(PostLike(post_id=post_id, user_id=current_user.id))
    db.commit()
    return {"status": "liked"}

# ── Get comments for a post ───────────────────────────
@router.get("/community/posts/{post_id}/comments")
async def get_comments(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    comments = db.query(CommunityComment).filter(
        CommunityComment.post_id == post_id
    ).order_by(CommunityComment.created_at.asc()).all()
    result = []
    for c in comments:
        like_count = db.query(CommentLike).filter(CommentLike.comment_id == c.id).count()
        user_liked = db.query(CommentLike).filter(
            CommentLike.comment_id == c.id, CommentLike.user_id == current_user.id
        ).first() is not None
        result.append({
            "id": c.id,
            "author": c.author.email,
            "content": c.content,
            "timestamp": c.created_at.strftime("%Y-%m-%d %H:%M"),
            "likes": like_count,
            "user_liked": user_liked
        })
    return result

# ── Add comment to post ───────────────────────────────
@router.post("/community/posts/{post_id}/comments")
async def add_comment(
    post_id: int,
    payload: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    comment = CommunityComment(
        post_id=post_id,
        user_id=current_user.id,
        content=payload.content.strip()
    )
    db.add(comment)
    db.commit()
    return {"status": "success"}

# ── Delete comment ────────────────────────────────────
@router.delete("/community/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    comment = db.query(CommunityComment).filter(CommunityComment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access Denied")
    db.delete(comment)
    db.commit()
    return {"status": "success"}

# ── Like/unlike comment ───────────────────────────────
@router.post("/community/comments/{comment_id}/like")
async def like_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing = db.query(CommentLike).filter(
        CommentLike.comment_id == comment_id, CommentLike.user_id == current_user.id
    ).first()
    if existing:
        db.delete(existing)
        db.commit()
        return {"status": "unliked"}
    db.add(CommentLike(comment_id=comment_id, user_id=current_user.id))
    db.commit()
    return {"status": "liked"}