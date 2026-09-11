import 'package:flutter/material.dart';
import '../constants/app_radius.dart';

class AppImagePlaceholder extends StatelessWidget {
  final double? width;
  final double? height;
  final BorderRadius? borderRadius;
  final IconData icon;

  const AppImagePlaceholder({
    super.key,
    this.width,
    this.height,
    this.borderRadius,
    this.icon = Icons.brush_outlined,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest,
        borderRadius: borderRadius ?? AppRadius.borderMd,
      ),
      child: Center(
        child: Icon(
          icon,
          size: 32,
          color: theme.colorScheme.onSurfaceVariant.withValues(alpha: 0.5),
        ),
      ),
    );
  }
}
