import 'package:flutter/material.dart';
import '../theme.dart';

class AppButton extends StatelessWidget {
  final String text;
  final VoidCallback? onPressed;
  final bool isLoading, isOutlined, isFullWidth;
  final Color? color;
  final IconData? icon;
  final double height;

  const AppButton({super.key, required this.text, this.onPressed, this.isLoading = false, this.isOutlined = false, this.isFullWidth = true, this.color, this.icon, this.height = 52});

  @override
  Widget build(BuildContext context) {
    final btnColor = color ?? AppColors.primary;
    Widget child = isLoading ? SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2.5, color: isOutlined ? btnColor : Colors.white)) : Row(mainAxisSize: MainAxisSize.min, mainAxisAlignment: MainAxisAlignment.center, children: [if (icon != null) ...[Icon(icon, size: 20), const SizedBox(width: 8)], Text(text)]);
    if (isOutlined) return SizedBox(width: isFullWidth ? double.infinity : null, height: height, child: OutlinedButton(onPressed: isLoading ? null : onPressed, style: OutlinedButton.styleFrom(foregroundColor: btnColor, side: BorderSide(color: btnColor, width: 1.5), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))), child: child));
    return SizedBox(width: isFullWidth ? double.infinity : null, height: height, child: ElevatedButton(onPressed: isLoading ? null : onPressed, style: ElevatedButton.styleFrom(backgroundColor: btnColor, foregroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)), elevation: 2, shadowColor: btnColor.withOpacity(0.3)), child: child));
  }
}
