import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_constants.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/widgets/app_chip.dart';
import '../../../core/widgets/app_empty_state.dart';
import '../../../core/widgets/app_error_state.dart';
import '../../../core/widgets/app_search_bar.dart';
import '../../../core/widgets/app_skeleton.dart';
import '../../../shared/widgets/artisan_cards.dart';
import '../../../shared/widgets/craft_product_card.dart';
import '../../ai/presentation/widgets/voice_mic_floating_button.dart';
import '../../products/data/cart_provider.dart';
import '../../products/data/supabase_products_repository.dart';
import '../../seller/data/sellers_repository.dart';

/// Category chip selected on the home screen.
final homeSelectedCategoryProvider = StateProvider<String>((ref) => AppConstants.craftCategories.first);

class BuyerHomeShell extends ConsumerWidget {
  const BuyerHomeShell({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final selectedCategory = ref.watch(homeSelectedCategoryProvider);
    final productsAsync = ref.watch(publishedProductsProvider);
    final sellersAsync = ref.watch(featuredSellersProvider);
    final cartCount = ref.watch(cartItemCountProvider);

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(7),
              decoration: const BoxDecoration(
                color: AppColors.primary,
                borderRadius: AppRadius.borderSm,
              ),
              child: const Icon(
                Icons.handshake_outlined,
                color: Colors.white,
                size: 20,
              ),
            ),
            AppSpacing.gapH12,
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(
                      AppConstants.appName,
                      style: theme.textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.w800,
                        letterSpacing: -0.2,
                      ),
                    ),
                    AppSpacing.gapH8,
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: const BoxDecoration(
                        color: AppColors.primaryContainer,
                        borderRadius: AppRadius.borderXs,
                      ),
                      child: const Text(
                        'BUYER MODE',
                        style: TextStyle(
                          color: AppColors.onPrimaryContainer,
                          fontSize: 9,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ),
                Text(
                  'Handmade crafts direct from Indian artisans',
                  style: theme.textTheme.bodySmall?.copyWith(
                    fontSize: 11,
                    color: isDark ? AppColors.textTertiaryDark : AppColors.textSecondaryLight,
                  ),
                ),
              ],
            ),
          ],
        ),
        actions: [
          IconButton(
            tooltip: 'Cart',
            onPressed: () => context.push('/cart'),
            icon: Badge(
              isLabelVisible: cartCount > 0,
              label: Text('$cartCount'),
              child: const Icon(Icons.shopping_cart_outlined),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.notifications_none_rounded),
            tooltip: 'Notifications',
            onPressed: () => context.push('/notifications'),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(publishedProductsProvider);
          ref.invalidate(featuredSellersProvider);
          try {
            await Future.wait([
              ref.read(publishedProductsProvider.future),
              ref.read(featuredSellersProvider.future),
            ]);
          } catch (_) {
            // The error states below render the failure.
          }
        },
        child: ListView(
          padding: AppSpacing.paddingAllBase,
          children: [
            // Search & Filter
            AppSearchBar(
              readOnly: true,
              onTap: () => context.push('/discovery'),
              onFilterTap: () => context.push('/discovery'),
            ),
            AppSpacing.gapV20,

            // Heritage Hero Banner
            Container(
              padding: AppSpacing.paddingAllLg,
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [AppColors.primary, Color(0xFFD4623B)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: AppRadius.borderLg,
                boxShadow: [
                  BoxShadow(
                    color: AppColors.primary.withValues(alpha: 0.3),
                    blurRadius: 16,
                    offset: const Offset(0, 6),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: 0.22),
                          borderRadius: AppRadius.borderSm,
                        ),
                        child: const Row(
                          children: [
                            Icon(Icons.handshake_rounded, size: 12, color: Colors.white),
                            SizedBox(width: 4),
                            Text(
                              'DIRECT FROM ARTISANS',
                              style: TextStyle(
                                color: Colors.white,
                                fontSize: 10,
                                fontWeight: FontWeight.bold,
                                letterSpacing: 0.6,
                              ),
                            ),
                          ],
                        ),
                      ),
                      const Icon(Icons.palette_outlined, color: Colors.white70, size: 20),
                    ],
                  ),
                  AppSpacing.gapV12,
                  const Text(
                    'Empower Indian Artisans.\nSource Direct Heritage Crafts.',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      height: 1.25,
                    ),
                  ),
                  AppSpacing.gapV8,
                  Text(
                    'Post custom B2B RFQs, trace craft provenance passports, and purchase authentic crafts without middlemen.',
                    style: TextStyle(
                      color: Colors.white.withValues(alpha: 0.9),
                      fontSize: 13,
                      height: 1.4,
                    ),
                  ),
                  AppSpacing.gapV16,
                  Row(
                    children: [
                      SizedBox(
                        height: 36,
                        child: ElevatedButton.icon(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.white,
                            foregroundColor: AppColors.primary,
                            elevation: 0,
                            shape: AppRadius.shapeMd,
                            padding: const EdgeInsets.symmetric(horizontal: 14),
                          ),
                          icon: const Icon(Icons.post_add_rounded, size: 16),
                          label: const Text('Post Custom RFQ', style: TextStyle(fontWeight: FontWeight.bold)),
                          onPressed: () => context.push('/rfq/create'),
                        ),
                      ),
                      AppSpacing.gapH12,
                      SizedBox(
                        height: 36,
                        child: OutlinedButton(
                          style: OutlinedButton.styleFrom(
                            foregroundColor: Colors.white,
                            side: const BorderSide(color: Colors.white, width: 1.2),
                            shape: AppRadius.shapeMd,
                          ),
                          child: const Text('Discover'),
                          onPressed: () => context.push('/discovery'),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            AppSpacing.gapV24,

            // Category Chips
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Explore Craft Traditions',
                  style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
                ),
                Text(
                  '${AppConstants.craftCategories.length - 1} Categories',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: isDark ? AppColors.textTertiaryDark : AppColors.textSecondaryLight,
                  ),
                ),
              ],
            ),
            AppSpacing.gapV12,
            SizedBox(
              height: 38,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                itemCount: AppConstants.craftCategories.length,
                separatorBuilder: (_, __) => AppSpacing.gapH8,
                itemBuilder: (context, index) {
                  final cat = AppConstants.craftCategories[index];
                  return AppChip(
                    label: cat,
                    isSelected: cat == selectedCategory,
                    onSelected: (_) {
                      ref.read(homeSelectedCategoryProvider.notifier).state = cat;
                    },
                  );
                },
              ),
            ),
            AppSpacing.gapV24,

            // Featured Products Section
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Featured Handicrafts',
                        style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
                      ),
                      Text(
                        'Handmade by artisans on KalaCart',
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: isDark ? AppColors.textTertiaryDark : AppColors.textSecondaryLight,
                        ),
                      ),
                    ],
                  ),
                ),
                TextButton(
                  onPressed: () => context.push('/discovery'),
                  child: const Text('View All'),
                ),
              ],
            ),
            AppSpacing.gapV12,

            productsAsync.when(
              loading: () => const _ProductSkeletonGrid(),
              error: (e, _) => AppErrorState(
                message: 'Unable to load crafts right now.',
                onRetry: () => ref.invalidate(publishedProductsProvider),
              ),
              data: (products) {
                final filtered = selectedCategory == AppConstants.craftCategories.first
                    ? products
                    : products.where((p) => p.category == selectedCategory).toList();
                if (filtered.isEmpty) {
                  return AppEmptyState(
                    icon: Icons.palette_outlined,
                    title: 'No crafts listed yet',
                    message: selectedCategory == AppConstants.craftCategories.first
                        ? 'Artisans have not published any products yet. Check back soon.'
                        : 'No published crafts in "$selectedCategory" yet.',
                    actionLabel: selectedCategory == AppConstants.craftCategories.first ? null : 'Show all crafts',
                    onAction: selectedCategory == AppConstants.craftCategories.first
                        ? null
                        : () => ref.read(homeSelectedCategoryProvider.notifier).state =
                            AppConstants.craftCategories.first,
                  );
                }
                return GridView.builder(
                  physics: const NeverScrollableScrollPhysics(),
                  shrinkWrap: true,
                  itemCount: filtered.length,
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 2,
                    crossAxisSpacing: 12,
                    mainAxisSpacing: 12,
                    childAspectRatio: 0.7,
                  ),
                  itemBuilder: (context, index) {
                    final product = filtered[index];
                    return CraftProductCard(
                      product: product,
                      onTap: () => context.push('/products/${product.id}'),
                    );
                  },
                );
              },
            ),
            AppSpacing.gapV24,

            // Artisans Section
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Artisans & Studios',
                  style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
                ),
                Text(
                  'Direct contact for wholesale & bespoke orders',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: isDark ? AppColors.textTertiaryDark : AppColors.textSecondaryLight,
                  ),
                ),
              ],
            ),
            AppSpacing.gapV12,

            sellersAsync.when(
              loading: () => Column(
                children: List.generate(
                  2,
                  (_) => const Padding(
                    padding: EdgeInsets.only(bottom: 12),
                    child: AppSkeleton(height: 140, borderRadius: AppRadius.borderMd),
                  ),
                ),
              ),
              error: (e, _) => AppErrorState(
                message: 'Unable to load artisans right now.',
                onRetry: () => ref.invalidate(featuredSellersProvider),
              ),
              data: (sellers) {
                if (sellers.isEmpty) {
                  return const AppEmptyState(
                    icon: Icons.storefront_outlined,
                    title: 'No artisan studios yet',
                    message: 'Artisan storefronts will appear here once they onboard.',
                  );
                }
                return ListView.separated(
                  physics: const NeverScrollableScrollPhysics(),
                  shrinkWrap: true,
                  itemCount: sellers.length,
                  separatorBuilder: (_, __) => AppSpacing.gapV12,
                  itemBuilder: (context, index) {
                    final seller = sellers[index];
                    return ArtisanCard(
                      seller: seller,
                      onTap: () => context.push('/artisan/${seller.id}'),
                      onConnectRfq: () => context.push('/rfq/create'),
                    );
                  },
                );
              },
            ),
            AppSpacing.gapV32,
          ],
        ),
      ),
      floatingActionButton: VoiceMicFloatingButton(
        isArtisanMode: false,
        onIntentExtracted: (result) {
          if (result.intentType == 'rfq_inquiry') {
            context.push('/rfq/create');
          }
        },
      ),
    );
  }
}

class _ProductSkeletonGrid extends StatelessWidget {
  const _ProductSkeletonGrid();

  @override
  Widget build(BuildContext context) {
    return GridView.builder(
      physics: const NeverScrollableScrollPhysics(),
      shrinkWrap: true,
      itemCount: 4,
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
        childAspectRatio: 0.7,
      ),
      itemBuilder: (_, __) => const ProductCardSkeleton(),
    );
  }
}
