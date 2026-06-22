import 'dart:io';

void main() {
  final filesToClean = {
    // patient_app unused imports
    '/Users/menna3lwan/hen_lhen/patient_app/lib/screens/community/create_post_screen.dart': [
      "import '../../widgets/widgets.dart';",
    ],
    '/Users/menna3lwan/hen_lhen/patient_app/lib/screens/favorites/favorites_screen.dart': [
      "import '../../models/models.dart';",
    ],
    '/Users/menna3lwan/hen_lhen/patient_app/lib/screens/profile/edit_profile_screen.dart': [
      "import '../../widgets/widgets.dart';",
    ],
    // doctor_app unused imports
    '/Users/menna3lwan/hen_lhen/doctor_app/lib/screens/auth/login_screen.dart': [
      "import '../../widgets/widgets.dart';",
    ],
    '/Users/menna3lwan/hen_lhen/doctor_app/lib/screens/auth/register_screen.dart': [
      "import '../../widgets/widgets.dart';",
    ],
    '/Users/menna3lwan/hen_lhen/doctor_app/lib/screens/branches/add_branch_screen.dart': [
      "import '../../widgets/widgets.dart';",
    ],
    '/Users/menna3lwan/hen_lhen/doctor_app/lib/screens/dashboard/main_screen.dart': [
      "import 'package:shared_ui/shared_ui.dart';",
    ],
    '/Users/menna3lwan/hen_lhen/doctor_app/lib/screens/profile/profile_screen.dart': [
      "import '../../widgets/widgets.dart';",
    ],
  };

  for (final entry in filesToClean.entries) {
    final file = File(entry.key);
    if (!file.existsSync()) {
      print('SKIP (not found): ${entry.key}');
      continue;
    }
    String content = file.readAsStringSync();
    bool changed = false;
    for (final importLine in entry.value) {
      if (content.contains(importLine)) {
        content = content.replaceAll('$importLine\n', '');
        changed = true;
      }
    }
    if (changed) {
      file.writeAsStringSync(content);
      print('Cleaned: ${entry.key}');
    } else {
      print('No change: ${entry.key}');
    }
  }
}
