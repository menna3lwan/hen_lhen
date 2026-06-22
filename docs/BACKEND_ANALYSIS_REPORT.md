# Backend Analysis Report — هُنَّ لَهُنَّ (Hen Lehen)
## Medical Consultation Platform — Full Backend Assessment

**Date:** June 2026
**Scope:** patient_app + doctor_app + shared packages
**Status:** Pre-Production (100% Mock Data — No Backend Exists)

---

# Phase 1 — Current Backend Analysis

## 1.1 Executive Summary

The project currently has **zero backend infrastructure**. Both applications (patient_app, doctor_app) operate entirely on hardcoded mock data with `Future.delayed()` simulating network latency. The `ApiClient` class wraps Dio configured to hit `https://api.henlehen.com/v1`, but **no endpoint is ever actually called**. Every feature must be built from scratch on the server side.

## 1.2 Features Inventory

### Patient App Features
| # | Feature | Current State | Backend Needed |
|---|---------|--------------|----------------|
| 1 | Registration (name, email, phone, governorate) | Mock — creates in-memory UserModel | YES |
| 2 | Login (email + password) | Hardcoded: `test@test.com` / `123456` | YES |
| 3 | Browse doctors by specialty | Static list of 8 mock doctors | YES |
| 4 | Search & filter doctors (name, specialty, rating, fee, experience) | Client-side filtering of mock list | YES |
| 5 | Doctor profile with reviews | Static mock data | YES |
| 6 | Appointment booking (date, time, type, promo code) | Creates in-memory appointment | YES |
| 7 | Payment processing | UI exists, no actual payment | YES |
| 8 | Promo codes (FIRST20, SAVE10) | Hardcoded client-side | YES |
| 9 | Appointment management (upcoming/completed/cancelled) | In-memory list | YES |
| 10 | Real-time chat | Simulated with `Future.delayed` auto-replies | YES |
| 11 | Community posts & comments (anonymous support) | In-memory mock data | YES |
| 12 | Notifications (appointment, message, promotion) | Static mock list | YES |
| 13 | Favorites (doctors) | In-memory `RxSet<String>` | YES |
| 14 | Profile management | In-memory updates | YES |
| 15 | Theme switching (light/dark) | Client-only | NO |
| 16 | Language switching (AR/EN) | Client-only | NO |
| 17 | Onboarding flow | Client-only | NO |

