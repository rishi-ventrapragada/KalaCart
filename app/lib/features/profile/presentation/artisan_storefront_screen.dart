import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/widgets/app_chip.dart';
import '../../../core/widgets/app_empty_state.dart';
import '../../../core/widgets/app_error_state.dart';
import '../../../core/widgets/app_loading_state.dart';
import '../../../core/widgets/app_skeleton.dart';
import '../../../shared/widgets/craft_product_card.dart';
import '../../../shared/widgets/social_share_sheet.dart';
import '../../products/data/supabase_products_repository.dart';
import '../../seller/data/sellers_repository.dart';

/// Local follow toggle (not persisted).
final artisanFollowProvider = StateProvider.family<bool, String>((ref, artisanId) => false);

class ArtisanStorefrontScreen extends ConsumerStatefulWidget {
  final String artisanId;

  const ArtisanStorefrontScreen({super.key, required this.artisanId});

  @override
  ConsumerState<ArtisanStorefrontScreen> createState() => _ArtisanStorefrontScreenState();
}

class _ArtisanStorefrontScreenState extends ConsumerState<ArtisanStorefrontScreen> {
  @override
  Widget build(BuildContext context) {
    final sellerAsync = ref.watch(sellerStorefrontProvider(widget.artisanId));

    return sellerAsync.when(
      loading: () => Scaffold(
        appBar: AppBar(),
        body: const AppLoadingState(message: 'Opening studio...'),
      ),
      error: (e, _) => Scaffold(
        appBar: AppBar(),
        body: AppErrorState(
          message: 'Unable to load this artisan studio right now.',
          onRetry: () => ref.invalidate(sellerStorefrontProvider(widget.artisanId)),
        ),
      ),
      data: (seller) {
        if (seller == null) {
          return Scaffold(
            appBar: AppBar(),
            body: AppErrorState(
              title: 'Studio not found',
              message: 'This artisan storefront does not exist or is no longer available.',
              retryLabel: 'Back to Discovery',
              onRetry: () => context.go('/discovery'),
            ),
          );
        }
        return _buildStorefront(context, seller);
      },
    );
  }

  Widget _buildStorefront(BuildContext context, SellerStorefront seller) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final isFollowing = ref.watch(artisanFollowProvider(widget.artisanId));
    final productsAsync = ref.watch(sellerPublishedProductsProvider(widget.artisanId));
    final bio = (seller.bio ?? '').trim();
    final artisanType = (seller.artisanType ?? '').trim();
    final avatarUrl = seller.avatarUrl;

