<div align="center">

# هُنَّ لَهُنَّ — Hen Lehen

**A Women-Only Healthcare Platform**

<p>
  <img src="https://img.shields.io/badge/Flutter-3.x-02569B?style=for-the-badge&logo=flutter&logoColor=white"/>
  <img src="https://img.shields.io/badge/Dart-3.x-0175C2?style=for-the-badge&logo=dart&logoColor=white"/>
  <img src="https://img.shields.io/badge/Platform-Android%20%7C%20iOS-lightgrey?style=for-the-badge"/>
</p>

<p>
  <img src="https://img.shields.io/badge/State%20Management-Provider-blueviolet?style=flat-square"/>
  <img src="https://img.shields.io/badge/Navigation-GoRouter-green?style=flat-square"/>
  <img src="https://img.shields.io/badge/Font-Cairo-orange?style=flat-square"/>
  <img src="https://img.shields.io/badge/i18n-Arabic%20%7C%20English-blue?style=flat-square"/>
</p>

</div>

---

## Table of Contents

- [Project Overview](#project-overview)
- [Repository Structure](#repository-structure)
- [Applications](#applications)
  - [Patient App](#patient-app)
  - [Doctor App](#doctor-app)
- [Architecture Overview](#architecture-overview)
- [Installation & Setup](#installation--setup)
- [Running the Applications](#running-the-applications)
- [Dependencies](#dependencies)
- [Development Guidelines](#development-guidelines)
- [Future Improvements](#future-improvements)

---

## Project Overview

**Hen Lehen (هُنَّ لَهُنَّ)** is a women-only telemedicine platform that connects female patients with female doctors across Egypt. The platform prioritises privacy, safety, and emotional comfort — providing a dedicated digital space where women can seek medical care with confidence.

The system consists of **two independent Flutter applications** that share the same domain:

| App | Audience | Purpose |
|-----|----------|---------|
| `patient_app` | Female patients | Browse doctors, book consultations, chat, community |
| `doctor_app` | Female doctors | Manage appointments, patients, clinic branches, earnings |

Both apps are bilingual (Arabic / English), support dark and light themes, and are built for Android and iOS from a single Dart codebase.

> **Current Status:** Both applications are fully functional UI prototypes with comprehensive mock data. Backend integration (API, authentication, real-time messaging) is planned for the next development phase.

---

## Repository Structure

```
hen_lhen/
│
├── patient_app/                  # Patient-facing Flutter application
│   ├── android/
│   ├── ios/
│   ├── assets/
│   │   ├── icons/
│   │   └── images/
│   ├── lib/
│   │   ├── config/
│   │   ├── models/
│   │   ├── screens/
│   │   └── widgets/
│   └── pubspec.yaml
│
├── doctor_app/                   # Doctor-facing Flutter application
│   ├── android/
│   ├── ios/
│   ├── assets/
│   │   └── icons/
│   ├── lib/
│   │   ├── config/
│   │   ├── models/
│   │   ├── screens/
│   │   └── widgets/
│   └── pubspec.yaml
│
├── packages/                     # Planned shared packages (monorepo)
│   ├── shared_core/              # Core utilities, constants, extensions
│   ├── shared_models/            # Unified data models (DTOs)
│   └── shared_ui/                # Shared widgets, theme, design system
│
├── apps/                         # Monorepo application aliases
│   ├── patient_app/
│   └── doctor_app/
│
├── docs/                         # Project documentation
│
└── README.md
```

### Directory Descriptions

| Directory | Description |
|-----------|-------------|
| `patient_app/` | Standalone Flutter project for the patient experience |
| `doctor_app/` | Standalone Flutter project for the doctor experience |
| `packages/shared_core/` | Planned: shared utilities, app-wide constants, base classes |
| `packages/shared_models/` | Planned: unified `DoctorModel`, `AppointmentModel`, shared DTOs |
| `packages/shared_ui/` | Planned: shared design system — `AppButton`, `AppTextField`, `AppColors`, `AppTheme` |
| `apps/` | Monorepo application entry points (future Melos workspace) |
| `docs/` | Architecture diagrams, API contracts, design specifications |

---

## Applications

### Patient App

**Package:** `hen_lehen_patient`  
**Primary Color:** `#E91E8C` (Rose)  
**Target Users:** Female patients

#### Purpose

The patient app is the primary consumer-facing product. It gives women access to a curated directory of female specialists, a streamlined booking and payment flow, real-time text-based consultations, and a supportive peer community — all within a safe, private environment.

#### Main Features

| Feature | Description |
|---------|-------------|
| **Onboarding** | 3-page animated introduction to the platform |
| **Authentication** | Email/password registration and login with form validation |
| **Doctor Discovery** | Browse and search doctors by specialty, rating, experience, and fee |
| **Doctor Profiles** | Full profiles with bio, stats, reviews, availability, and booking CTA |
| **Appointment Booking** | Select consultation type (online / clinic), date, and time slot |
| **Payment** | Payment method selection, promo code application, and price breakdown |
| **Online Chat** | Real-time text consultation linked to a confirmed appointment |
| **Appointment Management** | View upcoming, completed, and cancelled appointments with status tracking |
| **Community** | Women-only social feed with posts, likes, comments, and anonymous posting |
| **Favorites** | Save and quickly access preferred doctors |
| **Notifications** | In-app notification center with read/unread state |
| **Profile & Settings** | Edit profile, change theme, switch language, manage account |

#### Patient User Flow

```
App Launch
    │
    ├── First Launch ──► Onboarding (3 pages) ──► Login / Register
    │
    └── Returning User ──► Home Screen
                               │
              ┌────────────────┼────────────────┬────────────────┐
              ▼                ▼                ▼                ▼
           Home Tab     Appointments      Community          Profile
              │               │
    ┌─────────┤          ┌────┴─────┐
    │         │          │         │
  Search   Top       Upcoming  Completed
  Doctors  Doctors
    │
    ▼
Doctor Profile
    │
    ▼
Booking Screen ──► Payment Screen ──► Booking Success
                                            │
                                     Appointment Detail
                                            │
                                       Chat Screen
```

#### Patient App Folder Structure

```
lib/
├── main.dart
├── config/
│   ├── locale.dart        # LocaleProvider, AR/EN string maps (190+ keys)
│   ├── providers.dart     # All ChangeNotifier providers (auth, doctors, booking …)
│   ├── routes.dart        # GoRouter route definitions and named constants
│   └── theme.dart         # AppColors, AppTheme (light + dark), ThemeProvider
├── models/
│   └── models.dart        # All data models + MockData seed
├── screens/
│   ├── auth/              # OnboardingScreen, LoginScreen, RegisterScreen
│   ├── home/              # MainScreen (bottom nav), HomeTab
│   ├── appointments/      # AppointmentsTab, AppointmentDetailsScreen
│   ├── booking/           # BookingScreen, PaymentScreen, BookingSuccessScreen
│   ├── chat/              # ChatScreen
│   ├── community/         # CommunityTab, CreatePostScreen
│   ├── doctor/            # DoctorProfileScreen
│   ├── favorites/         # FavoritesScreen
│   ├── notifications/     # NotificationsScreen
│   ├── profile/           # ProfileTab, EditProfileScreen, SettingsScreen
│   └── search/            # SearchScreen
└── widgets/
    └── widgets.dart       # AppButton, AppTextField, DoctorCard, AppointmentCard …
```

---

### Doctor App

**Package:** `hen_lehen_doctor`  
**Primary Color:** `#7B9E89` (Sage Green)  
**Target Users:** Licensed female doctors

#### Purpose

The doctor app is the professional dashboard for the platform. It gives doctors a complete view of their daily schedule, tools to accept or reject incoming appointment requests, a direct consultation chat channel, clinic branch management, and a profile editor — all within a calm, professional interface.

#### Main Features

| Feature | Description |
|---------|-------------|
| **Authentication** | Email/password login and doctor registration with medical credentials |
| **Pending Approval** | Registration submissions enter a pending state pending admin review |
| **Dashboard** | Real-time stats: today's appointments, total patients, rating, monthly earnings |
| **Appointment Management** | Tabbed view of pending / confirmed / completed appointments |
| **Accept & Reject** | One-tap accept or reject for incoming appointment requests |
| **Online Chat** | Text-based consultation with typing indicator and session controls |
| **Patient List** | Searchable patient directory with visit history |
| **Branch Management** | Add, edit, activate/deactivate multiple clinic locations |
| **Profile Editor** | Edit name, phone, bio, and consultation fee |
| **Settings** | Theme toggle, language switcher, earnings summary, support |

#### Doctor User Flow

```
App Launch
    │
    ▼
Login Screen
    │
    ├── New Doctor ──► Registration Form ──► Pending Approval Screen
    │                  (name, email, phone,        (awaits admin action)
    │                   specialty, license,
    │                   experience, bio)
    │
    └── Verified Doctor ──► Dashboard (ShellRoute)
                                  │
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼
          Dashboard          Appointments          Patients
              │                   │
         Quick Actions      ┌─────┴──────┐
         ┌────┬────┐     Pending   Confirmed
         │    │    │        │         │
      Branches Profile Earnings  Accept/Reject  Start Chat
                                            │
                                       Chat Screen
                                            │
                                     End Consultation
```

#### Doctor App Folder Structure

```
lib/
├── main.dart
├── config/
│   ├── locale.dart        # LocaleProvider, AR/EN string maps
│   ├── providers.dart     # AuthProvider, AppointmentsProvider, BranchesProvider …
│   ├── routes.dart        # GoRouter with ShellRoute for bottom nav
│   └── theme.dart         # AppColors, AppTheme (light + dark), ThemeProvider
├── models/
│   └── models.dart        # DoctorModel, PatientModel, AppointmentModel, BranchModel + MockData
├── screens/
│   ├── auth/              # LoginScreen, RegisterScreen, PendingScreen
│   ├── dashboard/         # MainScreen (ShellRoute host), DashboardScreen
│   ├── appointments/      # AppointmentsScreen
│   ├── branches/          # BranchesScreen, AddBranchScreen
│   ├── chat/              # ChatScreen
│   ├── patients/          # PatientsScreen
│   ├── profile/           # ProfileScreen
│   └── settings/          # SettingsScreen
└── widgets/
    └── widgets.dart       # AppButton, AppTextField, StatCard, AppointmentCard, PatientCard
```

---

## Architecture Overview

### Pattern

Both applications follow the same architectural pattern:

```
┌─────────────────────────────────────────────────┐
│                   UI Layer                       │
│         Screens  ·  Widgets  ·  Theme            │
└─────────────────────┬───────────────────────────┘
                      │  reads / watches
┌─────────────────────▼───────────────────────────┐
│              State Management                    │
│    Provider (ChangeNotifier per feature)         │
│                                                  │
│  AuthProvider  ·  DoctorsProvider               │
│  AppointmentsProvider  ·  BookingProvider        │
│  CommunityProvider  ·  NotificationsProvider     │
│  FavoritesProvider  ·  BranchesProvider          │
│  ThemeProvider  ·  LocaleProvider                │
└─────────────────────┬───────────────────────────┘
                      │  currently mock — API layer planned
┌─────────────────────▼───────────────────────────┐
│              Data Layer (Planned)                │
│   Repositories  ·  DTOs  ·  API Client (Dio)    │
└─────────────────────────────────────────────────┘
```

### State Management

The applications use **Provider** (`ChangeNotifier`) for reactive state management.

- Each feature domain has a dedicated `ChangeNotifier` class
- All providers are registered at the app root via `MultiProvider`
- Screens access state using `context.watch<T>()` or `Provider.of<T>(context)`
- Business logic is contained entirely within provider classes

### Navigation

| App | Approach |
|-----|----------|
| `patient_app` | GoRouter with flat named routes; bottom nav managed via `IndexedStack` |
| `doctor_app` | GoRouter with `ShellRoute` for the bottom navigation shell |

### Localization

Both apps implement a custom `LocaleProvider` with a key-value string map for Arabic and English. The `Directionality` widget at the app root handles RTL/LTR layout switching automatically when the language changes.

### Theming

A shared color system (`AppColors`) and dual-theme setup (`AppTheme.lightTheme` / `AppTheme.darkTheme`) is managed by `ThemeProvider`. The Cairo typeface is used across both apps for consistent Arabic/Latin rendering.

### Current Data Layer

All data is served from in-memory `MockData` classes. Network calls are simulated with `Future.delayed`. No HTTP client or database is connected at this stage.

---

## Installation & Setup

### Prerequisites

| Requirement | Version |
|-------------|---------|
| Flutter SDK | ≥ 3.0.0 |
| Dart SDK | ≥ 3.0.0 |
| Xcode (iOS) | Latest stable |
| Android Studio / SDK | Latest stable |

Verify your Flutter installation:

```bash
flutter doctor
```

### Clone the Repository

```bash
git clone https://github.com/menna3lwan/hen_lhen.git
cd hen_lhen
```

### Patient App — Setup

```bash
cd patient_app
flutter pub get
```

### Doctor App — Setup

```bash
cd doctor_app
flutter pub get
```

---

## Running the Applications

### Patient App

```bash
cd patient_app

# Run on a connected device or emulator
flutter run

# Run on a specific device
flutter run -d <device_id>

# Run in release mode
flutter run --release
```

### Doctor App

```bash
cd doctor_app

# Run on a connected device or emulator
flutter run

# Run on a specific device
flutter run -d <device_id>

# Run in release mode
flutter run --release
```

### List Available Devices

```bash
flutter devices
```

### Build APK

```bash
# Patient App
cd patient_app && flutter build apk --release

# Doctor App
cd doctor_app && flutter build apk --release
```

### Build for iOS

```bash
# Patient App
cd patient_app && flutter build ios --release

# Doctor App
cd doctor_app && flutter build ios --release
```

---

## Dependencies

### Shared Dependencies (Both Apps)

| Package | Version | Purpose |
|---------|---------|---------|
| `flutter_localizations` | SDK | AR/EN localization delegates |
| `provider` | ^6.1.1 | State management (ChangeNotifier) |
| `go_router` | ^13.0.0 | Declarative navigation |
| `shared_preferences` | ^2.2.2 | Local key-value persistence |
| `google_fonts` | ^6.1.0 | Cairo typeface |
| `flutter_rating_bar` | ^4.0.1 | Star rating display |

### Patient App Only

| Package | Version | Purpose |
|---------|---------|---------|
| `iconsax` | ^0.0.8 | Extended icon set |

### Dev Dependencies (Both Apps)

| Package | Version | Purpose |
|---------|---------|---------|
| `flutter_lints` | ^3.0.0 | Dart static analysis rules |
| `flutter_launcher_icons` | ^0.13.1 | App icon generation |

### Planned Dependencies (Backend Phase)

| Package | Purpose |
|---------|---------|
| `dio` | HTTP client with interceptors |
| `flutter_secure_storage` | Encrypted token storage |
| `firebase_core` + `firebase_messaging` | Push notifications |
| `supabase_flutter` | Backend, database, real-time |

---

## Development Guidelines

### Branching Strategy

```
main              ← production-ready code
  └── develop     ← integration branch
        ├── feature/patient-<feature-name>
        ├── feature/doctor-<feature-name>
        ├── fix/patient-<bug-description>
        ├── fix/doctor-<bug-description>
        └── chore/<task-description>
```

- All feature work branches from `develop`
- Pull requests target `develop`, never directly to `main`
- `main` is updated via a release PR from `develop`
- Branch names use `kebab-case`

### Code Organization

```
DO:
  ✓ One ChangeNotifier per feature domain
  ✓ Keep business logic inside providers, not screens
  ✓ Use context.watch<T>() for reactive reads in build()
  ✓ Use context.read<T>() for one-shot calls in event handlers
  ✓ Use locale.get('key') for all user-facing strings — no hardcoded text
  ✓ Use AlignmentDirectional instead of Alignment for RTL compatibility
  ✓ Dispose all TextEditingControllers and ScrollControllers

DON'T:
  ✗ Add business logic directly inside widget build methods
  ✗ Nest providers inside other providers
  ✗ Create new widget files for single-use internal widgets — use private classes (_MyWidget)
  ✗ Hardcode Arabic or English strings in widget trees
  ✗ Use double.parse() without input validation
```

### Adding a New Screen

1. Create the screen file in the appropriate `screens/<feature>/` folder
2. Add a route constant and `GoRoute` entry in `config/routes.dart`
3. Add any i18n keys to both `_ar` and `_en` maps in `config/locale.dart`
4. Register any new providers in `config/providers.dart` and `AppProviders.providers`
5. Add the model (if new) to `models/models.dart`

### Adding i18n Strings

All user-visible strings must be added to **both** maps in `locale.dart`:

```dart
// In LocaleProvider
static const Map<String, String> _ar = {
  'myNewKey': 'النص بالعربية',
};

static const Map<String, String> _en = {
  'myNewKey': 'English text',
};

// Usage in a widget
Text(locale.get('myNewKey'))
```

### Theming

Always reference `AppColors` constants — never use raw `Color(0x...)` values in widget code:

```dart
// Correct
color: AppColors.primary

// Incorrect
color: Color(0xFFE91E8C)
```

### Code Style

- Follow the rules defined in `analysis_options.yaml`
- Run `flutter analyze` before every commit — zero warnings policy
- Format with `dart format .` before committing

---

## Future Improvements

### High Priority — Stabilization

| Item | Description |
|------|-------------|
| Auth persistence | Use `shared_preferences` to persist login state, theme, and language across sessions |
| Router guard | Add GoRouter `redirect` callbacks to protect authenticated routes in both apps |
| RTL chat fix | Replace `Alignment.centerLeft/Right` with `AlignmentDirectional` in the doctor app chat screen |
| Input validation | Add `try/catch` around `double.parse()` in the doctor profile editor |
| Dead code removal | Delete orphaned `user_model.dart` and `appointments_screen.dart` in the patient app |

### Medium Priority — Shared Package Extraction

The `/packages` directory contains three pre-scaffolded packages. Populating them will eliminate the current code duplication between apps:

| Package | Contents |
|---------|----------|
| `shared_ui` | `AppButton`, `AppTextField`, `StatCard`, `AppListTile`, `EmptyState`, `LoadingIndicator`, `SectionHeader`, `AppColors`, `AppTheme` |
| `shared_models` | Unified `DoctorModel`, `AppointmentModel`, `PatientModel`, `UserModel` with full `copyWith` and `fromJson`/`toJson` |
| `shared_core` | `LocaleProvider` base, common i18n keys, extension methods, validators |

After extraction, both apps import from these packages instead of duplicating code. Use **Melos** to manage the monorepo workspace.

### Medium Priority — Backend Integration

| Layer | Technology | Notes |
|-------|-----------|-------|
| HTTP client | `dio` | Add a base interceptor for auth tokens and error handling |
| Authentication | Firebase Auth or Supabase Auth | Replace mock `Future.delayed` auth with real token flows |
| Token storage | `flutter_secure_storage` | Never store tokens in `shared_preferences` |
| Database | Supabase (PostgreSQL) | Row-level security for patient/doctor data isolation |
| Real-time chat | Supabase Realtime or Firebase RTDB | Replace the local `List<_Message>` with a live stream |
| Push notifications | Firebase Cloud Messaging | Appointment reminders, acceptance notifications |
| File uploads | Supabase Storage | Profile photos, chat attachments |

#### Suggested Repository Layer

```
lib/
├── repositories/
│   ├── auth_repository.dart
│   ├── appointment_repository.dart
│   ├── doctor_repository.dart
│   └── chat_repository.dart
└── services/
    ├── api_client.dart          # Dio instance + interceptors
    └── notification_service.dart
```

### Long-Term — Scalability

| Improvement | Description |
|-------------|-------------|
| **Testing** | Unit tests for all providers; widget tests for auth, booking, and dashboard flows |
| **CI/CD** | GitHub Actions pipeline: lint → test → build APK/IPA on every PR |
| **Admin Panel** | Web dashboard (Flutter Web or Next.js) for doctor verification and content moderation |
| **Video Consultation** | Integrate Agora or Daily.co for video-based consultations |
| **Medical Records** | Structured patient medical history with PDF export |
| **Analytics** | Firebase Analytics for feature usage and funnel tracking |
| **Accessibility** | Screen reader support, minimum 4.5:1 contrast ratios, scalable text |

---

## Platform Support

| Platform | Status |
|----------|--------|
| Android | ✅ Supported |
| iOS | ✅ Supported |
| Web | Not planned |
| Desktop | Not planned |

---

## License

This project is developed as part of the **Hen Lehen – هُنَّ لَهُنَّ** platform.  
All rights reserved © 2025 Hen Lehen.

---

<div align="center">

Built with Flutter · Designed for women · هُنَّ لَهُنَّ

</div>
