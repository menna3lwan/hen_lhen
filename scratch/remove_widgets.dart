import 'dart:io';

void main() {
  final files = [
    File('/Users/menna3lwan/hen_lhen/patient_app/lib/widgets/widgets.dart'),
    File('/Users/menna3lwan/hen_lhen/doctor_app/lib/widgets/widgets.dart'),
  ];

  final buttonRegex1 = RegExp(r'class AppButton extends StatelessWidget \{.*?\n\}\n', dotAll: true);
  final textFieldRegex1 = RegExp(r'class AppTextField extends StatefulWidget \{.*?\n\}\n', dotAll: true);
  final textFieldStateRegex1 = RegExp(r'class _AppTextFieldState extends State<AppTextField> \{.*?\n\}\n', dotAll: true);

  final textFieldRegex2 = RegExp(r'class AppTextField extends StatelessWidget \{.*?\n\}\n', dotAll: true);
  
  final commentsRegex = RegExp(r'// ==================== APP BUTTON ====================\n|// ==================== APP TEXT FIELD ====================\n');

  for (final file in files) {
    if (!file.existsSync()) continue;
    
    String content = file.readAsStringSync();
    
    content = content.replaceAll(buttonRegex1, '');
    content = content.replaceAll(textFieldRegex1, '');
    content = content.replaceAll(textFieldStateRegex1, '');
    content = content.replaceAll(textFieldRegex2, '');
    content = content.replaceAll(commentsRegex, '');
    
    file.writeAsStringSync(content);
    print('Cleaned ${file.path}');
  }
}