    return Scaffold(
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(sellerStorefrontProvider(widget.artisanId));
          ref.invalidate(sellerPublishedProductsProvider(widget.artisanId));
          try {
            await ref.read(sellerPublishedProductsProvider(widget.artisanId).future);
          } catch (_) {
            // Rendered by the error state below.
          }
        },
        child: CustomScrollView(
          slivers: [
            SliverAppBar(
              expandedHeight: 200,
              pinned: true,
              flexibleSpace: FlexibleSpaceBar(
                background: Stack(
                  fit: StackFit.expand,
                  children: [
                    Container(
                      decoration: const BoxDecoration(
                        gradient: LinearGradient(
                          colors: [AppColors.secondaryDark, AppColors.secondary, AppColors.secondaryLight],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ),
                      ),
                      child: Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Icon(Icons.palette_rounded, size: 64, color: Colors.white24),
                            if (artisanType.isNotEmpty) ...[
                              AppSpacing.gapV8,
                              Text(
                                artisanType.toUpperCase(),
                                style: TextStyle(
                                  color: Colors.white.withValues(alpha: 0.6),
                                  letterSpacing: 2.0,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 12,
                                ),
                              ),
                            ],
                          ],
                        ),
                      ),
                    ),
                    Positioned.fill(
                      child: Container(
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            colors: [
                              Colors.black.withValues(alpha: 0.5),
                              Colors.transparent,
                              Colors.black.withValues(alpha: 0.6),
                            ],
                            begin: Alignment.topCenter,
                            end: Alignment.bottomCenter,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              actions: [
                IconButton(
                  icon: const Icon(Icons.share_outlined),
                  tooltip: 'Share Storefront',
                  onPressed: () {
                    SocialShareSheet.show(
                      context,
                      title: seller.shopName,
                      subtitle: '${seller.artisanName} · ${seller.regionLabel}',
                      deepLink: 'https://kalacart.in/artisan/${seller.id}',
                      entityType: 'store',
                    );
                  },
                ),
              ],
            ),

            // Header Information
            SliverToBoxAdapter(
              child: Padding(
                padding: AppSpacing.paddingAllBase,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          padding: const EdgeInsets.all(3),
                          decoration: BoxDecoration(
                            color: AppColors.primary,
                            shape: BoxShape.circle,
                            boxShadow: [
                              BoxShadow(color: AppColors.primary.withValues(alpha: 0.3), blurRadius: 8),
                            ],
                          ),
                          child: CircleAvatar(
                            radius: 36,
                            backgroundColor: Colors.white,
                            foregroundImage: avatarUrl != null && avatarUrl.isNotEmpty ? NetworkImage(avatarUrl) : null,
                            onForegroundImageError: avatarUrl != null && avatarUrl.isNotEmpty ? (_, __) {} : null,
                            child: Text(
                              _initials(seller.shopName),
                              style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: AppColors.primary),
                            ),
                          ),
                        ),
                        AppSpacing.gapH16,
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Flexible(
                                    child: Text(
                                      seller.shopName,
                                      style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                                    ),
                                  ),
                                  if (seller.isVerified) ...[
                                    const SizedBox(width: 4),
                                    const Icon(Icons.verified, color: AppColors.success, size: 18),
                                  ],
                                ],
                              ),
                              AppSpacing.gapV4,
                              Text(
                                seller.artisanName,
                                style: theme.textTheme.bodySmall?.copyWith(fontWeight: FontWeight.w600),
                              ),
                              AppSpacing.gapV2,
                              Row(
                                children: [
                                  const Icon(Icons.location_on_outlined, size: 13, color: AppColors.primary),
                                  const SizedBox(width: 2),
                                  Expanded(
                                    child: Text(
                                      seller.regionLabel,
                                      style: theme.textTheme.bodySmall?.copyWith(
                                        color: isDark ? AppColors.textTertiaryDark : AppColors.textSecondaryLight,
                                        fontSize: 11,
                                      ),
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    AppSpacing.gapV16,

                    // Badges from real fields only
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        if (seller.isVerified)
                          const AppChip(
                            label: 'VERIFIED ARTISAN',
                            variant: AppChipVariant.badge,
                            color: AppColors.giTag,
                            icon: Icon(Icons.verified_user_outlined, size: 12, color: Colors.white),
                          ),
                        if (artisanType.isNotEmpty)
                          AppChip(
                            label: artisanType.toUpperCase(),
                            variant: AppChipVariant.badge,
                            color: AppColors.handmade,
                            icon: const Icon(Icons.handshake_rounded, size: 12, color: Colors.white),
                          ),
                        if (seller.experienceYears != null && seller.experienceYears! > 0)
                          AppChip(
                            label: '${seller.experienceYears} YRS EXPERIENCE',
                            variant: AppChipVariant.badge,
                            color: AppColors.secondary,
                            icon: const Icon(Icons.history_edu_outlined, size: 12, color: Colors.white),
                          ),
                      ],
                    ),
                    if (bio.isNotEmpty) ...[
                      AppSpacing.gapV12,
                      Text(
                        bio,
                        style: theme.textTheme.bodyMedium?.copyWith(
                          height: 1.4,
                          color: isDark ? AppColors.textSecondaryDark : AppColors.textSecondaryLight,
                        ),
                      ),
                    ],
                    AppSpacing.gapV16,

                    // Action Buttons
                    Row(
                      children: [
                        Expanded(
                          child: OutlinedButton.icon(
                            style: OutlinedButton.styleFrom(
                              foregroundColor: isFollowing ? Colors.grey : AppColors.primary,
                              side: BorderSide(color: isFollowing ? Colors.grey : AppColors.primary, width: 1.4),
                              shape: AppRadius.shapeMd,
                              padding: const EdgeInsets.symmetric(vertical: 12),
                            ),
                            icon: Icon(isFollowing ? Icons.check : Icons.person_add_alt_1),
                            label: Text(
                              isFollowing ? 'Following' : 'Follow Studio',
                              style: const TextStyle(fontWeight: FontWeight.bold),
                            ),
                            onPressed: () {
                              final next = !isFollowing;
                              ref.read(artisanFollowProvider(widget.artisanId).notifier).state = next;
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                  content: Text(next ? 'Now following ${seller.shopName}.' : 'Unfollowed ${seller.shopName}.'),
                                  behavior: SnackBarBehavior.floating,
                                  duration: const Duration(seconds: 2),
                                ),
                              );
                            },
                          ),
                        ),
                        AppSpacing.gapH8,
                        Expanded(
                          child: ElevatedButton.icon(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppColors.primary,
                              foregroundColor: Colors.white,
                              shape: AppRadius.shapeMd,
                              padding: const EdgeInsets.symmetric(vertical: 12),
                            ),
                            icon: const Icon(Icons.handshake_outlined, size: 18),
                            label: const Text('Request Quote', style: TextStyle(fontWeight: FontWeight.bold)),
                            onPressed: () => context.push('/rfq/create'),
                          ),
                        ),
                      ],
                    ),
                    AppSpacing.gapV24,

                    // Products Grid Header
                    productsAsync.maybeWhen(
                      data: (products) => Text(
                        'Craft Showcase (${products.length})',
                        style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                      ),
                      orElse: () => Text(
                        'Craft Showcase',
                        style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                      ),
                    ),
                  ],
                ),
              ),
            ),

            // Products Grid
            productsAsync.when(
              loading: () => SliverPadding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                sliver: SliverGrid(
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 2,
                    crossAxisSpacing: 12,
                    mainAxisSpacing: 12,
                    childAspectRatio: 0.7,
                  ),
                  delegate: SliverChildBuilderDelegate(
                    (_, __) => const ProductCardSkeleton(),
                    childCount: 4,
                  ),
                ),
              ),
              error: (e, _) => SliverToBoxAdapter(
                child: AppErrorState(
                  message: 'Unable to load this studio\'s crafts.',
                  onRetry: () => ref.invalidate(sellerPublishedProductsProvider(widget.artisanId)),
                ),
              ),
              data: (products) {
                if (products.isEmpty) {
                  return const SliverToBoxAdapter(
                    child: AppEmptyState(
                      icon: Icons.inventory_2_outlined,
                      title: 'No crafts listed yet',
                      message: 'This studio has not published any products. Request a quote to commission a piece.',
                    ),
                  );
                }
                return SliverPadding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  sliver: SliverGrid(
                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2,
                      crossAxisSpacing: 12,
                      mainAxisSpacing: 12,
                      childAspectRatio: 0.7,
                    ),
                    delegate: SliverChildBuilderDelegate(
                      (context, index) {
                        final product = products[index];
                        return CraftProductCard(
                          product: product,
                          onTap: () => context.push('/products/${product.id}'),
                        );
                      },
                      childCount: products.length,
                    ),
                  ),
                );
              },
            ),

            const SliverToBoxAdapter(child: SizedBox(height: 48)),
          ],
        ),
      ),
    );
  }

  static String _initials(String name) {
    final parts = name.trim().split(RegExp(r'\s+')).where((p) => p.isNotEmpty).toList();
    if (parts.isEmpty) return '?';
    if (parts.length == 1) return parts.first[0].toUpperCase();
    return (parts.first[0] + parts.last[0]).toUpperCase();
  }
}
