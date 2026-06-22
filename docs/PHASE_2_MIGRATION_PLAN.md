# Phase 2 — GetX Migration Plan
## هُنَّ لَهُنَّ (Hen Lehen) — Provider → GetX Migration

---

## 1. Migration Strategy

**Approach:** Bottom-up migration — shared packages first, then each app.

**Order:**
1. `shared_ui` — Convert ThemeProvider to GetxController
2. `patient_app` — Larger app, more providers
3. `doctor_app` — Smaller, mirrors patient_app patterns

## 2. Migration Steps

### Step 1: Dependencies
- Add `get: ^4.6.6` to all pubspec.yaml files
- Remove `provider: ^6.1.1` and `go_router: ^13.0.0`

### Step 2: Shared UI — ThemeProvider
- Convert `ThemeProvider extends ChangeNotifier` → `ThemeController extends GetxController`
- Replace `notifyListeners()` → `.obs` reactive variables
- Update `AppButton`, `AppTextField` that reference context-based theme

### Step 3: Patient App Controllers (from providers.dart)
Each ChangeNotifier becomes a GetxController:

| Current Provider | New Controller | File |
|---|---|---|
| `AuthProvider` | `AuthController` | `controllers/auth_controller.dart` |
| `DoctorsProvider` | `DoctorsController` | `controllers/doctors_controller.dart` |
| `AppointmentsProvider` | `AppointmentsController` | `controllers/appointments_controller.dart` |
| `FavoritesProvider` | `FavoritesController` | `controllers/favorites_controller.dart` |
| `CommunityProvider` | `CommunityController` | `controllers/community_controller.dart` |
| `NotificationsProvider` | `NotificationsController` | `controllers/notifications_controller.dart` |
| `BookingProvider` | `BookingController` | `controllers/booking_controller.dart` |
| `LocaleProvider` | `LocaleController` | `controllers/locale_controller.dart` |

### Step 4: Patient App Navigation
- Replace `MaterialApp.router` → `GetMaterialApp`
- Replace GoRouter routes → `GetPage` list with `Bindings`
- Replace `context.go/push` → `Get.toNamed/Get.offAllNamed`
- Auth guard via `GetMiddleware` instead of GoRouter redirect

### Step 5: Patient App Screens
- Remove all `context.watch<X>()`, `context.read<X>()`, `Provider.of<X>(context)`
- Replace with `Get.find<XController>()` and `Obx(() => ...)`
- Remove `Consumer` widgets

### Step 6: Doctor App Controllers
| Current Provider | New Controller |
|---|---|
| `AuthProvider` | `AuthController` |
| `AppointmentsProvider` | `AppointmentsController` |
| `PatientsProvider` | `PatientsController` |
| `BranchesProvider` | `BranchesController` |
| `EarningsProvider` | `EarningsController` |
| `LocaleProvider` | `LocaleController` |

### Step 7: Doctor App Navigation + Screens
- Same pattern as patient_app

## 3. Bindings Architecture

```
// Example: Patient App
class AuthBinding extends Bindings {
  @override
  void dependencies() {
    Get.lazyPut(() => AuthController());
  }
}

class HomeBinding extends Bindings {
  @override
  void dependencies() {
    Get.lazyPut(() => DoctorsController());
    Get.lazyPut(() => AppointmentsController());
  }
}
```

## 4. Route Architecture

```
// Patient App GetPages
GetPage(name: '/login', page: () => LoginScreen(), binding: AuthBinding()),
GetPage(name: '/main', page: () => MainScreen(), bindings: [
  HomeBinding(),
  AppointmentsBinding(),
  CommunityBinding(),
  ProfileBinding(),
]),
GetPage(name: '/doctor/:id', page: () => DoctorProfileScreen()),
GetPage(name: '/booking', page: () => BookingScreen(), binding: BookingBinding()),
```

## 5. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Breaking navigation flow | High | Test all routes after migration |
| Losing auth state on navigation | High | Use `Get.put` (permanent) for AuthController |
| Controller disposal timing | Medium | Use `permanent: true` for global controllers |
| `extra` data passing breaks | Medium | Use `Get.arguments` or controller state |
| Theme not updating across app | Low | ThemeController as permanent singleton |
| Locale not updating across app | Low | LocaleController as permanent singleton |

## 6. Files Modified (Estimated)

| Area | Files | Action |
|---|---|---|
| pubspec.yaml (×5) | 5 | Edit deps |
| shared_ui | 3 | Convert ThemeProvider |
| patient_app/providers.dart | 1 | Delete → 8 controller files |
| patient_app/routes.dart | 1 | Rewrite |
| patient_app/main.dart | 1 | Rewrite |
| patient_app/screens/* | 17 | Update provider access |
| patient_app/widgets/* | 1 | Update provider access |
| patient_app/locale.dart | 1 | Convert to controller |
| patient_app/theme.dart | 1 | Remove (use shared_ui) |
| doctor_app/providers.dart | 1 | Delete → 5 controller files |
| doctor_app/routes.dart | 1 | Rewrite |
| doctor_app/main.dart | 1 | Rewrite |
| doctor_app/screens/* | 11 | Update provider access |
| doctor_app/widgets/* | 1 | Update provider access |
| doctor_app/locale.dart | 1 | Convert to controller |
| doctor_app/theme.dart | 1 | Remove (use shared_ui) |
| **Total** | **~50 files** | |

---

*Migration Plan Complete — Proceeding to Phase 3: Execution*
