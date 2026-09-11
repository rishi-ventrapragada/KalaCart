import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_constants.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/utils/currency_formatter.dart';
import '../../../core/widgets/app_chip.dart';
import '../../../core/widgets/app_empty_state.dart';
import '../../../core/widgets/app_error_state.dart';
import '../../../core/widgets/app_image_placeholder.dart';
import '../../../core/widgets/app_skeleton.dart';
import '../../../shared/models/product.dart';
import '../../../shared/widgets/social_share_sheet.dart';
import '../../products/data/supabase_products_repository.dart';
import '../../seller/data/sellers_repository.dart';

enum _FeedType { product, story }

/// One card in the discovery feed, derived from a real product or seller.
class _FeedItem {
  final String id;
  final _FeedType type;
  final String title;
  final String subtitle;
  final String artisanName;
  final String location;
  final String category;
  final String? imageUrl;
  final double? price;
  final String? productId;
  final String sellerId;
  final bool inStock;

  const _FeedItem({
    required this.id,
    required this.type,
    required this.title,
    required this.subtitle,
    required this.artisanName,
    required this.location,
    required this.category,
    required this.sellerId,
    this.imageUrl,
    this.price,
    this.productId,
    this.inStock = true,
  });

  factory _FeedItem.fromProduct(Product p) => _FeedItem(
        id: 'product-${p.id}',
        type: _FeedType.product,
        title: p.title,
        subtitle: p.description.trim(),
        artisanName: p.artisanName,
        location: p.region,
        category: p.category,
        imageUrl: p.primaryImageUrl,
        price: p.price,
        productId: p.id,
        sellerId: p.sellerId,
        inStock: p.inStock,
      );

  factory _FeedItem.fromSeller(SellerStorefront s) => _FeedItem(
        id: 'story-${s.id}',
        type: _FeedType.story,
        title: s.shopName,
        subtitle: (s.bio ?? '').trim(),
        artisanName: s.artisanName,
        location: s.regionLabel,
        category: (s.artisanType ?? '').trim(),
        imageUrl: s.avatarUrl,
        sellerId: s.id,
      );

  bool matches(String query) {
    if (query.isEmpty) return true;
    final q = query.toLowerCase();
    return title.toLowerCase().contains(q) ||
        artisanName.toLowerCase().contains(q) ||
        category.toLowerCase().contains(q) ||
        location.toLowerCase().contains(q) ||
        subtitle.toLowerCase().contains(q);
  }
}

class DiscoveryScreen extends ConsumerStatefulWidget {
  const DiscoveryScreen({super.key});

  @override
  ConsumerState<DiscoveryScreen> createState() => _DiscoveryScreenState();
}

class _DiscoveryScreenState extends ConsumerState<DiscoveryScreen> with SingleTickerProviderStateMixin {
  late final TabController _tabController;
  final _searchController = TextEditingController();
  final List<String> _tabs = const ['All', 'Crafts', 'Artisans'];

