import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';
import '../../core/constants/app_radius.dart';
import '../../core/constants/app_spacing.dart';
import '../../core/utils/currency_formatter.dart';
import '../../core/widgets/app_card.dart';
import '../../core/widgets/app_chip.dart';
import '../../core/widgets/app_image_placeholder.dart';
import '../models/craft_product.dart';

class CraftProductCard extends StatelessWidget {
  final CraftProduct product;
  final VoidCallback? onTap;

  const CraftProductCard({
    super.key,
    required this.product,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return AppCard(
      padding: EdgeInsets.zero,
      onTap: onTap,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Stack(
            children: [
              const AspectRatio(
                aspectRatio: 1.2,
                child: AppImagePlaceholder(
                  borderRadius: BorderRadius.vertical(top: Radius.circular(AppRadius.md)),
                  icon: Icons.palette_outlined,
                ),
              ),
              if (product.isGiTagged)
                Positioned(
                  top: 8,
                  left: 8,
                  child: AppChip.giTag(),
                ),
            ],
          ),
          Padding(
            padding: AppSpacing.paddingAllSm,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  product.title,
                  style: theme.textTheme.titleMedium,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                AppSpacing.gapV4,
                Text(
                  '${product.artisanName} · ${product.region}',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                AppSpacing.gapV8,
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      CurrencyFormatter.formatINR(product.price),
                      style: theme.textTheme.titleMedium?.copyWith(
                        color: theme.colorScheme.primary,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    if (product.rating != null)
                      Row(
                        children: [
                          const Icon(Icons.star_rounded, size: 14, color: AppColors.tertiary),
                          AppSpacing.gapH4,
                          Text(
                            product.rating!.toStringAsFixed(1),
                            style: theme.textTheme.bodySmall?.copyWith(
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
