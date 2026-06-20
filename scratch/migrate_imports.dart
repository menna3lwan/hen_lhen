import 'dart:io';

void main() {
  final directories = [
    Directory('/Users/menna3lwan/hen_lhen/patient_app/lib'),
    Directory('/Users/menna3lwan/hen_lhen/doctor_app/lib'),
  ];

  for (final dir in directories) {
    if (!dir.existsSync()) continue;
    
    final files = dir.listSync(recursive: true).whereType<File>().where((f) => f.path.endsWith('.dart'));
    for (final file in files) {
      String content = file.readAsStringSync();
      bool changed = false;
      
      final themePattern = RegExp(r"import '.*config/theme\.dart';");
      if (themePattern.hasMatch(content)) {
        content = content.replaceAll(themePattern, "import 'package:shared_ui/shared_ui.dart';");
        changed = true;
      }
      
      if (changed) {
        file.writeAsStringSync(content);
        print('Updated ${file.path}');
      }
    }
  }
}