  String _query = '';
  String _category = AppConstants.craftCategories.first;
  bool _searchVisible = false;
  final Set<String> _liked = {};
  final Set<String> _saved = {};

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: _tabs.length, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    _searchController.dispose();
    super.dispose();
  }

  bool get _isAllCategories => _category == AppConstants.craftCategories.first;

  List<_FeedItem> _applyFilters(List<_FeedItem> items) {
    return items.where((i) {
      if (!_isAllCategories && i.category != _category) return false;
      return i.matches(_query.trim());
    }).toList();
  }

  Future<void> _refresh() async {
    ref.invalidate(publishedProductsProvider);
    ref.invalidate(featuredSellersProvider);
    try {
      await Future.wait([
        ref.read(publishedProductsProvider.future),
        ref.read(featuredSellersProvider.future),
      ]);
    } catch (_) {
      // Error state is rendered by the body.
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final productsAsync = ref.watch(publishedProductsProvider);
    final sellersAsync = ref.watch(featuredSellersProvider);
    final hasActiveFilter = !_isAllCategories;

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            const Icon(Icons.explore_rounded, color: AppColors.primary),
            AppSpacing.gapH8,
            Text(
              'Discover',
              style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: Icon(_searchVisible ? Icons.search_off_rounded : Icons.search_rounded),
            tooltip: 'Search crafts & artisans',
            onPressed: () {
              setState(() {
                _searchVisible = !_searchVisible;
                if (!_searchVisible) {
                  _searchController.clear();
                  _query = '';
                }
              });
            },
          ),
          IconButton(
            icon: Badge(
              isLabelVisible: hasActiveFilter,
              smallSize: 8,
              child: const Icon(Icons.tune_rounded),
            ),
            tooltip: 'Filter by category',
            onPressed: () => _showFilterBottomSheet(context),
          ),
        ],
        bottom: PreferredSize(
          preferredSize: Size.fromHeight(_searchVisible ? 108 : 48),
          child: Column(
            children: [
              if (_searchVisible)
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 4, 16, 4),
                  child: TextField(
                    controller: _searchController,
                    autofocus: true,
                    onChanged: (v) => setState(() => _query = v),
                    decoration: InputDecoration(
                      hintText: 'Search crafts, artisans, categories...',
                      prefixIcon: const Icon(Icons.search_rounded, size: 20),
                      suffixIcon: _query.isEmpty
                          ? null
                          : IconButton(
                              icon: const Icon(Icons.clear, size: 18),
                              onPressed: () => setState(() {
                                _searchController.clear();
                                _query = '';
                              }),
                            ),
                      isDense: true,
                      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                      border: const OutlineInputBorder(borderRadius: AppRadius.borderMd),
                    ),
                  ),
                ),
              Container(
                alignment: Alignment.centerLeft,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                child: TabBar(
                  controller: _tabController,
                  isScrollable: true,
                  tabAlignment: TabAlignment.start,
                  indicatorSize: TabBarIndicatorSize.tab,
                  dividerColor: Colors.transparent,
                  indicator: const BoxDecoration(
                    color: AppColors.primary,
                    borderRadius: AppRadius.borderPill,
                  ),
                  labelColor: Colors.white,
                  unselectedLabelColor: isDark ? AppColors.textSecondaryDark : AppColors.textSecondaryLight,
                  labelStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                  tabs: _tabs.map((t) => Tab(text: t)).toList(),
                ),
              ),
            ],
          ),
        ),
      ),
      body: Builder(
        builder: (context) {
          if (productsAsync.isLoading && sellersAsync.isLoading) {
            return ListView.separated(
              padding: AppSpacing.paddingAllBase,
              itemCount: 3,
              separatorBuilder: (_, __) => AppSpacing.gapV20,
              itemBuilder: (_, __) => const AppSkeleton(height: 320, borderRadius: AppRadius.borderLg),
            );
          }
          if (productsAsync.hasError && sellersAsync.hasError) {
            return AppErrorState(
              message: 'Unable to load the discovery feed right now.',
              onRetry: _refresh,
            );
          }
          final products = productsAsync.valueOrNull ?? const <Product>[];
          final sellers = sellersAsync.valueOrNull ?? const <SellerStorefront>[];
          final productItems = _applyFilters(products.map(_FeedItem.fromProduct).toList());
          final storyItems = _applyFilters(sellers.map(_FeedItem.fromSeller).toList());

          // Interleave: a story after every two products so the feed feels mixed.
          final all = <_FeedItem>[];
          var s = 0;
          for (var i = 0; i < productItems.length; i++) {
            all.add(productItems[i]);
            if (i.isOdd && s < storyItems.length) all.add(storyItems[s++]);
          }
          while (s < storyItems.length) {
            all.add(storyItems[s++]);
          }

          return TabBarView(
            controller: _tabController,
            children: [
              _buildFeedList(all),
              _buildFeedList(productItems),
              _buildFeedList(storyItems),
            ],
          );
        },
      ),
    );
  }

  Widget _buildFeedList(List<_FeedItem> items) {
    if (items.isEmpty) {
      final filtering = _query.trim().isNotEmpty || !_isAllCategories;
      return RefreshIndicator(
        onRefresh: _refresh,
        child: ListView(
          children: [
            SizedBox(
              height: MediaQuery.sizeOf(context).height * 0.6,
              child: AppEmptyState(
                icon: Icons.auto_awesome_motion_outlined,
                title: filtering ? 'No matches' : 'Nothing here yet',
                message: filtering
                    ? 'Try a different search term or clear the category filter.'
                    : 'Artisans have not published anything yet. Check back soon.',
                actionLabel: filtering ? 'Clear filters' : null,
                onAction: filtering
                    ? () => setState(() {
                          _searchController.clear();
                          _query = '';
                          _category = AppConstants.craftCategories.first;
                        })
                    : null,
              ),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _refresh,
      child: ListView.separated(
        padding: AppSpacing.paddingAllBase,
        itemCount: items.length,
        separatorBuilder: (_, __) => AppSpacing.gapV20,
        itemBuilder: (context, index) {
          final item = items[index];
          return _DiscoveryCard(
            item: item,
            isLiked: _liked.contains(item.id),
            isSaved: _saved.contains(item.id),
            onLike: () => setState(() {
              if (!_liked.remove(item.id)) _liked.add(item.id);
            }),
            onSave: () => setState(() {
              if (!_saved.remove(item.id)) _saved.add(item.id);
            }),
          );
        },
      ),
    );
  }

  void _showFilterBottomSheet(BuildContext context) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (sheetContext) {
        var pending = _category;
        return StatefulBuilder(
          builder: (sheetContext, setSheetState) {
            return Padding(
              padding: AppSpacing.paddingAllLg,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'Filter Feed',
                        style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                      ),
                      IconButton(
                        icon: const Icon(Icons.close),
                        onPressed: () => Navigator.of(sheetContext).pop(),
                      ),
                    ],
                  ),
                  AppSpacing.gapV12,
                  const Text('Craft Category', style: TextStyle(fontWeight: FontWeight.w600)),
                  AppSpacing.gapV8,
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: AppConstants.craftCategories
                        .map(
                          (cat) => AppChip(
                            label: cat,
                            isSelected: pending == cat,
                            onSelected: (_) => setSheetState(() => pending = cat),
                          ),
                        )
                        .toList(),
                  ),
                  AppSpacing.gapV24,
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton(
                          style: OutlinedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 14),
                            shape: AppRadius.shapeMd,
                          ),
                          onPressed: () {
                            Navigator.of(sheetContext).pop();
                            setState(() => _category = AppConstants.craftCategories.first);
                          },
                          child: const Text('Reset'),
                        ),
                      ),
                      AppSpacing.gapH12,
                      Expanded(
                        flex: 2,
                        child: ElevatedButton(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.primary,
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(vertical: 14),
                            shape: AppRadius.shapeMd,
                          ),
                          onPressed: () {
                            Navigator.of(sheetContext).pop();
                            setState(() => _category = pending);
                          },
                          child: const Text('Apply Filters', style: TextStyle(fontWeight: FontWeight.bold)),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }
}

