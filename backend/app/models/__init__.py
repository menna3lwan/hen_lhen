"""Import all models so Alembic discovers them."""

from app.models.user import User, Patient, Doctor, UserRole, VerificationStatus
from app.models.specialty import Specialty
from app.models.branch import Branch, BranchSchedule
from app.models.appointment import Appointment, AppointmentType, AppointmentStatus
from app.models.payment import Payment, PaymentStatus
from app.models.promo_code import PromoCode, PromoType
from app.models.chat import ChatRoom, Message, ChatStatus, MessageType
from app.models.community import Post, Comment, PostLike
from app.models.review import Review
from app.models.notification import Notification, NotificationType
from app.models.favorite import Favorite
from app.models.device import Device, DevicePlatform
from app.models.audit_log import AuditLog
from app.models.auth import RefreshToken
from app.models.medical_record import MedicalRecord, RecordType

__all__ = [
    "User", "Patient", "Doctor", "UserRole", "VerificationStatus",
    "Specialty",
    "Branch", "BranchSchedule",
    "Appointment", "AppointmentType", "AppointmentStatus",
    "Payment", "PaymentStatus",
    "PromoCode", "PromoType",
    "ChatRoom", "Message", "ChatStatus", "MessageType",
    "Post", "Comment", "PostLike",
    "Review",
    "Notification", "NotificationType",
    "Favorite",
    "Device", "DevicePlatform",
    "AuditLog",
    "RefreshToken",
    "MedicalRecord", "RecordType",
]
