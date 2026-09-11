import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';
import '../../core/constants/app_spacing.dart';
import '../../core/widgets/app_button.dart';
import '../../core/widgets/app_card.dart';
import '../../core/widgets/app_chip.dart';
import '../../features/seller/data/sellers_repository.dart';

class ArtisanCard extends StatelessWidget {
  final SellerStorefront seller;
  final VoidCallback? onTap;
  final VoidCallback? onConnectRfq;

  const ArtisanCard({
    super.key,
    required this.seller,
    this.onTap,
    this.onConnectRfq,
  });

  String get _initials {
    final parts = seller.shopName.trim().split(RegExp(r'\s+')).where((p) => p.isNotEmpty).toList();
    if (parts.isEmpty) return '?';
    if (parts.length == 1) return parts.first[0].toUpperCase();
    return (parts.first[0] + parts.last[0]).toUpperCase();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final bio = (seller.bio ?? '').trim();
    final artisanType = (seller.artisanType ?? '').trim();
    final avatarUrl = seller.avatarUrl;

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
                clipBehavior: Clip.antiAlias,
                child: avatarUrl != null && avatarUrl.isNotEmpty
                    ? Image.network(
                        avatarUrl,
                        fit: BoxFit.cover,
                        errorBuilder: (_, __, ___) => _InitialsText(initials: _initials),
                      )
                    : _InitialsText(initials: _initials),
              ),
              AppSpacing.gapH12,
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      seller.shopName,
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    AppSpacing.gapV4,
                    Text(
                      '${seller.artisanName} · ${seller.regionLabel}',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.onSurface.withValues(alpha: 0.65),
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    if (seller.experienceYears != null && seller.experienceYears! > 0) ...[
                      AppSpacing.gapV4,
                      Text(
                        '${seller.experienceYears} yrs experience',
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),
          if (bio.isNotEmpty) ...[
            AppSpacing.gapV12,
            Text(
              bio,
              style: theme.textTheme.bodySmall?.copyWith(
                height: 1.4,
                color: theme.colorScheme.onSurface.withValues(alpha: 0.8),
              ),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ],
          AppSpacing.gapV12,
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Wrap(
                  spacing: 8,
                  runSpacing: 6,
                  children: [
                    if (artisanType.isNotEmpty)
                      AppChip(
                        label: artisanType.toUpperCase(),
                        variant: AppChipVariant.badge,
                        color: AppColors.handmade,
                        icon: const Icon(Icons.handshake_rounded, size: 12, color: Colors.white),
                      ),
                    if (seller.isVerified)
                      const AppChip(
                        label: 'VERIFIED',
                        variant: AppChipVariant.badge,
                        color: AppColors.giTag,
                        icon: Icon(Icons.verified_rounded, size: 12, color: Colors.white),
                      ),
                  ],
                ),
              ),
              if (onConnectRfq != null) ...[
                AppSpacing.gapH8,
                AppButton(
                  label: 'Request Quote',
                  variant: AppButtonVariant.outline,
                  height: 32,
                  isFullWidth: false,
                  onPressed: onConnectRfq,
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }
}

class _InitialsText extends StatelessWidget {
  final String initials;

  const _InitialsText({required this.initials});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: Text(
        initials,
        style: TextStyle(
          fontSize: 18,
          fontWeight: FontWeight.bold,
          color: theme.colorScheme.primary,
        ),
      ),
    );
  }
}
