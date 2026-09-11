import 'package:flutter/material.dart';
import '../constants/app_radius.dart';
import '../constants/app_spacing.dart';

class AppCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;
  final EdgeInsetsGeometry? margin;
  final VoidCallback? onTap;
  final Color? backgroundColor;
  final Border? border;
  final double? elevation;

  const AppCard({
    super.key,
    required this.child,
    this.padding = AppSpacing.paddingAllBase,
    this.margin,
    this.onTap,
    this.backgroundColor,
    this.border,
    this.elevation,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    Widget cardContent = Padding(
      padding: padding,
      child: child,
    );

    if (onTap != null) {
      cardContent = InkWell(
        onTap: onTap,
        borderRadius: AppRadius.borderMd,
        child: cardContent,
      );
    }

    return Card(
      margin: margin,
      elevation: elevation ?? 0,
      color: backgroundColor ?? theme.cardColor,
      shape: AppRadius.shapeMd,
      clipBehavior: Clip.antiAlias,
      child: cardContent,
    );
  }
}
