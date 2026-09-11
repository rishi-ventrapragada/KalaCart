import 'package:flutter/material.dart';
import '../constants/app_colors.dart';
import '../constants/app_radius.dart';
import '../constants/app_spacing.dart';

enum AppChipVariant { filled, outline, filter, badge }

class AppChip extends StatelessWidget {
  final String label;
  final Widget? icon;
  final bool isSelected;
  final ValueChanged<bool>? onSelected;
  final VoidCallback? onTap;
  final AppChipVariant variant;
  final Color? color;
  final Color? textColor;

  const AppChip({
    super.key,
    required this.label,
    this.icon,
    this.isSelected = false,
    this.onSelected,
    this.onTap,
    this.variant = AppChipVariant.filter,
    this.color,
    this.textColor,
  });

  factory AppChip.giTag({String label = 'GI TAGGED'}) {
    return AppChip(
      label: label,
      variant: AppChipVariant.badge,
      color: AppColors.giTag,
      textColor: Colors.white,
      icon: const Icon(Icons.verified_rounded, size: 12, color: Colors.white),
    );
  }

  factory AppChip.handmade({String label = 'HANDMADE'}) {
    return AppChip(
      label: label,
      variant: AppChipVariant.badge,
      color: AppColors.handmade,
      textColor: Colors.white,
      icon: const Icon(Icons.handshake_rounded, size: 12, color: Colors.white),
    );
  }

  factory AppChip.aiStudio({String label = 'AI VERIFIED'}) {
    return AppChip(
      label: label,
      variant: AppChipVariant.badge,
      color: AppColors.aiStudio,
      textColor: Colors.white,
      icon: const Icon(Icons.auto_awesome_rounded, size: 12, color: Colors.white),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    if (variant == AppChipVariant.badge) {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
        decoration: BoxDecoration(
          color: color ?? AppColors.primary,
          borderRadius: AppRadius.borderXs,
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (icon != null) ...[
              icon!,
              AppSpacing.gapH4,
            ],
            Text(
              label,
              style: TextStyle(
                color: textColor ?? Colors.white,
                fontSize: 10,
                fontWeight: FontWeight.w700,
                letterSpacing: 0.6,
              ),
            ),
          ],
        ),
      );
    }

    if (variant == AppChipVariant.filter) {
      return FilterChip(
        label: Text(label),
        avatar: icon,
        selected: isSelected,
        onSelected: onSelected,
        shape: AppRadius.shapeMd,
        selectedColor: theme.colorScheme.primaryContainer,
        labelStyle: TextStyle(
          fontSize: 12,
          fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
          color: isSelected ? AppColors.onPrimaryContainer : theme.colorScheme.onSurface,
        ),
      );
    }

    return ActionChip(
      label: Text(label),
      avatar: icon,
      onPressed: onTap,
      shape: AppRadius.shapeMd,
      backgroundColor: color,
    );
  }
}
