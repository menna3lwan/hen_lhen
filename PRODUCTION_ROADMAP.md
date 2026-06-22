# 🚀 Hen Lehen — Production Roadmap

This document outlines the steps remaining to launch the **patient_app** and **doctor_app** in a production environment.

---

## 1. App Identity & Branding

| Item | patient_app | doctor_app |
|------|-------------|------------|
| **Bundle ID (iOS)** | `com.henlehen.patient` | `com.henlehen.doctor` |
| **Application ID (Android)** | `com.henlehen.patient` | `com.henlehen.doctor` |
| **App Name (AR)** | حِن لِحَن | حِن لِحَن — طبيب |
| **App Icon** | ✅ Configured via `flutter_launcher_icons` | ✅ Configured via `flutter_launcher_icons` |
| **Splash Screen** | Needs `flutter_native_splash` setup | Needs `flutter_native_splash` setup |

### Action Items
- [ ] Finalize app icon assets (1024×1024 PNG).
- [ ] Add `flutter_native_splash` with branded splash screen.
- [ ] Update `AndroidManifest.xml` and `Info.plist` with correct app names.
- [ ] Update Android `applicationId` and iOS `PRODUCT_BUNDLE_IDENTIFIER`.

---

## 2. Environment & Flavors

### Recommended Flavor Setup
```
├── dev      → Mock API, debug logging
├── staging  → Real API (staging server), verbose logging
└── prod     → Real API (production server), minimal logging
```

### Action Items
- [ ] Create `lib/config/env.dart` with environment-specific configuration.
- [ ] Setup Android product flavors in `build.gradle.kts`.
- [ ] Setup iOS schemes (Dev, Staging, Prod) in Xcode.
- [ ] Use `--dart-define=ENVIRONMENT=prod` for builds.

---

## 3. Backend API Integration

### Current State
- `ApiClient` is set up with `Dio`, timeouts, and interceptor placeholders.
- `AuthRepository` is wired into `AuthProvider` but currently returns mock data.

### Action Items
- [ ] Replace mock data in all Repositories with real API calls.
- [ ] Implement token refresh logic in `ApiClient` interceptors.
- [ ] Add `flutter_secure_storage` for secure token persistence.
- [ ] Implement proper logout flow (clear tokens, navigate to login).

---

## 4. Security

| Concern | Status | Action |
|---------|--------|--------|
| API tokens stored securely | ❌ | Use `flutter_secure_storage` |
| Certificate pinning | ❌ | Add via Dio interceptor |
| Input sanitization | ⚠️ Partial | Review all text fields |
| ProGuard/R8 (Android) | ❌ | Enable in `build.gradle` |
| Code obfuscation | ❌ | Add `--obfuscate --split-debug-info` to build |

---

## 5. Testing Strategy

### Unit Tests
- [ ] Test all Repository classes (mock Dio responses).
- [ ] Test all Provider state transitions.

### Widget Tests
- [ ] Test critical screens: Login, Register, Booking, Chat.

### Integration Tests
- [ ] End-to-end login → book appointment flow.
- [ ] End-to-end doctor registration → dashboard flow.

---

## 6. CI/CD Pipeline

### Recommended: GitHub Actions

```yaml
# .github/workflows/build.yml
name: Build & Test
on: [push, pull_request]
jobs:
  build:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - uses: subosito/flutter-action@v2
        with:
          flutter-version: '3.x'
      - run: flutter pub get
        working-directory: patient_app
      - run: flutter analyze
        working-directory: patient_app
      - run: flutter test
        working-directory: patient_app
      - run: flutter build apk --release
        working-directory: patient_app
```

### Action Items
- [ ] Create `.github/workflows/build.yml` for automated builds.
- [ ] Add separate workflows for `patient_app` and `doctor_app`.
- [ ] Setup Fastlane for automated store deployment.

---

## 7. Signing & Store Submission

### Android
- [ ] Generate upload keystore (`keytool -genkey -v -keystore upload-keystore.jks`).
- [ ] Configure `key.properties` (DO NOT commit to git).
- [ ] Update `build.gradle.kts` with signing config.
- [ ] Prepare Play Store listing (screenshots, description, privacy policy).

### iOS
- [ ] Enroll in Apple Developer Program.
- [ ] Configure provisioning profiles and certificates.
- [ ] Setup App Store Connect listing.
- [ ] Prepare App Review screenshots and metadata.

---

## 8. Analytics & Monitoring

- [ ] Add Firebase Analytics for user behavior tracking.
- [ ] Add Firebase Crashlytics for crash reporting.
- [ ] Setup remote config for feature flags.

---

## 9. Pre-Launch Checklist

- [x] Global error handler (`FlutterError.onError`).
- [x] Router guards for authentication.
- [x] Repository/Service architecture layer.
- [x] Shared UI packages for consistency.
- [x] `cached_network_image` for image performance.
- [ ] Remove all `TODO` comments or convert to tracked issues.
- [ ] Run `flutter build apk --release` successfully.
- [ ] Run `flutter build ios --release` successfully.
- [ ] Test on physical Android device.
- [ ] Test on physical iOS device.
- [ ] Performance profiling with Flutter DevTools.