### Doctor App Features
| # | Feature | Current State | Backend Needed |
|---|---------|--------------|----------------|
| 1 | Registration (name, email, phone, specialty, license, experience, bio) | Mock — creates DoctorModel | YES |
| 2 | Login (email + password) | Hardcoded: `doctor@hen.com` / `123456` | YES |
| 3 | Pending approval flow | isPending flag, no real verification | YES |
| 4 | Dashboard (today's appointments, stats, earnings) | Mock data | YES |
| 5 | Appointment management (accept/reject/complete) | In-memory status changes | YES |
| 6 | Patient list with search | Static 5 mock patients | YES |
| 7 | Branch management (CRUD, toggle active) | In-memory list | YES |
| 8 | Chat with patients | Simulated auto-replies | YES |
| 9 | Earnings & reports | Hardcoded static numbers | YES |
| 10 | Profile editing | In-memory DoctorModel rebuild | YES |
| 11 | Settings (theme, language, logout) | Client-only | Partial |

## 1.3 API Layer Analysis

**Current state: Skeleton only.**

Both apps have identical `ApiClient` classes:
- Base URL: `https://api.henlehen.com/v1`
- Timeouts: 10s connect, 10s receive
- Interceptors: Placeholder for auth token injection and global error handling
- **No endpoint is called anywhere in the codebase**

Both apps have `AuthRepository` classes with commented-out API calls (`// TODO: Replace with actual API call`).

## 1.4 Data Flow

```
Current: UI → Controller → MockData (hardcoded) → UI
Target:  UI → Controller → Repository → ApiClient → Backend API → Database
```

## 1.5 Authentication Mechanism

**Current:** Hardcoded credential matching with no token, no session, no persistence.

- Patient login: `email == 'test@test.com' && password == '123456'`
- Doctor login: `email == 'doctor@hen.com' && password == '123456'`
- No JWT tokens
- No refresh token mechanism
- No token storage (SharedPreferences not used for auth)
- No session persistence — logout on app restart
- No password hashing
- No email verification
- No forgot password flow

## 1.6 Authorization Logic

**None.** No role-based access control. The apps are separate binaries (patient vs doctor) which provides basic separation, but there is no server-side enforcement.

## 1.7 Database Structure

**None exists.** All data lives in Dart classes with hardcoded values in `MockData`.

## 1.8 Third-Party Integrations

**None active.** Dependencies installed but unused:
- `dio: ^5.9.2` — HTTP client, configured but no real calls
- `cached_network_image: ^3.4.1` — Imported but no network images loaded
- `google_fonts` — Active (Cairo font)
- `shared_preferences` — In pubspec but not used

## 1.9 Notification Services

**None.** Mock `NotificationModel` list displayed in UI. No FCM, no APNs, no local notifications.

## 1.10 File & Media Management

**None.** Camera and file attachment buttons in chat screens are no-ops (`onTap: () => Navigator.pop(context)`). No image upload, no file storage, no CDN.

## 1.11 Real-Time Features

**None.** Chat is simulated:
- Hardcoded initial messages in Arabic
- `Future.delayed(2 seconds)` adds auto-reply "شكراً دكتورة على الاهتمام"
- No WebSocket, no Firebase, no real-time protocol

---

# Phase 2 — Backend Requirements Analysis

## 2.1 Authentication & Authorization

| Requirement | Priority | Description |
|-------------|----------|-------------|
| Email/Password Registration | CRITICAL | Separate flows for patients (name, email, phone, governorate) and doctors (+ specialty, license, experience, bio) |
| Email Verification | CRITICAL | OTP or magic link to verify email |
| Login with JWT | CRITICAL | Access token (short-lived) + refresh token (long-lived) |
| Token Refresh | CRITICAL | Silent token refresh before expiry |
| Password Reset | HIGH | Forgot password via email OTP |
| Doctor Approval Workflow | CRITICAL | Admin reviews doctor registration, verifies license |
| Role-Based Access Control | CRITICAL | Three roles: patient, doctor, admin |
| Social Login (Google/Apple) | MEDIUM | Optional — Egyptian market prefers email |
| Phone OTP Login | HIGH | Common in Egyptian apps |
| Session Management | HIGH | Device tracking, force logout |
| Account Deactivation | MEDIUM | GDPR/data-protection compliance |

## 2.2 User Management

| Requirement | Priority |
|-------------|----------|
| Patient CRUD | CRITICAL |
| Doctor CRUD + verification status | CRITICAL |
| Admin CRUD | HIGH |
| Profile photo upload | HIGH |
| Governorate-based location | HIGH |
| Blood type & medical info for patients | MEDIUM |
| License verification for doctors | CRITICAL |
| Doctor online/offline status | HIGH |

## 2.3 Appointments & Scheduling

| Requirement | Priority |
|-------------|----------|
| Doctor availability schedule (per branch, per day) | CRITICAL |
| Time slot management | CRITICAL |
| Booking creation (patient → doctor) | CRITICAL |
| Doctor accept/reject workflow | CRITICAL |
| Appointment status lifecycle (pending → confirmed → completed/cancelled) | CRITICAL |
| Appointment type (online / clinic) | CRITICAL |
| Branch-based appointments | HIGH |
| Recurring appointments | LOW |
| Appointment reminders (push + email) | HIGH |
| Cancellation policy & grace period | MEDIUM |
| Booking conflict detection | CRITICAL |
| Waiting list | LOW |

## 2.4 Payment & Billing

| Requirement | Priority |
|-------------|----------|
| Payment gateway integration (Fawry, Paymob, or Stripe Egypt) | CRITICAL |
| Consultation fee per doctor/branch | CRITICAL |
| Promo code system (percentage/fixed discounts) | HIGH |
| Payment receipt generation | HIGH |
| Refund management | HIGH |
| Doctor earnings tracking | HIGH |
| Platform commission calculation | MEDIUM |
| Payout to doctors | HIGH |
| Invoice generation | MEDIUM |
| Wallet/credit system | LOW |

## 2.5 Chat & Messaging

| Requirement | Priority |
|-------------|----------|
| Real-time text messaging (WebSocket) | CRITICAL |
| Message persistence | CRITICAL |
| File/image sharing in chat | HIGH |
| Typing indicators | MEDIUM |
| Read receipts | MEDIUM |
| Chat session lifecycle (tied to appointment) | HIGH |
| Chat history retrieval | HIGH |
| Message encryption (end-to-end) | MEDIUM |
| Video call integration | LOW (v2) |

## 2.6 Community

| Requirement | Priority |
|-------------|----------|
| Post CRUD (create, read, delete) | HIGH |
| Anonymous posting support | HIGH |
| Like/unlike posts | HIGH |
| Comment on posts | HIGH |
| Anonymous comments | HIGH |
| Post reporting/moderation | HIGH |
| Content filtering (profanity/spam) | MEDIUM |
| Post feed pagination | HIGH |

## 2.7 Notifications

| Requirement | Priority |
|-------------|----------|
| Push notifications (FCM + APNs) | CRITICAL |
| Notification persistence & history | HIGH |
| Notification types: appointment, message, promotion, system | HIGH |
| Read/unread tracking | HIGH |
| Notification preferences per user | MEDIUM |
| Email notifications (appointment confirmation, reminders) | HIGH |
| SMS notifications (OTP, appointment reminders) | MEDIUM |

## 2.8 Branch Management (Doctor-specific)

| Requirement | Priority |
|-------------|----------|
| Branch CRUD (name, governorate, area, address, phone) | HIGH |
| Working days & hours per branch | HIGH |
| Consultation fee per branch | HIGH |
| Active/inactive toggle | HIGH |
| Branch-specific appointment capacity | MEDIUM |

## 2.9 Reviews & Ratings

| Requirement | Priority |
|-------------|----------|
| Patient reviews on doctors (after completed appointment) | HIGH |
| Star rating (1-5) | HIGH |
| Review text | HIGH |
| Doctor average rating calculation | HIGH |
| Review moderation | MEDIUM |

## 2.10 Search & Discovery

| Requirement | Priority |
|-------------|----------|
| Doctor search by name | HIGH |
| Filter by specialty | HIGH |
| Filter by rating | HIGH |
| Sort by fee/experience/rating | HIGH |
| Filter by availability (online now) | MEDIUM |
| Filter by governorate/area | MEDIUM |
| Full-text search | MEDIUM |

## 2.11 Reports & Analytics

| Requirement | Priority |
|-------------|----------|
| Doctor earnings report (daily/weekly/monthly) | HIGH |
| Appointment statistics | HIGH |
| Patient visit history | HIGH |
| Platform admin dashboard | MEDIUM |
| Revenue reports | MEDIUM |
| User growth metrics | LOW |

## 2.12 Settings & Configuration

| Requirement | Priority |
|-------------|----------|
| User notification preferences | MEDIUM |
| Language preference persistence | MEDIUM |
| Theme preference persistence | LOW |
| App version management | MEDIUM |
| Force update mechanism | MEDIUM |
| Terms & privacy policy content | HIGH |

---

# Phase 3 — Database Design

## 3.1 Entity Relationship Overview

### Core Entities
1. **users** — Base table for all user types
2. **patients** — Patient-specific fields (extends users)
3. **doctors** — Doctor-specific fields (extends users)
4. **admins** — Admin-specific fields (extends users)
5. **specialties** — Medical specialties catalog
6. **branches** — Doctor clinic branches
7. **branch_schedules** — Working hours per branch per day
8. **appointments** — Booking records
9. **time_slots** — Available time slots per doctor per branch per day
10. **payments** — Payment transactions
11. **promo_codes** — Discount codes
12. **chat_rooms** — Chat sessions (tied to appointments)
13. **messages** — Individual chat messages
14. **posts** — Community posts
15. **comments** — Post comments
16. **reviews** — Doctor reviews from patients
17. **notifications** — User notifications
18. **favorites** — Patient favorite doctors
19. **devices** — FCM/APNs token storage
20. **audit_logs** — System audit trail

## 3.2 Table Definitions

### users
```
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
email           VARCHAR(255) UNIQUE NOT NULL
phone           VARCHAR(20) UNIQUE NOT NULL
password_hash   VARCHAR(255) NOT NULL
role            ENUM('patient', 'doctor', 'admin') NOT NULL
name            VARCHAR(255) NOT NULL
avatar_url      VARCHAR(500)
is_active       BOOLEAN DEFAULT true
is_verified     BOOLEAN DEFAULT false
language        VARCHAR(5) DEFAULT 'ar'
last_login_at   TIMESTAMP
created_at      TIMESTAMP DEFAULT NOW()
updated_at      TIMESTAMP DEFAULT NOW()
deleted_at      TIMESTAMP NULL  -- soft delete
```

### patients
```
id              UUID PRIMARY KEY REFERENCES users(id)
governorate     VARCHAR(100) NOT NULL
blood_type      VARCHAR(5)
date_of_birth   DATE
medical_notes   TEXT
```

### doctors
```
id                  UUID PRIMARY KEY REFERENCES users(id)
specialty_id        UUID REFERENCES specialties(id)
license_number      VARCHAR(50) UNIQUE NOT NULL
experience_years    INTEGER NOT NULL
bio                 TEXT
consultation_fee    DECIMAL(10,2) DEFAULT 200.00
rating              DECIMAL(3,2) DEFAULT 0.00
reviews_count       INTEGER DEFAULT 0
patients_count      INTEGER DEFAULT 0
is_online           BOOLEAN DEFAULT false
verification_status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending'
verified_at         TIMESTAMP
verified_by         UUID REFERENCES users(id)
```

### specialties
```
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
name_ar     VARCHAR(100) NOT NULL
name_en     VARCHAR(100) NOT NULL
icon        VARCHAR(10)       -- emoji
color       INTEGER           -- hex color code
is_active   BOOLEAN DEFAULT true
sort_order  INTEGER DEFAULT 0
```

### branches
```
id                UUID PRIMARY KEY DEFAULT gen_random_uuid()
doctor_id         UUID NOT NULL REFERENCES doctors(id)
name              VARCHAR(255) NOT NULL
governorate       VARCHAR(100) NOT NULL
area              VARCHAR(100) NOT NULL
address           TEXT NOT NULL
phone             VARCHAR(20) NOT NULL
consultation_fee  DECIMAL(10,2) NOT NULL
is_active         BOOLEAN DEFAULT true
created_at        TIMESTAMP DEFAULT NOW()
updated_at        TIMESTAMP DEFAULT NOW()
deleted_at        TIMESTAMP NULL
```

### branch_schedules
```
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
branch_id   UUID NOT NULL REFERENCES branches(id)
day_of_week INTEGER NOT NULL  -- 0=Saturday, 6=Friday
start_time  TIME NOT NULL
end_time    TIME NOT NULL
slot_duration_minutes INTEGER DEFAULT 30
is_active   BOOLEAN DEFAULT true
UNIQUE(branch_id, day_of_week)
```

### appointments
```
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
patient_id      UUID NOT NULL REFERENCES patients(id)
doctor_id       UUID NOT NULL REFERENCES doctors(id)
branch_id       UUID REFERENCES branches(id)  -- NULL for online
date            DATE NOT NULL
time            TIME NOT NULL
type            ENUM('online', 'clinic') NOT NULL
status          ENUM('pending', 'confirmed', 'completed', 'cancelled') DEFAULT 'pending'
amount          DECIMAL(10,2) NOT NULL
discount_amount DECIMAL(10,2) DEFAULT 0
promo_code_id   UUID REFERENCES promo_codes(id)
notes           TEXT
cancelled_by    ENUM('patient', 'doctor', 'system')
cancel_reason   TEXT
created_at      TIMESTAMP DEFAULT NOW()
updated_at      TIMESTAMP DEFAULT NOW()
INDEX idx_appointments_patient (patient_id, status)
INDEX idx_appointments_doctor (doctor_id, date, status)
INDEX idx_appointments_date (date, status)
```

### payments
```
id                  UUID PRIMARY KEY DEFAULT gen_random_uuid()
appointment_id      UUID NOT NULL REFERENCES appointments(id)
patient_id          UUID NOT NULL REFERENCES patients(id)
amount              DECIMAL(10,2) NOT NULL
currency            VARCHAR(3) DEFAULT 'EGP'
payment_method      VARCHAR(50) NOT NULL
payment_gateway     VARCHAR(50) NOT NULL  -- fawry, paymob, etc.
gateway_transaction_id VARCHAR(255)
status              ENUM('pending', 'completed', 'failed', 'refunded') DEFAULT 'pending'
paid_at             TIMESTAMP
refunded_at         TIMESTAMP
refund_amount       DECIMAL(10,2)
created_at          TIMESTAMP DEFAULT NOW()
INDEX idx_payments_appointment (appointment_id)
INDEX idx_payments_status (status)
```

### promo_codes
```
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
code            VARCHAR(50) UNIQUE NOT NULL
type            ENUM('percentage', 'fixed') NOT NULL
value           DECIMAL(10,2) NOT NULL  -- percentage (0.20) or fixed amount
max_uses        INTEGER
current_uses    INTEGER DEFAULT 0
min_amount      DECIMAL(10,2) DEFAULT 0
max_discount    DECIMAL(10,2)   -- cap for percentage discounts
valid_from      TIMESTAMP NOT NULL
valid_until     TIMESTAMP NOT NULL
is_active       BOOLEAN DEFAULT true
created_at      TIMESTAMP DEFAULT NOW()
```

### chat_rooms
```
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
appointment_id  UUID UNIQUE REFERENCES appointments(id)
patient_id      UUID NOT NULL REFERENCES patients(id)
doctor_id       UUID NOT NULL REFERENCES doctors(id)
status          ENUM('active', 'closed') DEFAULT 'active'
created_at      TIMESTAMP DEFAULT NOW()
closed_at       TIMESTAMP
INDEX idx_chatrooms_participants (patient_id, doctor_id)
```

### messages
```
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
chat_room_id    UUID NOT NULL REFERENCES chat_rooms(id)
sender_id       UUID NOT NULL REFERENCES users(id)
content         TEXT NOT NULL
type            ENUM('text', 'image', 'file') DEFAULT 'text'
media_url       VARCHAR(500)
is_read         BOOLEAN DEFAULT false
created_at      TIMESTAMP DEFAULT NOW()
INDEX idx_messages_chatroom (chat_room_id, created_at)
```

### posts
```
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id         UUID NOT NULL REFERENCES users(id)
content         TEXT NOT NULL
is_anonymous    BOOLEAN DEFAULT false
likes_count     INTEGER DEFAULT 0
comments_count  INTEGER DEFAULT 0
is_reported     BOOLEAN DEFAULT false
is_hidden       BOOLEAN DEFAULT false
created_at      TIMESTAMP DEFAULT NOW()
updated_at      TIMESTAMP DEFAULT NOW()
deleted_at      TIMESTAMP NULL
INDEX idx_posts_created (created_at DESC)
INDEX idx_posts_user (user_id)
```

### comments
```
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
post_id         UUID NOT NULL REFERENCES posts(id) ON DELETE CASCADE
user_id         UUID NOT NULL REFERENCES users(id)
content         TEXT NOT NULL
is_anonymous    BOOLEAN DEFAULT false
created_at      TIMESTAMP DEFAULT NOW()
deleted_at      TIMESTAMP NULL
INDEX idx_comments_post (post_id, created_at)
```

### post_likes
```
post_id     UUID NOT NULL REFERENCES posts(id) ON DELETE CASCADE
user_id     UUID NOT NULL REFERENCES users(id)
created_at  TIMESTAMP DEFAULT NOW()
PRIMARY KEY (post_id, user_id)
```

### reviews
```
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
doctor_id   UUID NOT NULL REFERENCES doctors(id)
patient_id  UUID NOT NULL REFERENCES patients(id)
appointment_id UUID REFERENCES appointments(id)
rating      DECIMAL(2,1) NOT NULL CHECK (rating >= 1 AND rating <= 5)
comment     TEXT
created_at  TIMESTAMP DEFAULT NOW()
UNIQUE(appointment_id)  -- one review per appointment
INDEX idx_reviews_doctor (doctor_id, created_at DESC)
```

### notifications
```
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id     UUID NOT NULL REFERENCES users(id)
title       VARCHAR(255) NOT NULL
body        TEXT NOT NULL
type        ENUM('appointment', 'message', 'promotion', 'system') NOT NULL
data        JSONB  -- additional payload (appointment_id, etc.)
is_read     BOOLEAN DEFAULT false
created_at  TIMESTAMP DEFAULT NOW()
INDEX idx_notifications_user (user_id, is_read, created_at DESC)
```

### favorites
```
patient_id  UUID NOT NULL REFERENCES patients(id)
doctor_id   UUID NOT NULL REFERENCES doctors(id)
created_at  TIMESTAMP DEFAULT NOW()
PRIMARY KEY (patient_id, doctor_id)
```

### devices
```
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id     UUID NOT NULL REFERENCES users(id)
platform    ENUM('ios', 'android') NOT NULL
fcm_token   VARCHAR(500) NOT NULL
device_name VARCHAR(255)
is_active   BOOLEAN DEFAULT true
created_at  TIMESTAMP DEFAULT NOW()
updated_at  TIMESTAMP DEFAULT NOW()
INDEX idx_devices_user (user_id, is_active)
```

### audit_logs
```
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id     UUID REFERENCES users(id)
action      VARCHAR(100) NOT NULL
entity_type VARCHAR(100) NOT NULL
entity_id   UUID
old_data    JSONB
new_data    JSONB
ip_address  INET
user_agent  TEXT
created_at  TIMESTAMP DEFAULT NOW()
INDEX idx_audit_user (user_id, created_at DESC)
INDEX idx_audit_entity (entity_type, entity_id)
```

## 3.3 Key Relationships

- users 1→1 patients (patient role)
- users 1→1 doctors (doctor role)
- doctors N→1 specialties
- doctors 1→N branches
- branches 1→N branch_schedules
- patients N→N doctors (through appointments)
- appointments N→1 patients, N→1 doctors, N→1 branches
- appointments 1→1 payments
- appointments 1→1 chat_rooms
- chat_rooms 1→N messages
- posts N→1 users, 1→N comments, N→N users (through post_likes)
- reviews N→1 doctors, N→1 patients
- notifications N→1 users
- favorites N→N (patients ↔ doctors)

## 3.4 Scalability Considerations

- UUID primary keys for distributed-friendly IDs
- Soft delete (`deleted_at`) on users, branches, posts, comments
- JSONB for flexible notification payloads and audit data
- Composite indexes on frequently queried patterns
- Partition appointments table by date (monthly) when data grows
- Read replicas for search/listing queries

---

# Phase 4 — API Contract Design

## 4.1 Base Configuration

```
Base URL:     https://api.henlehen.com/v1
Content-Type: application/json
Auth Header:  Authorization: Bearer <jwt_token>
Language:     Accept-Language: ar | en
Pagination:   ?page=1&limit=20
Sorting:      ?sort=rating&order=desc
```

## 4.2 Authentication APIs

### POST /auth/register/patient
```json
Request: { "name": "string", "email": "string", "phone": "string", "password": "string", "governorate": "string" }
Response 201: { "user": {...}, "tokens": { "access": "jwt", "refresh": "jwt" } }
Errors: 400 (validation), 409 (email/phone exists)
```

### POST /auth/register/doctor
```json
Request: { "name": "string", "email": "string", "phone": "string", "password": "string", "specialty_id": "uuid", "license_number": "string", "experience_years": int, "bio": "string" }
Response 201: { "doctor": {...}, "status": "pending_approval" }
Errors: 400 (validation), 409 (email/phone/license exists)
```

### POST /auth/login
```json
Request: { "email": "string", "password": "string" }
Response 200: { "user": {...}, "tokens": { "access": "jwt", "refresh": "jwt" } }
Errors: 401 (invalid credentials), 403 (account not verified / doctor pending)
```

### POST /auth/refresh
```json
Request: { "refresh_token": "string" }
Response 200: { "tokens": { "access": "jwt", "refresh": "jwt" } }
```

### POST /auth/forgot-password
```json
Request: { "email": "string" }
Response 200: { "message": "OTP sent" }
```

### POST /auth/reset-password
```json
Request: { "email": "string", "otp": "string", "new_password": "string" }
Response 200: { "message": "Password updated" }
```

### POST /auth/verify-email
```json
Request: { "email": "string", "otp": "string" }
Response 200: { "message": "Email verified" }
```

### POST /auth/logout
```json
Request: { "refresh_token": "string" }
Response 204
```

## 4.3 Patient APIs

### GET /patients/profile
```json
Response 200: { "id", "name", "email", "phone", "governorate", "avatar_url", "blood_type" }
```

### PUT /patients/profile
```json
Request: { "name?", "phone?", "governorate?", "blood_type?" }
Response 200: { updated patient object }
```

### POST /patients/profile/avatar
```json
Request: multipart/form-data { avatar: file }
Response 200: { "avatar_url": "string" }
```

## 4.4 Doctor APIs

### GET /doctors
```json
Query: ?specialty=gynecology&search=منة&sort=rating&order=desc&page=1&limit=20&online=true&governorate=القاهرة
Response 200: { "data": [...], "meta": { "total", "page", "limit", "pages" } }
```

### GET /doctors/:id
```json
Response 200: { doctor object with branches, reviews summary }
```

### GET /doctors/:id/reviews
```json
Query: ?page=1&limit=10
Response 200: { "data": [...], "meta": {...} }
```

### GET /doctors/:id/availability
```json
Query: ?date=2026-07-01&branch_id=uuid
Response 200: { "slots": [{ "time": "10:00", "is_available": true }, ...] }
```

### PUT /doctors/profile (doctor role)
```json
Request: { "name?", "phone?", "bio?", "consultation_fee?" }
Response 200: { updated doctor object }
```

### PUT /doctors/online-status (doctor role)
```json
Request: { "is_online": boolean }
Response 200: { "is_online": true }
```

## 4.5 Appointment APIs

### POST /appointments
```json
Request: { "doctor_id": "uuid", "branch_id?": "uuid", "date": "2026-07-01", "time": "10:00", "type": "online|clinic", "promo_code?": "FIRST20" }
Response 201: { appointment object }
Errors: 400 (validation), 409 (slot unavailable)
```

### GET /appointments (patient or doctor)
```json
Query: ?status=pending,confirmed&page=1&limit=20
Response 200: { "data": [...], "meta": {...} }
```

### GET /appointments/:id
```json
Response 200: { appointment with patient/doctor details }
```

### PATCH /appointments/:id/status (doctor role)
```json
Request: { "status": "confirmed|cancelled|completed", "reason?": "string" }
Response 200: { updated appointment }
Triggers: push notification to patient
```

### PATCH /appointments/:id/cancel (patient role)
```json
Request: { "reason?": "string" }
Response 200: { updated appointment }
Triggers: push notification to doctor, refund check
```

## 4.6 Payment APIs

### POST /payments/initiate
```json
Request: { "appointment_id": "uuid", "payment_method": "card|fawry|wallet" }
Response 200: { "payment_url": "string", "transaction_id": "string" }
```

### POST /payments/webhook (payment gateway callback)
```json
Request: { gateway-specific payload }
Response 200
Triggers: update payment status, send confirmation notification
```

### GET /payments/history
```json
Query: ?page=1&limit=20
Response 200: { "data": [...], "meta": {...} }
```

## 4.7 Chat APIs

### GET /chat/rooms
```json
Response 200: { "data": [{ "id", "appointment_id", "other_user", "last_message", "unread_count" }] }
```

### GET /chat/rooms/:id/messages
```json
Query: ?before=timestamp&limit=50
Response 200: { "data": [...], "has_more": boolean }
```

### POST /chat/rooms/:id/messages
```json
Request: { "content": "string", "type": "text|image|file", "media?": file }
Response 201: { message object }
Broadcasts: via WebSocket to other participant
```

### WebSocket: wss://api.henlehen.com/ws
```json
Events: message.new, message.read, user.typing, chat.closed
Auth: token query param
```

## 4.8 Community APIs

### GET /posts
```json
Query: ?page=1&limit=20
Response 200: { "data": [...], "meta": {...} }
```

### POST /posts
```json
Request: { "content": "string", "is_anonymous": boolean }
Response 201: { post object }
```

### DELETE /posts/:id (owner only)
```json
Response 204
```

### POST /posts/:id/like
```json
Response 200: { "likes_count": int, "is_liked": true }
```

### DELETE /posts/:id/like
```json
Response 200: { "likes_count": int, "is_liked": false }
```

### GET /posts/:id/comments
```json
Response 200: { "data": [...] }
```

### POST /posts/:id/comments
```json
Request: { "content": "string", "is_anonymous": boolean }
Response 201: { comment object }
```

### POST /posts/:id/report
```json
Request: { "reason": "string" }
Response 200
```

## 4.9 Branch APIs (doctor role)

### GET /branches
```json
Response 200: { "data": [branch objects with schedules] }
```

### POST /branches
```json
Request: { "name", "governorate", "area", "address", "phone", "consultation_fee", "working_days": [{ "day": 0, "start": "10:00", "end": "18:00" }] }
Response 201: { branch object }
```

### PUT /branches/:id
```json
Request: { fields to update }
Response 200: { updated branch }
```

### PATCH /branches/:id/toggle-active
```json
Response 200: { "is_active": boolean }
```

### DELETE /branches/:id
```json
Response 204 (soft delete)
```

## 4.10 Notification APIs

### GET /notifications
```json
Query: ?page=1&limit=20&unread_only=true
Response 200: { "data": [...], "meta": {...}, "unread_count": int }
```

### PATCH /notifications/:id/read
```json
Response 200
```

### PATCH /notifications/read-all
```json
Response 200
```

### DELETE /notifications/:id
```json
Response 204
```

## 4.11 Favorites APIs (patient role)

### GET /favorites
```json
Response 200: { "data": [doctor objects] }
```

### POST /favorites/:doctor_id
```json
Response 201
```

### DELETE /favorites/:doctor_id
```json
Response 204
```

## 4.12 Admin APIs

### GET /admin/doctors/pending
```json
Response 200: { "data": [doctors awaiting verification] }
```

### PATCH /admin/doctors/:id/verify
```json
Request: { "status": "approved|rejected", "reason?": "string" }
Response 200
Triggers: notification to doctor
```

### GET /admin/reports/revenue
```json
Query: ?from=2026-01-01&to=2026-06-30
Response 200: { "total_revenue", "total_appointments", "monthly_breakdown": [...] }
```

### GET /admin/reports/users
```json
Response 200: { "total_patients", "total_doctors", "new_this_month", ... }
```

## 4.13 Error Handling

```json
Standard Error Response:
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable message",
    "message_ar": "رسالة بالعربية",
    "details": [{ "field": "email", "message": "Invalid email format" }]
  }
}

Status Codes:
200 — Success
201 — Created
204 — No Content (delete)
400 — Bad Request / Validation Error
401 — Unauthorized (no/invalid token)
403 — Forbidden (insufficient role)
404 — Not Found
409 — Conflict (duplicate)
422 — Unprocessable Entity
429 — Rate Limited
500 — Internal Server Error
```

---

# Phase 5 — Infrastructure Requirements

## 5.1 Recommended Architecture

```
Client Apps (Flutter)
      ↓ HTTPS
API Gateway (Nginx / AWS ALB)
      ↓
Backend Service (Node.js/NestJS or Python/FastAPI or Go)
      ↓
┌──────────┬──────────┬──────────┬──────────┐
│ PostgreSQL│  Redis   │    S3    │ Firebase │
│ (Primary │ (Cache + │ (Media   │ (FCM for │
│  Database)│  Sessions│  Storage)│  Push)   │
│          │  + Queue)│          │          │
└──────────┴──────────┴──────────┴──────────┘
```

## 5.2 Server Requirements

| Component | Minimum (Launch) | Recommended (Growth) |
|-----------|-----------------|---------------------|
| API Server | 2 vCPU, 4GB RAM | 4 vCPU, 8GB RAM × 2 (HA) |
| Database | 2 vCPU, 4GB RAM, 50GB SSD | 4 vCPU, 8GB RAM, 100GB SSD |
| Redis | 1 vCPU, 1GB RAM | 2 vCPU, 2GB RAM |
| WebSocket Server | 1 vCPU, 2GB RAM | 2 vCPU, 4GB RAM |

## 5.3 Storage Requirements

| Type | Service | Estimated Size |
|------|---------|---------------|
| Database | PostgreSQL 15+ | 10-50 GB first year |
| Media (avatars, chat images) | S3/Cloudflare R2 | 50-200 GB first year |
| Backups | S3 Glacier | 3× database size |
| Logs | ELK/CloudWatch | 20 GB/month |

## 5.4 CDN Requirements

- CloudFront or Cloudflare for static media delivery
- Image resizing service (Sharp/Imgproxy) for avatar thumbnails
- Cache headers: avatars 30d, chat media 7d

## 5.5 Caching Strategy

| Data | Cache | TTL |
|------|-------|-----|
| Doctor profiles | Redis | 5 min |
| Specialty list | Redis | 24 hr |
| Doctor search results | Redis | 2 min |
| User sessions | Redis | 7 days |
| Rate limit counters | Redis | 1 min window |
| Time slot availability | Redis | 30 sec |

## 5.6 Queue System

Redis-based queue (BullMQ or similar) for:
- Email sending (registration, appointment confirmation, reminders)
- Push notification dispatch
- SMS sending (OTP)
- Payment webhook processing
- Report generation
- Image processing (resize/compress uploaded photos)

## 5.7 Real-Time Services

- WebSocket server (Socket.IO or native WS) for chat
- Redis Pub/Sub for multi-instance message routing
- Presence system for doctor online/offline status

## 5.8 Monitoring & Logging

| Tool | Purpose |
|------|---------|
| Sentry / Bugsnag | Error tracking |
| Prometheus + Grafana | Metrics & dashboards |
| ELK Stack / CloudWatch | Centralized logging |
| UptimeRobot | Uptime monitoring |
| PGHero | Database performance |

## 5.9 Backup Strategy

- Database: Automated daily snapshots, point-in-time recovery (30 days)
- Media: Cross-region S3 replication
- Configuration: Version-controlled (Git)
- Test restore procedure monthly

## 5.10 Disaster Recovery

- RTO (Recovery Time Objective): 1 hour
- RPO (Recovery Point Objective): 15 minutes
- Multi-AZ database deployment
- Automated failover for primary database
- Runbook for manual recovery procedures

---

# Phase 6 — Security Review

## 6.1 Authentication Security

| Requirement | Implementation |
|-------------|---------------|
| Password hashing | bcrypt with cost factor 12 |
| JWT access token | 15-minute expiry, RS256 signing |
| JWT refresh token | 7-day expiry, stored in DB, single-use |
| Login brute force protection | 5 attempts per 15 min, then lock 30 min |
| OTP for email verification | 6-digit, 10-minute expiry, max 3 attempts |
| Phone OTP | 6-digit via SMS gateway, 5-minute expiry |

## 6.2 API Security

| Layer | Measure |
|-------|---------|
| Transport | TLS 1.3 only, HSTS headers |
| Rate limiting | 100 req/min per user, 20 req/min for auth endpoints |
| Input validation | Server-side validation on ALL inputs (Joi/Zod/Pydantic) |
| SQL injection | Parameterized queries / ORM (never raw string interpolation) |
| XSS | Sanitize all user content before storage |
| CORS | Whitelist mobile app origins only |
| Request size | 10MB max (for file uploads) |
| Helmet headers | X-Content-Type-Options, X-Frame-Options, CSP |

## 6.3 Role-Based Access Control

```
Patient:
  ✅ View/search doctors
  ✅ Book appointments, manage own appointments
  ✅ Chat (own rooms only)
  ✅ Community (post, comment, like)
  ✅ Manage own profile, favorites
  ❌ Access other patients' data
  ❌ Doctor admin features

Doctor:
  ✅ Manage own profile, branches
  ✅ Accept/reject/complete own appointments
  ✅ Chat with own patients
  ✅ View own earnings
  ❌ Access other doctors' data
  ❌ View patient medical records beyond own consultations

Admin:
  ✅ Verify/reject doctor registrations
  ✅ Moderate community posts
  ✅ View platform analytics
  ✅ Manage promo codes
  ✅ Handle refunds
  ❌ Read private chat messages
```

## 6.4 Data Protection

| Category | Measure |
|----------|---------|
| PII at rest | AES-256 encryption for sensitive fields (license numbers, phone in DB) |
| PII in transit | TLS 1.3 |
| Chat messages | Encrypted at rest, access-controlled by chat room membership |
| Medical data | Separate encrypted column store for patient medical notes |
| Payment data | Never stored — handled entirely by payment gateway (PCI DSS compliance) |
| Passwords | bcrypt hashed, never logged, never returned in API |
| Tokens | JWT in memory only (mobile), refresh token in secure storage |
| File uploads | Virus scan, file type validation, size limits, randomized filenames |

## 6.5 Audit Logging

Track these events:
- Login/logout (success and failure)
- Password changes
- Profile updates
- Appointment status changes
- Payment transactions
- Doctor verification actions
- Admin moderation actions
- Data access patterns (for compliance)

---

# Phase 7 — Backend Gap Analysis

## 7.1 Gap Summary

| Category | Exists | Missing | Gap % |
|----------|--------|---------|-------|
| Backend Server | ❌ | Complete server | 100% |
| Database | ❌ | Full schema + migrations | 100% |
| Authentication | ❌ | JWT, OAuth, OTP | 100% |
| Authorization | ❌ | RBAC, middleware | 100% |
| API Layer | ❌ | ~60 endpoints | 100% |
| Payment Integration | ❌ | Payment gateway | 100% |
| Real-time Chat | ❌ | WebSocket server | 100% |
| Push Notifications | ❌ | FCM integration | 100% |
| File Storage | ❌ | S3 + CDN | 100% |
| Email Service | ❌ | SMTP/SES | 100% |
| SMS Service | ❌ | SMS gateway | 100% |
| Admin Panel | ❌ | Web dashboard | 100% |
| Monitoring | ❌ | Logging, metrics | 100% |
| CI/CD | ❌ | Deployment pipeline | 100% |
| Flutter API Integration | ❌ | Replace all mock data | 100% |

## 7.2 Prioritized Feature List

### CRITICAL — Must Have for Launch
1. **User authentication** (register, login, JWT, refresh)
2. **Doctor registration with approval workflow**
3. **Doctor listing & search API**
4. **Appointment booking & management**
5. **Payment integration** (at least one gateway)
6. **Real-time chat** (WebSocket)
7. **Push notifications** (FCM)
8. **Database schema & migrations**
9. **API server deployment**
10. **Flutter apps: replace all mock data with API calls**

### HIGH — Needed Before Public Launch
11. Email verification
12. Password reset
13. Profile photo upload
14. Branch management API
15. Doctor availability/time slots
16. Community posts API
17. Favorites API
18. Notification history API
19. Doctor earnings API
20. Rate limiting & security headers

### MEDIUM — Enhances Experience
21. Review & rating system
22. Admin web panel
23. Promo code management
24. SMS OTP verification
25. Search optimization (Elasticsearch)
26. Email notifications (appointment reminders)
27. Audit logging
28. Analytics dashboard

### LOW — Can Wait for v2
29. Video call integration
30. Social login (Google/Apple)
31. Wallet/credit system
32. Recurring appointments
33. Waiting list
34. Advanced reporting
35. Multi-language push notifications

## 7.3 Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| No backend exists at all | CRITICAL | Start immediately with core auth + booking |
| Chat requires real-time infrastructure | HIGH | Use managed service (Firebase/Ably) initially |
| Payment compliance (PCI DSS) | HIGH | Use hosted payment page, never handle card data |
| Medical data privacy regulations | HIGH | Encrypt PII, implement access controls early |
| Scale concerns if user growth is rapid | MEDIUM | Design stateless API, use caching from day 1 |
| Doctor verification bottleneck | MEDIUM | Build admin panel early, define SLA |
| App store rejection (no real functionality) | HIGH | Backend must exist before app submission |

---

# Phase 8 — Production Readiness Report

## 8.1 Current Readiness Score: 15/100

| Area | Score | Notes |
|------|-------|-------|
| Frontend (Flutter) | 85% | UI complete, state management migrated to GetX |
| Backend Server | 0% | Does not exist |
| Database | 0% | Does not exist |
| API Integration | 0% | All mock data |
| Authentication | 0% | Hardcoded credentials |
| Payment | 0% | UI only, no gateway |
| Chat | 0% | Simulated |
| Notifications | 0% | Mock data |
| Security | 0% | No measures |
| DevOps/CI/CD | 0% | No pipeline |
| Monitoring | 0% | No monitoring |
| Testing | 0% | No tests |

## 8.2 Pre-Launch Requirements

### Sprint 1 (Weeks 1-2): Foundation
- Set up backend project (NestJS/FastAPI recommended)
- Design and create database schema (PostgreSQL)
- Implement user authentication (register, login, JWT)
- Deploy to staging environment
- Set up CI/CD pipeline

### Sprint 2 (Weeks 3-4): Core Features
- Doctor registration + admin approval API
- Doctor listing, search, and profile APIs
- Appointment booking API with conflict detection
- Time slot management API
- Flutter: integrate auth APIs (replace mock)

### Sprint 3 (Weeks 5-6): Transactions
- Payment gateway integration (Paymob recommended for Egypt)
- Appointment lifecycle management
- Push notification service (FCM)
- Flutter: integrate booking + payment

### Sprint 4 (Weeks 7-8): Communication
- WebSocket chat server
- Message persistence
- File upload service (S3)
- Flutter: integrate chat + notifications

### Sprint 5 (Weeks 9-10): Social & Polish
- Community posts/comments API
- Favorites API
- Review/rating API
- Branch management API
- Admin web panel (basic)

### Sprint 6 (Weeks 11-12): Hardening
- Security audit & penetration testing
- Load testing
- Error handling refinement
- Monitoring & alerting setup
- Production deployment
- App store preparation

## 8.3 Estimated Timeline

| Milestone | Duration | Cumulative |
|-----------|----------|------------|
| Backend foundation + auth | 2 weeks | Week 2 |
| Core booking flow | 2 weeks | Week 4 |
| Payment + notifications | 2 weeks | Week 6 |
| Chat + file uploads | 2 weeks | Week 8 |
| Community + admin + polish | 2 weeks | Week 10 |
| Security + testing + deployment | 2 weeks | Week 12 |
| **Total estimated: 12 weeks (3 months)** | | |

This assumes 1-2 backend developers working full-time.

## 8.4 Recommended Tech Stack

| Layer | Recommendation | Reason |
|-------|---------------|--------|
| Backend Framework | NestJS (TypeScript) or FastAPI (Python) | Type safety, strong ecosystem, good for medical apps |
| Database | PostgreSQL 16 | Robust, JSONB support, excellent for structured + semi-structured data |
| Cache | Redis 7 | Sessions, caching, queues, pub/sub |
| File Storage | AWS S3 or Cloudflare R2 | Cost-effective media storage |
| CDN | CloudFront or Cloudflare | Global edge delivery |
| Push Notifications | Firebase Cloud Messaging | Free, reliable, cross-platform |
| Email | AWS SES or SendGrid | Transactional emails |
| SMS | Vodafone Egypt API or Twilio | OTP delivery |
| Payment | Paymob | Egyptian market leader, supports Fawry/cards |
| Hosting | AWS (Cairo region) or DigitalOcean | Low latency for Egyptian users |
| WebSocket | Socket.IO on NestJS or native WS | Real-time chat |
| Monitoring | Sentry + Prometheus + Grafana | Error tracking + metrics |

## 8.5 Final Recommendation

The Flutter frontend is well-built with clean architecture after the GetX migration. The **critical blocker** is the complete absence of any backend infrastructure. Every feature currently runs on hardcoded mock data. The recommended approach is to start with authentication and the booking flow (the core value proposition), then layer on chat, payments, and community features in subsequent sprints. A 12-week timeline with 1-2 dedicated backend developers is realistic for an MVP launch.

---

*Report generated from full codebase analysis of hen_lhen monorepo — patient_app (23 screens, 7 controllers) + doctor_app (12 screens, 5 controllers) + 3 shared packages.*
