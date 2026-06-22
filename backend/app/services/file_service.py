"""File upload service — local storage with optional S3 backend.

Handles profile images, chat media, medical documents.
Falls back to local filesystem when S3 is not configured.
"""

import os
import uuid
import shutil
from datetime import datetime, timezone
from typing import Optional, Protocol
from pathlib import Path

from app.core.config import settings


# ── Storage Protocol ──

class StorageBackend(Protocol):
    async def save(self, file_data: bytes, key: str, content_type: str) -> str:
        """Save file and return public URL."""
        ...

    async def delete(self, key: str) -> bool:
        """Delete a file by key."""
        ...


# ── Local Storage ──

class LocalStorage:
    """Store files on local filesystem."""

    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir or settings.UPLOAD_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, file_data: bytes, key: str, content_type: str) -> str:
        file_path = self.base_dir / key
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(file_data)
        return f"/uploads/{key}"

    async def delete(self, key: str) -> bool:
        file_path = self.base_dir / key
        if file_path.exists():
            file_path.unlink()
            return True
        return False


# ── S3 Storage (placeholder — requires boto3) ──

class S3Storage:
    """Store files on S3-compatible storage (AWS, MinIO, DigitalOcean Spaces).

    TODO: Install boto3 and implement:
        import boto3
        self.client = boto3.client('s3', ...)
    """

    def __init__(self):
        self.bucket = settings.S3_BUCKET
        self.region = settings.S3_REGION

    async def save(self, file_data: bytes, key: str, content_type: str) -> str:
        # Placeholder — would use boto3 in production
        # self.client.put_object(Bucket=self.bucket, Key=key, Body=file_data, ContentType=content_type)
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{key}"

    async def delete(self, key: str) -> bool:
        # self.client.delete_object(Bucket=self.bucket, Key=key)
        return True


# ── File Service ──

CATEGORY_DIRS = {
    "avatar": "avatars",
    "chat": "chat_media",
    "document": "documents",
    "prescription": "prescriptions",
    "license": "licenses",
}

ALLOWED_CONTENT_TYPES = {
    "avatar": {"image/jpeg", "image/png", "image/webp"},
    "chat": {"image/jpeg", "image/png", "image/webp", "application/pdf", "audio/mpeg", "audio/ogg"},
    "document": {"application/pdf", "image/jpeg", "image/png"},
    "prescription": {"application/pdf", "image/jpeg", "image/png"},
    "license": {"application/pdf", "image/jpeg", "image/png"},
}

MAX_SIZES = {
    "avatar": 2 * 1024 * 1024,       # 2 MB
    "chat": 10 * 1024 * 1024,         # 10 MB
    "document": 10 * 1024 * 1024,     # 10 MB
    "prescription": 5 * 1024 * 1024,  # 5 MB
    "license": 5 * 1024 * 1024,       # 5 MB
}


def get_storage() -> StorageBackend:
    """Get the appropriate storage backend."""
    if settings.S3_BUCKET and settings.S3_ACCESS_KEY:
        return S3Storage()
    return LocalStorage()


class FileService:
    def __init__(self, storage: Optional[StorageBackend] = None):
        self.storage = storage or get_storage()

    def validate(self, file_data: bytes, content_type: str, category: str) -> Optional[str]:
        """Validate file. Returns error message or None if valid."""
        if category not in ALLOWED_CONTENT_TYPES:
            return "INVALID_CATEGORY"

        allowed = ALLOWED_CONTENT_TYPES[category]
        if content_type not in allowed:
            return "INVALID_FILE_TYPE"

        max_size = MAX_SIZES.get(category, 10 * 1024 * 1024)
        if len(file_data) > max_size:
            return "FILE_TOO_LARGE"

        return None

    async def upload(
        self,
        file_data: bytes,
        content_type: str,
        category: str,
        user_id: uuid.UUID,
        original_filename: str = "",
    ) -> dict:
        """Upload a file and return metadata."""
        error = self.validate(file_data, content_type, category)
        if error:
            raise ValueError(error)

        # Generate unique key
        ext = _ext_from_content_type(content_type)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        unique = uuid.uuid4().hex[:8]
        directory = CATEGORY_DIRS.get(category, "misc")
        key = f"{directory}/{user_id}/{timestamp}_{unique}{ext}"

        # Save
        url = await self.storage.save(file_data, key, content_type)

        return {
            "url": url,
            "key": key,
            "size": len(file_data),
            "content_type": content_type,
            "category": category,
            "original_filename": original_filename,
        }

    async def delete(self, key: str) -> bool:
        return await self.storage.delete(key)


def _ext_from_content_type(ct: str) -> str:
    mapping = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "application/pdf": ".pdf",
        "audio/mpeg": ".mp3",
        "audio/ogg": ".ogg",
    }
    return mapping.get(ct, ".bin")
