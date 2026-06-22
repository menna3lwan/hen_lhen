"""File upload endpoints — images, documents, chat media."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.v1.deps import get_current_active_user
from app.models.user import User
from app.services.file_service import FileService

router = APIRouter(prefix="/uploads", tags=["Uploads"])

ERROR_MAP = {
    "INVALID_CATEGORY": (400, "Invalid file category", "تصنيف الملف غير صالح"),
    "INVALID_FILE_TYPE": (400, "File type not allowed", "نوع الملف غير مسموح"),
    "FILE_TOO_LARGE": (413, "File too large", "حجم الملف كبير جداً"),
}


@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    category: str = Form("document"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a file.

    Categories: avatar, chat, document, prescription, license
    """
    file_data = await file.read()
    content_type = file.content_type or "application/octet-stream"

    svc = FileService()
    try:
        result = await svc.upload(
            file_data=file_data,
            content_type=content_type,
            category=category,
            user_id=current_user.id,
            original_filename=file.filename or "",
        )
    except ValueError as e:
        code = str(e)
        if code in ERROR_MAP:
            status, msg, msg_ar = ERROR_MAP[code]
            raise HTTPException(status_code=status, detail={
                "code": code, "message": msg, "message_ar": msg_ar,
            })
        raise HTTPException(status_code=400, detail={
            "code": "UPLOAD_ERROR", "message": str(e), "message_ar": "خطأ في رفع الملف",
        })

    return result


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a profile avatar. Auto-updates user record."""
    file_data = await file.read()
    content_type = file.content_type or "image/jpeg"

    svc = FileService()
    try:
        result = await svc.upload(
            file_data=file_data,
            content_type=content_type,
            category="avatar",
            user_id=current_user.id,
            original_filename=file.filename or "",
        )
    except ValueError as e:
        code = str(e)
        if code in ERROR_MAP:
            status, msg, msg_ar = ERROR_MAP[code]
            raise HTTPException(status_code=status, detail={
                "code": code, "message": msg, "message_ar": msg_ar,
            })
        raise

    # Update user avatar URL
    current_user.avatar_url = result["url"]
    await db.commit()

    return result