class _DiscoveryCard extends StatelessWidget {
  final _FeedItem item;
  final bool isLiked;
  final bool isSaved;
  final VoidCallback onLike;
  final VoidCallback onSave;

  const _DiscoveryCard({
    required this.item,
    required this.isLiked,
    required this.isSaved,
    required this.onLike,
    required this.onSave,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final isStory = item.type == _FeedType.story;

    final badgeColor = isStory ? AppColors.secondary : AppColors.primary;
    final badgeIcon = isStory ? Icons.storefront_rounded : Icons.palette_rounded;
    final badgeText = isStory ? 'ARTISAN STUDIO' : 'HANDMADE CRAFT';
    final imageUrl = item.imageUrl;

    return Container(
      decoration: BoxDecoration(
        color: isDark ? AppColors.surfaceDark : AppColors.surfaceLight,
        borderRadius: AppRadius.borderLg,
        border: Border.all(
          color: isDark ? AppColors.borderDark : AppColors.borderLight,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: isDark ? 0.2 : 0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header: Artisan Info
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                CircleAvatar(
                  radius: 20,
                  backgroundColor: AppColors.primaryContainer,
                  child: Text(
                    item.artisanName.isNotEmpty ? item.artisanName[0].toUpperCase() : 'A',
                    style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary),
                  ),
                ),
                AppSpacing.gapH10,
                Expanded(
                  child: GestureDetector(
                    onTap: item.sellerId.isEmpty ? null : () => context.push('/artisan/${item.sellerId}'),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          item.artisanName,
                          style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        Row(
                          children: [
                            const Icon(Icons.location_on_outlined, size: 12, color: AppColors.textTertiaryLight),
                            const SizedBox(width: 2),
                            Expanded(
                              child: Text(
                                item.location,
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
                ),
                if (item.category.isNotEmpty) ...[
                  AppSpacing.gapH8,
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: badgeColor.withValues(alpha: 0.12),
                      borderRadius: AppRadius.borderPill,
                    ),
                    child: Text(
                      item.category,
                      style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: badgeColor),
                    ),
                  ),
                ],
              ],
            ),
          ),

          // Media
          Stack(
            children: [
              SizedBox(
                height: 220,
                width: double.infinity,
                child: imageUrl == null || imageUrl.isEmpty
                    ? _GradientPlaceholder(color: badgeColor, icon: badgeIcon, label: item.category)
                    : Image.network(
                        imageUrl,
                        fit: BoxFit.cover,
                        errorBuilder: (_, __, ___) =>
                            _GradientPlaceholder(color: badgeColor, icon: badgeIcon, label: item.category),
                      ),
              ),
              Positioned(
                top: 12,
                left: 12,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: badgeColor,
                    borderRadius: AppRadius.borderSm,
                    boxShadow: [
                      BoxShadow(color: Colors.black.withValues(alpha: 0.2), blurRadius: 4),
                    ],
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(badgeIcon, size: 12, color: Colors.white),
                      const SizedBox(width: 4),
                      Text(
                        badgeText,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 0.5,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              if (!isStory && !item.inStock)
                Positioned(
                  top: 12,
                  right: 12,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: const BoxDecoration(color: AppColors.error, borderRadius: AppRadius.borderSm),
                    child: const Text(
                      'OUT OF STOCK',
                      style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
                    ),
                  ),
                ),
              if (item.price != null)
                Positioned(
                  bottom: 12,
                  right: 12,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                    decoration: BoxDecoration(
                      color: Colors.black.withValues(alpha: 0.75),
                      borderRadius: AppRadius.borderMd,
                    ),
                    child: Text(
                      CurrencyFormatter.formatINR(item.price!),
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14),
                    ),
                  ),
                ),
            ],
          ),

          // Action Toolbar
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            child: Row(
              children: [
                IconButton(
                  icon: Icon(
                    isLiked ? Icons.favorite_rounded : Icons.favorite_border_rounded,
                    color: isLiked ? const Color(0xFFE53935) : null,
                  ),
                  tooltip: 'Like',
                  onPressed: onLike,
                ),
                IconButton(
                  icon: Icon(
                    isSaved ? Icons.bookmark_rounded : Icons.bookmark_border_rounded,
                    color: isSaved ? AppColors.secondary : null,
                  ),
                  tooltip: 'Save',
                  onPressed: onSave,
                ),
                IconButton(
                  icon: const Icon(Icons.share_outlined),
                  tooltip: 'Share',
                  onPressed: () {
                    SocialShareSheet.show(
                      context,
                      title: item.title,
                      subtitle: '${item.artisanName} · ${item.location}',
                      deepLink: isStory
                          ? 'https://kalacart.in/artisan/${item.sellerId}'
                          : 'https://kalacart.in/products/${item.productId}',
                      entityType: isStory ? 'store' : 'product',
                    );
                  },
                ),
                const Spacer(),
                if (item.productId != null)
                  ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      foregroundColor: Colors.white,
                      shape: AppRadius.shapePill,
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                    ),
                    icon: const Icon(Icons.shopping_bag_outlined, size: 14),
                    label: const Text('View Craft', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                    onPressed: () => context.push('/products/${item.productId}'),
                  )
                else
                  OutlinedButton.icon(
                    style: OutlinedButton.styleFrom(
                      shape: AppRadius.shapePill,
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    ),
                    icon: const Icon(Icons.storefront_outlined, size: 14),
                    label: const Text('Visit Studio', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                    onPressed: () => context.push('/artisan/${item.sellerId}'),
                  ),
              ],
            ),
          ),

          // Content Description
          Padding(
            padding: const EdgeInsets.fromLTRB(14, 0, 14, 14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item.title,
                  style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold),
                ),
                if (item.subtitle.isNotEmpty) ...[
                  AppSpacing.gapV4,
                  Text(
                    item.subtitle,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: isDark ? AppColors.textSecondaryDark : AppColors.textSecondaryLight,
                      height: 1.35,
                    ),
                    maxLines: 3,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _GradientPlaceholder extends StatelessWidget {
  final Color color;
  final IconData icon;
  final String label;

  const _GradientPlaceholder({required this.color, required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    if (label.isEmpty) {
      return AppImagePlaceholder(borderRadius: BorderRadius.zero, icon: icon);
    }
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [color.withValues(alpha: 0.8), color.withValues(alpha: 0.4)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
      ),
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 54, color: Colors.white.withValues(alpha: 0.85)),
            AppSpacing.gapV8,
            Text(
              label,
              style: const TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
                fontSize: 16,
                letterSpacing: 0.4,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
