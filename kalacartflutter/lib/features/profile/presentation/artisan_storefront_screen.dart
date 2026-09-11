import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/widgets/app_chip.dart';
import '../../../shared/widgets/craft_product_card.dart';
import '../../../shared/widgets/social_share_sheet.dart';
import '../../products/data/buyer_catalog_repository.dart';

// State provider for follow status
final artisanFollowProvider = StateNotifierProvider.family<ArtisanFollowNotifier, bool, String>((ref, artisanId) {
  return ArtisanFollowNotifier();
});

class ArtisanFollowNotifier extends StateNotifier<bool> {
  ArtisanFollowNotifier() : super(false);

  void toggle() {
    state = !state;
  }
}

class ArtisanStorefrontScreen extends ConsumerStatefulWidget {
  final String artisanId;

  const ArtisanStorefrontScreen({super.key, required this.artisanId});

  @override
  ConsumerState<ArtisanStorefrontScreen> createState() => _ArtisanStorefrontScreenState();
}

class _ArtisanStorefrontScreenState extends ConsumerState<ArtisanStorefrontScreen> {
  final List<String> _collections = ['All Creations', 'Royal Cobalt Glazes', 'Mughal Architectural Tiles', 'Masterpiece Keepsakes'];
  String _selectedCollection = 'All Creations';

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final isFollowing = ref.watch(artisanFollowProvider(widget.artisanId));
    final products = ref.watch(buyerCatalogProvider);

    const storeName = 'Dr. Kripal Kumbh Heritage Studio';
    const artisanName = 'Dr. Kripal Singh Shekhawat Master Guild';
    const cluster = 'Kot Jewar & Jaipur, Rajasthan';
    const bio = 'Pioneering Rajasthan\'s famed GI-certified Blue Pottery for over 45 years. Preserving ancient quartz and fuller earth formulation with pure cobalt and copper oxide natural glazes. Direct from Jaipur artisan kilns.';
    const followerCount = 3840;
    const storeSlug = 'kripal-kumbh-jaipur';

