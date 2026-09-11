import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';
import '../../core/constants/app_radius.dart';
import '../../core/constants/app_spacing.dart';
import '../../core/widgets/app_button.dart';
import '../../core/widgets/app_card.dart';
import '../../core/widgets/app_chip.dart';
import '../../core/widgets/app_image_placeholder.dart';
import '../models/artisan_model.dart';

class ArtisanCard extends StatelessWidget {
  final ArtisanProfile artisan;
  final VoidCallback? onTap;
  final VoidCallback? onConnectRfq;

  const ArtisanCard({
    super.key,
    required this.artisan,
    this.onTap,
    this.onConnectRfq,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return AppCard(
      padding: AppSpacing.paddingAllBase,
      onTap: onTap,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 52,
                height: 52,
                decoration: BoxDecoration(
                  color: theme.colorScheme.primaryContainer,
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: AppColors.primaryLight.withValues(alpha: 0.3),
                    width: 1.5,
                  ),
                ),
                child: Center(
                  child: Text(
                    artisan.name.substring(0, 1),
                    style: TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.bold,
                      color: theme.colorScheme.primary,
                    ),
                  ),
                ),
              ),
              AppSpacing.gapH12,
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Flexible(
                          child: Text(
                            artisan.name,
                            style: theme.textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.w700,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        if (artisan.isNationalAwardee) ...[
                          AppSpacing.gapH4,
                          const Icon(Icons.military_tech_rounded, size: 16, color: AppColors.tertiary),
                        ],
                      ],
                    ),
                    AppSpacing.gapV4,
                    Text(
                      '${artisan.craftSpecialty} · ${artisan.clusterRegion}, ${artisan.state}',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.onSurface.withValues(alpha: 0.65),
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    AppSpacing.gapV4,
                    Row(
                      children: [
                        const Icon(Icons.star_rounded, size: 14, color: AppColors.tertiary),
                        AppSpacing.gapH4,
                        Text(
                          '${artisan.rating} (${artisan.reviewCount} reviews)',
                          style: theme.textTheme.bodySmall?.copyWith(
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        AppSpacing.gapH8,
                        Text(
                          '· ${artisan.yearsOfExperience}+ yrs exp',
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
          AppSpacing.gapV12,
          Text(
            artisan.storySnippet,
            style: theme.textTheme.bodySmall?.copyWith(
              height: 1.4,
              color: theme.colorScheme.onSurface.withValues(alpha: 0.8),
            ),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
          AppSpacing.gapV12,
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  if (artisan.isGiCertified) AppChip.giTag(),
                  AppSpacing.gapH8,
                  AppChip.handmade(),
                ],
              ),
              if (onConnectRfq != null)
                SizedBox(
                  height: 32,
                  child: AppButton(
                    label: 'Request Quote',
                    variant: AppButtonVariant.outline,
                    height: 32,
                    isFullWidth: false,
                    onPressed: onConnectRfq,
                  ),
                ),
            ],
          ),
        ],
      ),
    );
  }
}

class StoreCard extends StatelessWidget {
  final ArtisanStore store;
  final VoidCallback? onTap;

  const StoreCard({
    super.key,
    required this.store,
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
                aspectRatio: 2.2,
                child: AppImagePlaceholder(
                  borderRadius: BorderRadius.vertical(top: Radius.circular(AppRadius.md)),
                  icon: Icons.storefront_outlined,
                ),
              ),
              if (store.acceptsCustomRfq)
                Positioned(
                  top: 8,
                  right: 8,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: const BoxDecoration(
                      color: AppColors.secondary,
                      borderRadius: AppRadius.borderXs,
                    ),
                    child: const Text(
                      'CUSTOM RFQ OPEN',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 9,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
            ],
          ),
          Padding(
            padding: AppSpacing.paddingAllBase,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Text(
                        store.storeName,
                        style: theme.textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.w700,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    Row(
                      children: [
                        const Icon(Icons.star_rounded, size: 14, color: AppColors.tertiary),
                        AppSpacing.gapH4,
                        Text(
                          store.rating.toStringAsFixed(1),
                          style: theme.textTheme.bodySmall?.copyWith(fontWeight: FontWeight.w700),
                        ),
                      ],
                    ),
                  ],
                ),
                AppSpacing.gapV4,
                Text(
                  'By ${store.artisanName} · ${store.region}',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.65),
                  ),
                ),
                AppSpacing.gapV8,
                Row(
                  children: [
                    Icon(Icons.inventory_2_outlined, size: 14, color: theme.colorScheme.primary),
                    AppSpacing.gapH4,
                    Text(
                      '${store.totalProducts} Authentic Handicrafts Listed',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.primary,
                        fontWeight: FontWeight.w600,
                      ),
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
