import 'package:flutter/material.dart';
import '../theme.dart';

class AppTextField extends StatefulWidget {
  final TextEditingController? controller;
  final String? label, hint;
  final bool obscureText, showPasswordToggle, enabled, readOnly;
  final TextInputType? keyboardType;
  final Widget? prefixIcon, suffixIcon;
  final String? Function(String?)? validator;
  final int maxLines;
  final void Function(String)? onChanged, onSubmitted;
  final VoidCallback? onTap;
  final TextInputAction? textInputAction;

  const AppTextField({super.key, this.controller, this.label, this.hint, this.obscureText = false, this.showPasswordToggle = false, this.keyboardType, this.prefixIcon, this.suffixIcon, this.validator, this.maxLines = 1, this.onChanged, this.onSubmitted, this.enabled = true, this.readOnly = false, this.onTap, this.textInputAction});

  @override
  State<AppTextField> createState() => _AppTextFieldState();
}

class _AppTextFieldState extends State<AppTextField> {
  bool _obscureText = true;
  @override
  void initState() { super.initState(); _obscureText = widget.obscureText; }
  @override
  Widget build(BuildContext context) {
    return TextFormField(controller: widget.controller, obscureText: widget.showPasswordToggle ? _obscureText : widget.obscureText, keyboardType: widget.keyboardType, maxLines: widget.obscureText ? 1 : widget.maxLines, onChanged: widget.onChanged, onFieldSubmitted: widget.onSubmitted, enabled: widget.enabled, readOnly: widget.readOnly, onTap: widget.onTap, textInputAction: widget.textInputAction, decoration: InputDecoration(labelText: widget.label, hintText: widget.hint, prefixIcon: widget.prefixIcon, suffixIcon: widget.showPasswordToggle ? IconButton(icon: Icon(_obscureText ? Icons.visibility_off_outlined : Icons.visibility_outlined, color: AppColors.textSecondaryLight), onPressed: () => setState(() => _obscureText = !_obscureText)) : widget.suffixIcon), validator: widget.validator);
  }
}
