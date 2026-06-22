"""Community endpoints — posts, comments, likes."""

import uuid
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.api.v1.deps import get_current_active_user
from app.models.user import User
from app.models.community import Post, Comment, PostLike
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.auth import MessageResponse

router = APIRouter(prefix="/posts", tags=["Community"])


# ── Schemas ──

class PostCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    is_anonymous: bool = False


class CommentCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    is_anonymous: bool = False


class PostOut(BaseModel):
    id: str
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None
    content: str
    is_anonymous: bool
    likes_count: int
    comments_count: int
    is_liked: bool = False
    created_at: str


class CommentOut(BaseModel):
    id: str
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    content: str
    is_anonymous: bool
    created_at: str


# ── Endpoints ──

@router.get("", response_model=PaginatedResponse)
async def list_posts(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List community posts (paginated)."""
    base = select(Post).where(Post.deleted_at == None, Post.is_hidden == False)

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = (
        base.order_by(Post.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    result = await db.execute(query)
    posts = result.scalars().all()

    # Check likes for current user
    post_ids = [p.id for p in posts]
    liked_q = select(PostLike.post_id).where(
        PostLike.user_id == current_user.id,
        PostLike.post_id.in_(post_ids),
    )
    liked_result = await db.execute(liked_q)
    liked_set = {row[0] for row in liked_result.all()}

    # Load user names
    user_ids = [p.user_id for p in posts if not p.is_anonymous]
    users_map = {}
    if user_ids:
        users_q = select(User).where(User.id.in_(user_ids))
        users_result = await db.execute(users_q)
        for u in users_result.scalars().all():
            users_map[u.id] = u

    data = []
    for p in posts:
        user = users_map.get(p.user_id)
        data.append({
            "id": str(p.id),
            "user_id": str(p.user_id) if not p.is_anonymous else None,
            "user_name": user.name if user and not p.is_anonymous else "مجهولة",
            "user_avatar": user.avatar_url if user and not p.is_anonymous else None,
            "content": p.content,
            "is_anonymous": p.is_anonymous,
            "likes_count": p.likes_count,
            "comments_count": p.comments_count,
            "is_liked": p.id in liked_set,
            "created_at": p.created_at.isoformat(),
        })

    pages = (total + limit - 1) // limit if limit else 1
    return PaginatedResponse(
        data=data,
        meta=PaginationMeta(total=total, page=page, limit=limit, pages=pages),
    )


@router.post("", status_code=201)
async def create_post(
    body: PostCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new community post."""
    post = Post(
        user_id=current_user.id,
        content=body.content,
        is_anonymous=body.is_anonymous,
    )
    db.add(post)
    await db.flush()

    return PostOut(
        id=str(post.id),
        user_id=str(current_user.id) if not body.is_anonymous else None,
        user_name=current_user.name if not body.is_anonymous else "مجهولة",
        user_avatar=current_user.avatar_url if not body.is_anonymous else None,
        content=post.content,
        is_anonymous=post.is_anonymous,
        likes_count=0,
        comments_count=0,
        is_liked=False,
        created_at=post.created_at.isoformat(),
    )


@router.delete("/{post_id}", response_model=MessageResponse)
async def delete_post(
    post_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete own post (soft delete)."""
    post = await db.get(Post, post_id)
    if not post or post.deleted_at is not None:
        raise HTTPException(status_code=404, detail={
            "code": "POST_NOT_FOUND", "message": "Post not found",
            "message_ar": "المنشور غير موجود",
        })
    if post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail={
            "code": "NOT_YOUR_POST", "message": "Not your post",
            "message_ar": "هذا ليس منشورك",
        })
    post.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    return MessageResponse(message="Post deleted", message_ar="تم حذف المنشور")


@router.post("/{post_id}/like")
async def toggle_like(
    post_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggle like on a post."""
    post = await db.get(Post, post_id)
    if not post or post.deleted_at is not None:
        raise HTTPException(status_code=404, detail={
            "code": "POST_NOT_FOUND", "message": "Post not found",
            "message_ar": "المنشور غير موجود",
        })

    existing = await db.execute(
        select(PostLike).where(
            PostLike.post_id == post_id,
            PostLike.user_id == current_user.id,
        )
    )
    like = existing.scalar_one_or_none()

    if like:
        await db.delete(like)
        post.likes_count = max(0, post.likes_count - 1)
        is_liked = False
    else:
        db.add(PostLike(post_id=post_id, user_id=current_user.id))
        post.likes_count += 1
        is_liked = True

    await db.flush()
    return {"likes_count": post.likes_count, "is_liked": is_liked}


@router.get("/{post_id}/comments")
async def list_comments(
    post_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get comments for a post."""
    result = await db.execute(
        select(Comment, User)
        .join(User, Comment.user_id == User.id)
        .where(Comment.post_id == post_id, Comment.deleted_at == None)
        .order_by(Comment.created_at.asc())
    )
    rows = result.all()

    return {
        "data": [
            {
                "id": str(comment.id),
                "user_id": str(comment.user_id) if not comment.is_anonymous else None,
                "user_name": user.name if not comment.is_anonymous else "مجهولة",
                "content": comment.content,
                "is_anonymous": comment.is_anonymous,
                "created_at": comment.created_at.isoformat(),
            }
            for comment, user in rows
        ]
    }


@router.post("/{post_id}/comments", status_code=201)
async def add_comment(
    post_id: uuid.UUID,
    body: CommentCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Add comment to a post."""
    post = await db.get(Post, post_id)
    if not post or post.deleted_at is not None:
        raise HTTPException(status_code=404, detail={
            "code": "POST_NOT_FOUND", "message": "Post not found",
            "message_ar": "المنشور غير موجود",
        })

    comment = Comment(
        post_id=post_id,
        user_id=current_user.id,
        content=body.content,
        is_anonymous=body.is_anonymous,
    )
    db.add(comment)
    post.comments_count += 1
    await db.flush()

    return CommentOut(
        id=str(comment.id),
        user_id=str(current_user.id) if not body.is_anonymous else None,
        user_name=current_user.name if not body.is_anonymous else "مجهولة",
        content=comment.content,
        is_anonymous=comment.is_anonymous,
        created_at=comment.created_at.isoformat(),
    )


@router.post("/{post_id}/report", response_model=MessageResponse)
async def report_post(
    post_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Report a post for moderation."""
    post = await db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail={
            "code": "POST_NOT_FOUND", "message": "Post not found",
            "message_ar": "المنشور غير موجود",
        })
    post.is_reported = True
    await db.flush()
    return MessageResponse(message="Post reported", message_ar="تم الإبلاغ عن المنشور")
