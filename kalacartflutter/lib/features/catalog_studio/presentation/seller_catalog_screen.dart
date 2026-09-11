import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/utils/currency_formatter.dart';
import '../../../core/widgets/app_button.dart';
import '../../../core/widgets/app_card.dart';
import '../../../core/widgets/app_chip.dart';
import '../../../core/widgets/app_search_bar.dart';
import '../../../shared/models/seller_models.dart';
import '../../seller/data/seller_repository.dart';

class SellerCatalogScreen extends ConsumerStatefulWidget {
  const SellerCatalogScreen({super.key});

  @override
  ConsumerState<SellerCatalogScreen> createState() => _SellerCatalogScreenState();
}

class _SellerCatalogScreenState extends ConsumerState<SellerCatalogScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  String _searchQuery = '';
  String _selectedCategory = 'All Categories';

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final allProducts = ref.watch(sellerProductsProvider);

    final publishedProducts = allProducts.where((p) => p.status == ProductStatus.published).toList();
    final draftProducts = allProducts.where((p) => p.status == ProductStatus.draft).toList();

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            const Icon(Icons.inventory_2_rounded, color: AppColors.primary),
            AppSpacing.gapH8,
            Text(
              'Artisan Catalog & Inventory',
              style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.auto_awesome, color: Color(0xFF6A1B9A)),
            tooltip: 'Kala-AI Catalog Studio',
            onPressed: () => context.push('/catalog-studio/ai'),
          ),
          IconButton(
            icon: const Icon(Icons.add_rounded),
            tooltip: 'Manual Product Wizard',
            onPressed: () => context.push('/catalog-studio/create'),
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          labelColor: AppColors.primary,
          unselectedLabelColor: isDark ? AppColors.textSecondaryDark : AppColors.textSecondaryLight,
          indicatorColor: AppColors.primary,
          tabs: [
            Tab(text: 'All (${allProducts.length})'),
            Tab(text: 'Published (${publishedProducts.length})'),
            Tab(text: 'Drafts (${draftProducts.length})'),
          ],
        ),
      ),
      body: Column(
        children: [
          // Search & Filters Header
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            child: AppSearchBar(
              hintText: 'Search crafts, materials or GI IDs...',
              onChanged: (val) {
                setState(() {
                  _searchQuery = val.toLowerCase();
                });
              },
            ),
          ),

          // Categories Filter Row
          SizedBox(
            height: 38,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16),
              children: [
                'All Categories',
                'Pottery & Terracotta',
                'Handloom & Textiles',
                'Brass & Metal Craft',
                'Paintings & Madhubani',
              ].map((cat) {
                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: AppChip(
                    label: cat,
                    isSelected: _selectedCategory == cat,
                    onSelected: (_) {
                      setState(() {
                        _selectedCategory = cat;
                      });
                    },
                  ),
                );
              }).toList(),
            ),
          ),
          AppSpacing.gapV8,

          // Tab Bar View
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                _buildProductList(allProducts, theme, isDark),
                _buildProductList(publishedProducts, theme, isDark),
                _buildProductList(draftProducts, theme, isDark),
              ],
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: const Color(0xFF6A1B9A),
        foregroundColor: Colors.white,
        icon: const Icon(Icons.auto_awesome),
        label: const Text('AI Studio Add', style: TextStyle(fontWeight: FontWeight.bold)),
        onPressed: () => context.push('/catalog-studio/ai'),
      ),
    );
  }

  Widget _buildProductList(List<SellerProduct> products, ThemeData theme, bool isDark) {
    final filtered = products.where((p) {
      final matchesSearch = p.title.toLowerCase().contains(_searchQuery) ||
          p.category.toLowerCase().contains(_searchQuery) ||
          p.material.toLowerCase().contains(_searchQuery);
      final matchesCat = _selectedCategory == 'All Categories' || p.category == _selectedCategory;
      return matchesSearch && matchesCat;
    }).toList();

    if (filtered.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.inventory_2_outlined, size: 48, color: Colors.grey),
            AppSpacing.gapV12,
            const Text('No craft products found', style: TextStyle(fontWeight: FontWeight.bold)),
            AppSpacing.gapV4,
            const Text('Use Kala-AI Studio to add new items in 60s', style: TextStyle(color: Colors.grey)),
            AppSpacing.gapV16,
            AppButton(
              label: 'Add Product with AI',
              icon: Icons.auto_awesome,
              variant: AppButtonVariant.secondary,
              onPressed: () => context.push('/catalog-studio/ai'),
            ),
          ],
        ),
      );
    }

    return ListView.separated(
      padding: AppSpacing.paddingAllBase,
      itemCount: filtered.length,
      separatorBuilder: (_, __) => AppSpacing.gapV12,
      itemBuilder: (context, index) {
        final product = filtered[index];
        return _buildProductCard(product, theme, isDark);
      },
    );
  }

  Widget _buildProductCard(SellerProduct product, ThemeData theme, bool isDark) {
    final isPublished = product.status == ProductStatus.published;

    return AppCard(
      padding: AppSpacing.paddingAllBase,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Craft Thumbnail
              Container(
                width: 72,
                height: 72,
                decoration: BoxDecoration(
                  color: const Color(0xFF6A1B9A).withValues(alpha: 0.1),
                  borderRadius: AppRadius.borderMd,
                ),
                child: Center(
                  child: Icon(
                    Icons.palette_outlined,
                    size: 32,
                    color: const Color(0xFF6A1B9A).withValues(alpha: 0.7),
                  ),
                ),
              ),
              AppSpacing.gapH12,
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: isPublished ? AppColors.successContainer : AppColors.warningContainer,
                            borderRadius: AppRadius.borderXs,
                          ),
                          child: Text(
                            isPublished ? 'PUBLISHED' : 'DRAFT',
                            style: TextStyle(
                              fontSize: 9,
                              fontWeight: FontWeight.bold,
                              color: isPublished ? AppColors.success : AppColors.warning,
                            ),
                          ),
                        ),
                        PopupMenuButton<String>(
                          icon: const Icon(Icons.more_vert, size: 20),
                          onSelected: (action) => _handleAction(action, product),
                          itemBuilder: (context) => [
                            const PopupMenuItem(value: 'analytics', child: Row(children: [Icon(Icons.bar_chart, size: 18), SizedBox(width: 8), Text('Product Analytics')])),
                            const PopupMenuItem(value: 'duplicate', child: Row(children: [Icon(Icons.copy, size: 18), SizedBox(width: 8), Text('Duplicate Listing')])),
                            PopupMenuItem(
                              value: 'toggle_status',
                              child: Row(children: [
                                Icon(isPublished ? Icons.visibility_off : Icons.visibility, size: 18),
                                const SizedBox(width: 8),
                                Text(isPublished ? 'Unpublish to Draft' : 'Publish to Store'),
                              ]),
                            ),
                            const PopupMenuItem(value: 'delete', child: Row(children: [Icon(Icons.delete_outline, color: Colors.red, size: 18), SizedBox(width: 8), Text('Delete Listing', style: TextStyle(color: Colors.red))])),
                          ],
                        ),
                      ],
                    ),
                    Text(
                      product.title,
                      style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    AppSpacing.gapV4,
                    Text(
                      '${product.category} · Stock: ${product.stockQuantity} units',
                      style: theme.textTheme.bodySmall?.copyWith(fontSize: 11),
                    ),
                  ],
                ),
              ),
            ],
          ),
          AppSpacing.gapV12,
          const Divider(height: 1),
          AppSpacing.gapV8,

          // Stats & Pricing Row
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Retail Price', style: theme.textTheme.bodySmall?.copyWith(fontSize: 10)),
                  Text(
                    CurrencyFormatter.formatINR(product.retailPrice),
                    style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary, fontSize: 14),
                  ),
                ],
              ),
              if (product.wholesaleTiers.isNotEmpty)
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Wholesale Tier', style: theme.textTheme.bodySmall?.copyWith(fontSize: 10)),
                    Text(
                      '${CurrencyFormatter.formatINR(product.wholesaleTiers.first.pricePerUnit)} (${product.wholesaleTiers.first.minQuantity}+ qty)',
                      style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.secondary, fontSize: 12),
                    ),
                  ],
                ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text('Performance', style: theme.textTheme.bodySmall?.copyWith(fontSize: 10)),
                  Text(
                    '${product.viewsCount} views · ${product.salesCount} sold',
                    style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 11),
                  ),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }

  void _handleAction(String action, SellerProduct product) {
    switch (action) {
      case 'analytics':
        _showProductAnalyticsModal(context, product);
        break;
      case 'duplicate':
        ref.read(sellerProductsProvider.notifier).duplicateProduct(product.id);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Duplicated "${product.title}" into drafts!')),
        );
        break;
      case 'toggle_status':
        ref.read(sellerProductsProvider.notifier).toggleStatus(product.id);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Listing status updated for "${product.title}"!')),
        );
        break;
      case 'delete':
        _showDeleteConfirmationDialog(context, product);
        break;
    }
  }

  void _showDeleteConfirmationDialog(BuildContext context, SellerProduct product) {
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Row(
            children: [
              Icon(Icons.warning_amber_rounded, color: Colors.red),
              SizedBox(width: 8),
              Text('Delete Listing?'),
            ],
          ),
          content: Text('Are you sure you want to delete "${product.title}"? This action cannot be undone.'),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
            ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: Colors.red, foregroundColor: Colors.white),
              onPressed: () {
                ref.read(sellerProductsProvider.notifier).deleteProduct(product.id);
                Navigator.pop(context);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Listing deleted.')),
                );
              },
              child: const Text('Delete'),
            ),
          ],
        );
      },
    );
  }

  void _showProductAnalyticsModal(BuildContext context, SellerProduct product) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return Padding(
          padding: AppSpacing.paddingAllLg,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('Product Analytics', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.pop(context)),
                ],
              ),
              AppSpacing.gapV8,
              Text(product.title, style: const TextStyle(fontWeight: FontWeight.w600)),
              AppSpacing.gapV16,
              Row(
                children: [
                  Expanded(
                    child: Container(
                      padding: AppSpacing.paddingAllBase,
                      decoration: BoxDecoration(
                        color: AppColors.primaryContainer.withValues(alpha: 0.3),
                        borderRadius: AppRadius.borderMd,
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('Total Revenue', style: TextStyle(fontSize: 11)),
                          Text(CurrencyFormatter.formatINR(product.totalRevenue), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: AppColors.primary)),
                        ],
                      ),
                    ),
                  ),
                  AppSpacing.gapH12,
                  Expanded(
                    child: Container(
                      padding: AppSpacing.paddingAllBase,
                      decoration: BoxDecoration(
                        color: AppColors.secondaryContainer.withValues(alpha: 0.3),
                        borderRadius: AppRadius.borderMd,
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('Conversion Rate', style: TextStyle(fontSize: 11)),
                          Text(
                            product.viewsCount > 0 ? '${((product.salesCount / product.viewsCount) * 100).toStringAsFixed(1)}%' : '0%',
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: AppColors.secondary),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
              AppSpacing.gapV16,
              const Text('Top Buyer Locations:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
              AppSpacing.gapV6,
              const Text('1. New Delhi & NCR (42%)\n2. Mumbai, Maharashtra (28%)\n3. Bengaluru, Karnataka (18%)', style: TextStyle(fontSize: 12, height: 1.4)),
              AppSpacing.gapV20,
            ],
          ),
        );
      },
    );
  }
}
