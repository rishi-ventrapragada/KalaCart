import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_constants.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/utils/responsive.dart';
import '../../../shared/models/craft_product.dart';
import '../../../shared/widgets/craft_product_card.dart';
import 'home_providers.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final themeMode = ref.watch(themeModeProvider);
    final selectedCategory = ref.watch(selectedCategoryProvider);
    final products = ref.watch(mockProductsProvider);

    final filteredProducts = selectedCategory == 'All Crafts'
        ? products
        : products.where((p) => p.category == selectedCategory).toList();

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(6),
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
            AppSpacing.gapH8,
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  AppConstants.appName,
                  style: theme.textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(
                  'Hyperlocal Artisan Commerce',
                  style: theme.textTheme.bodySmall?.copyWith(
                    fontSize: 10,
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                  ),
                ),
              ],
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: Icon(
              themeMode == ThemeMode.dark
                  ? Icons.light_mode_outlined
                  : Icons.dark_mode_outlined,
            ),
            tooltip: 'Toggle Theme',
            onPressed: () {
              ref.read(themeModeProvider.notifier).state =
                  themeMode == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark;
            },
          ),
          IconButton(
            icon: const Icon(Icons.notifications_none_rounded),
            onPressed: () => context.push('/notifications'),
          ),
        ],
      ),
      body: SingleCardsBody(
        selectedCategory: selectedCategory,
        filteredProducts: filteredProducts,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: 0,
        onDestinationSelected: (index) {
          switch (index) {
            case 0:
              break;
            case 1:
              context.push('/discovery');
              break;
            case 2:
              context.push('/catalog-studio');
              break;
            case 3:
              context.push('/rfq');
              break;
            case 4:
              context.push('/profile');
              break;
          }
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.home_outlined),
            selectedIcon: Icon(Icons.home_rounded),
            label: 'Home',
          ),
          NavigationDestination(
            icon: Icon(Icons.explore_outlined),
            selectedIcon: Icon(Icons.explore_rounded),
            label: 'Discover',
          ),
          NavigationDestination(
            icon: Icon(Icons.auto_awesome_outlined),
            selectedIcon: Icon(Icons.auto_awesome_rounded),
            label: 'Studio AI',
          ),
          NavigationDestination(
            icon: Icon(Icons.handshake_outlined),
            selectedIcon: Icon(Icons.handshake_rounded),
            label: 'RFQ / B2B',
          ),
          NavigationDestination(
            icon: Icon(Icons.person_outline_rounded),
            selectedIcon: Icon(Icons.person_rounded),
            label: 'Profile',
          ),
        ],
      ),
    );
  }
}

class SingleCardsBody extends ConsumerWidget {
  final String selectedCategory;
  final List<CraftProduct> filteredProducts;

  const SingleCardsBody({
    super.key,
    required this.selectedCategory,
    required this.filteredProducts,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final isMobile = ResponsiveLayout.isMobile(context);

    return ListView(
      padding: AppSpacing.paddingAllBase,
      children: [
        // Artisan Hero Banner
        Container(
          padding: AppSpacing.paddingAllLg,
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [
                AppColors.primary,
                AppColors.primaryLight,
              ],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: AppRadius.borderLg,
            boxShadow: [
              BoxShadow(
                color: AppColors.primary.withValues(alpha: 0.25),
                blurRadius: 12,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.2),
                      borderRadius: AppRadius.borderSm,
                    ),
                    child: const Text(
                      'AI-POWERED PLATFORM',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 0.8,
                      ),
                    ),
                  ),
                ],
              ),
              AppSpacing.gapV12,
              Text(
                'Direct from India\'s Master Artisans',
                style: theme.textTheme.headlineMedium?.copyWith(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                ),
              ),
              AppSpacing.gapV8,
              Text(
                'Explore verified GI-tagged handicrafts, connect via custom RFQs, and support heritage crafts.',
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: Colors.white.withValues(alpha: 0.9),
                ),
              ),
            ],
          ),
        ),

        AppSpacing.gapV24,

        // Categories Horizontal Bar
        Text('Explore Craft Traditions', style: theme.textTheme.titleMedium),
        AppSpacing.gapV12,
        SizedBox(
          height: 38,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            itemCount: AppConstants.craftCategories.length,
            separatorBuilder: (_, __) => AppSpacing.gapH8,
            itemBuilder: (context, index) {
              final cat = AppConstants.craftCategories[index];
              final isSelected = cat == selectedCategory;
              return FilterChip(
                label: Text(cat),
                selected: isSelected,
                onSelected: (_) {
                  ref.read(selectedCategoryProvider.notifier).state = cat;
                },
                selectedColor: theme.colorScheme.primaryContainer,
                shape: AppRadius.shapeMd,
              );
            },
          ),
        ),

        AppSpacing.gapV24,

        // Featured Crafts Grid
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text('Featured Art & Artifacts', style: theme.textTheme.titleMedium),
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
          gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: isMobile ? 2 : 4,
            crossAxisSpacing: 12,
            mainAxisSpacing: 12,
            childAspectRatio: 0.75,
          ),
          itemBuilder: (context, index) {
            final product = filteredProducts[index];
            return CraftProductCard(
              product: product,
              onTap: () => context.push('/products/${product.id}'),
            );
          },
        ),
      ],
    );
  }
}
