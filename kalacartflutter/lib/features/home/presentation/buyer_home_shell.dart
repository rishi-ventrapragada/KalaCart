import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_constants.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/widgets/app_chip.dart';
import '../../../core/widgets/app_search_bar.dart';
import '../../../core/widgets/app_top_bar.dart';
import '../../../shared/models/artisan_model.dart';
import '../../../shared/widgets/artisan_cards.dart';
import '../../../shared/widgets/craft_product_card.dart';
import '../../ai/presentation/widgets/voice_mic_floating_button.dart';
import 'home_providers.dart';

final mockArtisansProvider = Provider<List<ArtisanProfile>>((ref) {
  return const [
    ArtisanProfile(
      id: 'art-001',
      name: 'Mohd. Rafiq Ansari',
      craftSpecialty: 'Master Weaver, Banarasi Brocade',
      clusterRegion: 'Varanasi',
      state: 'Uttar Pradesh',
      yearsOfExperience: 32,
      rating: 4.95,
      reviewCount: 240,
      isGiCertified: true,
      isNationalAwardee: true,
      storySnippet: '5th-generation master weaver preserving 400-year-old Kadwa silk brocade weaving techniques.',
      productCount: 48,
    ),
    ArtisanProfile(
      id: 'art-002',
      name: 'Dr. Kripal Kumbh Studio',
      craftSpecialty: 'Blue Pottery & Ceramic Art',
      clusterRegion: 'Jaipur',
      state: 'Rajasthan',
      yearsOfExperience: 28,
      rating: 4.9,
      reviewCount: 180,
      isGiCertified: true,
      isNationalAwardee: true,
      storySnippet: 'Pioneering traditional quartz and fuller earth pottery with cobalt oxide natural mineral glazes.',
      productCount: 35,
    ),
    ArtisanProfile(
      id: 'art-003',
      name: 'Bastar Bell Metal Guild',
      craftSpecialty: 'Lost-Wax Dhokra Castings',
      clusterRegion: 'Kondagaon',
      state: 'Chhattisgarh',
      yearsOfExperience: 24,
      rating: 4.85,
      reviewCount: 95,
      isGiCertified: true,
      isNationalAwardee: false,
      storySnippet: 'Crafting 4,000-year-old Indus Valley non-ferrous lost-wax metal tribal figurines.',
      productCount: 20,
    ),
  ];
});

class BuyerHomeShell extends ConsumerWidget {
  const BuyerHomeShell({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final selectedCategory = ref.watch(selectedCategoryProvider);
    final products = ref.watch(mockProductsProvider);
    final artisans = ref.watch(mockArtisansProvider);

    final filteredProducts = selectedCategory == 'All Crafts'
        ? products
        : products.where((p) => p.category == selectedCategory).toList();

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
                  'Hyperlocal Indian Handicrafts & GI Clusters',
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
            icon: const Icon(Icons.notifications_none_rounded),
            tooltip: 'Notifications',
            onPressed: () => context.push('/notifications'),
          ),
        ],
      ),
      body: ListView(
        padding: AppSpacing.paddingAllBase,
        children: [
          // Search & Filter
          AppSearchBar(
            onTap: () => context.push('/discovery'),
            onFilterTap: () => context.push('/discovery'),
            onVoiceTap: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('AI Voice Assistant listening (Hindi, Telugu, Bengali, Tamil, English)...'),
                  behavior: SnackBarBehavior.floating,
                ),
              );
            },
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
                          Icon(Icons.verified_rounded, size: 12, color: Colors.white),
                          SizedBox(width: 4),
                          Text(
                            '100% VERIFIED GI & HANDMADE',
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
                  'Post custom B2B RFQs, trace digital provenance passports, and purchase authentic crafts without middlemen.',
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
                        onPressed: () => context.push('/rfq'),
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
                        child: const Text('Craft Clusters'),
                        onPressed: () => context.push('/discovery'),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          AppSpacing.gapV24,

          // Regional Cluster Banner
          ArtisanClusterHeader(
            title: 'Jaipur Blue Pottery Cluster',
            region: 'Rajasthan',
            artisanCount: 142,
            onExplore: () => context.push('/discovery'),
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
                '${AppConstants.craftCategories.length} Categories',
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
                    ref.read(selectedCategoryProvider.notifier).state = cat;
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
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Featured Handicrafts',
                    style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
                  ),
                  Text(
                    'Handmade by verified master craftspeople',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: isDark ? AppColors.textTertiaryDark : AppColors.textSecondaryLight,
                    ),
                  ),
                ],
              ),
              TextButton(
                onPressed: () => context.push('/discovery'),
                child: const Text('View All'),
              ),
            ],
          ),
          AppSpacing.gapV12,

          GridView.builder(
            physics: const NeverScrollableScrollPhysics(),
            shrinkWrap: true,
            itemCount: filteredProducts.length,
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              crossAxisSpacing: 12,
              mainAxisSpacing: 12,
              childAspectRatio: 0.74,
            ),
            itemBuilder: (context, index) {
              final product = filteredProducts[index];
              return CraftProductCard(
                product: product,
                onTap: () => context.push('/products/${product.id}'),
              );
            },
          ),
          AppSpacing.gapV24,

          // Master Artisans Section
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Master Artisans & Guilds',
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
            ],
          ),
          AppSpacing.gapV12,

          ListView.separated(
            physics: const NeverScrollableScrollPhysics(),
            shrinkWrap: true,
            itemCount: artisans.length,
            separatorBuilder: (_, __) => AppSpacing.gapV12,
            itemBuilder: (context, index) {
              final artisan = artisans[index];
              return ArtisanCard(
                artisan: artisan,
                onTap: () => context.push('/profile'),
                onConnectRfq: () => context.push('/rfq'),
              );
            },
          ),
          AppSpacing.gapV32,
        ],
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
