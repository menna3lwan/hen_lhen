# Phase 1 — Project Analysis Report
## هُنَّ لَهُنَّ (Hen Lehen) — Current Architecture Analysis

---

## 1. Project Overview

A medical consultation platform for women, consisting of two Flutter apps under a Melos monorepo:

- **patient_app** — For patients to find doctors, book appointments, chat, and join a community
- **doctor_app** — For doctors to manage appointments, patients, branches, and earnings
- **packages/** — Shared code: `shared_ui`, `shared_models`, `shared_core`

## 2. Current Architecture

### 2.1 State Management: Provider (ChangeNotifier)

**Patient App Providers** (all in `config/providers.dart`):

| Provider | Purpose | Fields |
|---|---|---|
| `AuthProvider` | Login, register, user state | `_user`, `_isLoading`, `_isLoggedIn`, `_error` |
| `DoctorsProvider` | Doctor listing, search, filter, sort | `_doctors`, `_selectedSpecialty`, `_searchQuery`, `_sortBy` |
| `AppointmentsProvider` | CRUD appointments | `_appointments`, `_isLoading` |
| `FavoritesProvider` | Favorite doctors | `_favoriteIds` (Set) |
| `CommunityProvider` | Posts, likes, comments | `_posts`, `_isLoading` |
| `NotificationsProvider` | Notifications | `_notifications` |
| `BookingProvider` | Booking flow state | `_selectedDate`, `_selectedTime`, `_consultationType`, `_promoCode`, `_discount` |

**Doctor App Providers** (all in `config/providers.dart`):

| Provider | Purpose |
|---|---|
| `AuthProvider` | Doctor login, register, pending approval |
| `AppointmentsProvider` | Accept/reject/complete appointments |
| `PatientsProvider` | Patient listing + search |
| `BranchesProvider` | CRUD branches |
| `EarningsProvider` | Static earnings data |

**Additional Providers from shared_ui:**
- `ThemeProvider` (duplicated in doctor_app/theme.dart)

**Issues Found:**
- All providers are in a single monolithic file (`providers.dart`) in each app — ~870 lines in patient_app
- `LocaleProvider` is a separate ChangeNotifier but duplicated in both apps
- `ThemeProvider` is defined in `shared_ui` AND redefined in both apps' theme files
- No separation between business logic and UI state
- Providers create themselves with `ChangeNotifierProvider(create: (_) => ...)` — no DI

### 2.2 Navigation: GoRouter

**Patient App Routes** (`config/routes.dart`):
- 16 routes defined
- Router is rebuilt on every build (created inside `router(BuildContext context)`)
- Uses `Provider.of<AuthProvider>` for auth redirect — tightly coupled
- Mix of path params (`/doctor/:id`), query params (`?specialty=`), and `extra` for passing data

**Doctor App Routes** (`config/routes.dart`):
- 10 routes using `ShellRoute` for bottom nav
- Same pattern of creating router inside build method

**Issues:**
- Router recreation on every rebuild is wasteful
- Passing `extra` (untyped data) for navigation is fragile
- No named route constants shared between navigation calls

### 2.3 Dependency Injection: None

- No DI framework
- `AuthRepository` instantiates `ApiClient` inline: `ApiClient? apiClient ?? ApiClient()`
- Providers are created directly in `AppProviders.providers` list
- No ability to swap implementations for testing

### 2.4 API Layer

**ApiClient** (identical in both apps):
- Uses Dio with base URL `https://api.henlehen.com/v1`
- Has interceptor stubs (no actual auth token injection)
- 10-second timeouts

**AuthRepository** (in both apps):
- Mock implementations with `Future.delayed`
- Hardcoded test credentials (`test@test.com` / `doctor@hen.com`)
- TODO comments for real API integration

**Current State:** 100% mock data. No real API calls exist.

### 2.5 Models

**Patient App Models** (`models/models.dart`):
- `UserModel`, `DoctorModel`, `AppointmentModel`, `PostModel`, `CommentModel`, `NotificationModel`, `ReviewModel`, `TimeSlotModel`, `SpecialtyModel`
- `MockData` class with static data
- No JSON serialization (`fromJson`/`toJson`)
- No `Equatable` or `copyWith` on most models

**Doctor App Models** (`models/models.dart`):
- `DoctorModel` (different from patient's), `PatientModel`, `AppointmentModel` (different from patient's), `BranchModel`
- `MockData` class with static data
- Same issues: no serialization, different model definitions across apps

**Issues:**
- Duplicate model definitions between apps
- `shared_models` package exists but is EMPTY (just a Calculator stub)
- Models should be shared but aren't

### 2.6 Localization

- Custom `LocaleProvider` with inline Arabic/English maps
- Duplicated entirely between both apps (~200+ translation keys each)
- Not using Flutter's intl/arb system

### 2.7 Shared Packages

| Package | Contents | Status |
|---|---|---|
| `shared_core` | Empty (Calculator stub) | **Unused** |
| `shared_models` | Empty (Calculator stub) | **Unused** |
| `shared_ui` | `AppColors`, `ThemeProvider`, `AppTheme`, `AppButton`, `AppTextField`, `SnackbarUtil` | **Partially used** |

### 2.8 Features Inventory

**Patient App Features:**
1. Onboarding (3-page intro)
2. Auth (Login, Register with governorate selection)
3. Home (greeting, search, specialties grid, top doctors)
4. Doctor Search (filter by specialty, sort by rating/experience/fee)
5. Doctor Profile (stats, reviews, about, online status)
6. Booking Flow (consultation type → date → time → payment → success)
7. Payment (credit/wallet/cash, promo codes, price breakdown)
8. Appointments Management (upcoming/completed/cancelled tabs)
9. Appointment Details (status, doctor info, actions)
10. Chat (text messages, session info)
11. Community (posts, likes, comments, anonymous posting)
12. Favorites (add/remove doctors)
13. Notifications (list, mark read, dismiss)
14. Profile (edit, change photo, change password, medical history)
15. Settings (theme toggle, language toggle, notification prefs)

**Doctor App Features:**
1. Auth (Login, Register with license/specialty/bio)
2. Pending Approval Screen
3. Dashboard (stats: today's appointments, patients, rating, earnings)
4. Appointments Management (accept/reject/complete)
5. Patients List (search, visit history)
6. Chat (same as patient app)
7. Branches Management (add/edit/delete/toggle active)
8. Profile (edit doctor info)
9. Settings (theme, language, support links)

## 3. Code Quality Issues

1. **Monolithic providers.dart** — All business logic in one file per app
2. **ThemeProvider duplication** — Defined in 3 places
3. **LocaleProvider duplication** — Identical structure in both apps
4. **Empty shared packages** — shared_core and shared_models unused
5. **No model sharing** — DoctorModel, AppointmentModel defined differently in each app
6. **No JSON serialization** — Models can't parse API responses
7. **Hardcoded strings** — Some Arabic text directly in widgets (not using locale)
8. **`withOpacity()` usage** — Deprecated in Flutter 3.x, should use `Color.withValues()`
9. **No error boundaries** — API calls have no proper error handling
10. **`context.watch` mixed with `Provider.of`** — Inconsistent provider access patterns

## 4. Dependency Versions

| Package | Version | Notes |
|---|---|---|
| flutter | >=3.0.0 <4.0.0 | |
| provider | ^6.1.1 | **To be replaced by GetX** |
| go_router | ^13.0.0 | **To be replaced by GetX** |
| dio | ^5.9.2 | Keep |
| shared_preferences | ^2.2.2 | Keep |
| google_fonts | ^8.1.0 | Keep |
| flutter_rating_bar | ^4.0.1 | Keep |
| iconsax | ^0.0.8 | Keep (patient_app only) |
| cached_network_image | ^3.4.1 | Keep |

---

*Report generated: Phase 1 Complete*
