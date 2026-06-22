"""Post, Comment, PostLike models — community features."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String, Boolean, Integer, ForeignKey, Text, DateTime, Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.base import Base, TimestampMixin, SoftDeleteMixin


class Post(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "posts"
    __table_args__ = (
        Index("idx_posts_created", "created_at"),
        Index("idx_posts_user", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    likes_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comments_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_reported: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(lazy="joined")
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="post", lazy="noload", cascade="all, delete-orphan"
    )
    likes: Mapped[list["PostLike"]] = relationship(
        back_populates="post", lazy="noload", cascade="all, delete-orphan"
    )


class Comment(Base, SoftDeleteMixin):
    __tablename__ = "comments"
    __table_args__ = (
        Index("idx_comments_post", "post_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    post: Mapped["Post"] = relationship(back_populates="comments")
    user: Mapped["User"] = relationship(lazy="joined")


class PostLike(Base):
    __tablename__ = "post_likes"

    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    post: Mapped["Post"] = relationship(back_populates="likes")


from app.models.user import User