    return Scaffold(
      body: CustomScrollView(
        slivers: [
          // Full-Screen / Parallax Banner AppBar
          SliverAppBar(
            expandedHeight: 240,
            pinned: true,
            flexibleSpace: FlexibleSpaceBar(
              background: Stack(
                fit: StackFit.expand,
                children: [
                  Container(
                    decoration: const BoxDecoration(
                      gradient: LinearGradient(
                        colors: [Color(0xFF0D47A1), Color(0xFF1976D2), Color(0xFF00838F)],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                    ),
                    child: Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.palette_rounded, size: 64, color: Colors.white24),
                          AppSpacing.gapV8,
                          Text(
                            'JAIPUR BLUE POTTERY GUILD',
                            style: TextStyle(
                              color: Colors.white.withValues(alpha: 0.6),
                              letterSpacing: 2.0,
                              fontWeight: FontWeight.bold,
                              fontSize: 12,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),

                  // Gradient scrim
                  Positioned.fill(
                    child: Container(
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          colors: [
                            Colors.black.withValues(alpha: 0.5),
                            Colors.transparent,
                            Colors.black.withValues(alpha: 0.7),
                          ],
                          begin: Alignment.topCenter,
                          end: Alignment.bottomCenter,
                        ),
                      ),
                    ),
                  ),

                  // Live Workshop Indicator Badge
                  Positioned(
                    top: 80,
                    right: 16,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                      decoration: BoxDecoration(
                        color: Colors.red.shade700,
                        borderRadius: AppRadius.borderPill,
                        boxShadow: [
                          BoxShadow(color: Colors.red.withValues(alpha: 0.4), blurRadius: 8),
                        ],
                      ),
                      child: const Row(
                        children: [
                          Icon(Icons.sensors_rounded, color: Colors.white, size: 14),
                          SizedBox(width: 4),
                          Text('LIVE IN STUDIO', style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold)),
                        ],
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
                    title: storeName,
                    subtitle: 'GI Tagged Master Artisan Studio in Jaipur, Rajasthan',
                    deepLink: 'https://kalacart.in/store/$storeSlug',
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
                      // Avatar with Guild Border
                      Container(
                        padding: const EdgeInsets.all(3),
                        decoration: BoxDecoration(
                          color: AppColors.primary,
                          shape: BoxShape.circle,
                          boxShadow: [
                            BoxShadow(
                              color: AppColors.primary.withValues(alpha: 0.3),
                              blurRadius: 8,
                            ),
                          ],
                        ),
                        child: const CircleAvatar(
                          radius: 36,
                          backgroundColor: Colors.white,
                          child: Text(
                            '🏺',
                            style: TextStyle(fontSize: 32),
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
                                    storeName,
                                    style: theme.textTheme.titleMedium?.copyWith(
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 4),
                                const Icon(Icons.verified, color: AppColors.success, size: 18),
                              ],
                            ),
                            AppSpacing.gapV4,
                            Text(
                              artisanName,
                              style: theme.textTheme.bodySmall?.copyWith(fontWeight: FontWeight.w600),
                            ),
                            AppSpacing.gapV2,
                            Row(
                              children: [
                                const Icon(Icons.location_on_outlined, size: 13, color: AppColors.primary),
                                const SizedBox(width: 2),
                                Text(
                                  cluster,
                                  style: theme.textTheme.bodySmall?.copyWith(
                                    color: isDark ? AppColors.textTertiaryDark : AppColors.textSecondaryLight,
                                    fontSize: 11,
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

                  // Guild Badges
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: const BoxDecoration(
                          color: AppColors.successContainer,
                          borderRadius: AppRadius.borderSm,
                        ),
                        child: const Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.verified_user_outlined, size: 12, color: AppColors.success),
                            SizedBox(width: 4),
                            Text('GI Tag Registered #04', style: TextStyle(color: AppColors.success, fontSize: 10, fontWeight: FontWeight.bold)),
                          ],
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: const BoxDecoration(
                          color: AppColors.secondaryContainer,
                          borderRadius: AppRadius.borderSm,
                        ),
                        child: const Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.military_tech_outlined, size: 12, color: AppColors.secondary),
                            SizedBox(width: 4),
                            Text('National Shilp Guru Awardee', style: TextStyle(color: AppColors.onSecondaryContainer, fontSize: 10, fontWeight: FontWeight.bold)),
                          ],
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: const BoxDecoration(
                          color: AppColors.primaryContainer,
                          borderRadius: AppRadius.borderSm,
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Icon(Icons.people_alt_outlined, size: 12, color: AppColors.primary),
                            const SizedBox(width: 4),
                            Text('${followerCount + (isFollowing ? 1 : 0)} Followers', style: const TextStyle(color: AppColors.primary, fontSize: 10, fontWeight: FontWeight.bold)),
                          ],
                        ),
                      ),
                    ],
                  ),
                  AppSpacing.gapV12,

                  // Bio Description
                  Text(
                    bio,
                    style: theme.textTheme.bodyMedium?.copyWith(
                      height: 1.4,
                      color: isDark ? AppColors.textSecondaryDark : AppColors.textSecondaryLight,
                    ),
                  ),
                  AppSpacing.gapV16,

                  // Action Buttons: Follow, Chat, Custom RFQ
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton.icon(
                          style: OutlinedButton.styleFrom(
                            foregroundColor: isFollowing ? Colors.grey : AppColors.primary,
                            side: BorderSide(
                              color: isFollowing ? Colors.grey : AppColors.primary,
                              width: 1.4,
                            ),
                            shape: AppRadius.shapeMd,
                            padding: const EdgeInsets.symmetric(vertical: 12),
                          ),
                          icon: Icon(isFollowing ? Icons.check : Icons.person_add_alt_1),
                          label: Text(
                            isFollowing ? 'Following' : 'Follow Studio',
                            style: const TextStyle(fontWeight: FontWeight.bold),
                          ),
                          onPressed: () {
                            ref.read(artisanFollowProvider(widget.artisanId).notifier).toggle();
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(
                                content: Text(isFollowing ? 'Unfollowed $storeName' : 'Now following $storeName! You will receive new craft drops and live alerts.'),
                                duration: const Duration(seconds: 2),
                              ),
                            );
                          },
                        ),
                      ),
                      AppSpacing.gapH8,
                      IconButton.filledTonal(
                        icon: const Icon(Icons.chat_outlined),
                        tooltip: 'Message Artisan Guild',
                        onPressed: () {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text('Direct Artisan Chat channel opened. Audio & text translations enabled!')),
                          );
                        },
                      ),
                      AppSpacing.gapH8,
                      ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.primary,
                          foregroundColor: Colors.white,
                          shape: AppRadius.shapeMd,
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                        ),
                        icon: const Icon(Icons.handshake_outlined, size: 18),
                        label: const Text('Request RFQ', style: TextStyle(fontWeight: FontWeight.bold)),
                        onPressed: () => context.push('/rfq'),
                      ),
                    ],
                  ),
                  AppSpacing.gapV24,

                  // Collections Selector
                  Text('Artisan Collections', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
                  AppSpacing.gapV8,
                  SizedBox(
                    height: 38,
                    child: ListView.separated(
                      scrollDirection: Axis.horizontal,
                      itemCount: _collections.length,
                      separatorBuilder: (_, __) => AppSpacing.gapH8,
                      itemBuilder: (context, index) {
                        final col = _collections[index];
                        return AppChip(
                          label: col,
                          isSelected: _selectedCollection == col,
                          onSelected: (_) {
                            setState(() {
                              _selectedCollection = col;
                            });
                          },
                        );
                      },
                    ),
                  ),
                  AppSpacing.gapV16,

                  // Products Grid Header
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text('Craft Showcase (${products.length})', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                      const Text('100% Authentic GI', style: TextStyle(fontSize: 11, color: AppColors.success, fontWeight: FontWeight.bold)),
                    ],
                  ),
                ],
              ),
            ),
          ),

          // Products Grid
          SliverPadding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            sliver: SliverGrid(
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2,
                crossAxisSpacing: 12,
                mainAxisSpacing: 12,
                childAspectRatio: 0.74,
              ),
              delegate: SliverChildBuilderDelegate(
                (context, index) {
                  final product = products[index % products.length];
                  return CraftProductCard(
                    product: product.toCraftProduct(),
                    onTap: () => context.push('/products/${product.id}'),
                  );
                },
                childCount: products.length,
              ),
            ),
          ),

          const SliverToBoxAdapter(
            child: SizedBox(height: 48),
          ),
        ],
      ),
    );
  }
}
