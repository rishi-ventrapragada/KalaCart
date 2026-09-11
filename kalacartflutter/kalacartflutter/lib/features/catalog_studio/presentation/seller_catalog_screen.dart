import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_constants.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/utils/currency_formatter.dart';
import '../../../core/widgets/app_button.dart';
import '../../../core/widgets/app_card.dart';
import '../../../core/widgets/app_chip.dart';
import '../../../core/widgets/app_empty_state.dart';
import '../../../core/widgets/app_error_state.dart';
import '../../../core/widgets/app_image_placeholder.dart';
import '../../../core/widgets/app_search_bar.dart';
import '../../../core/widgets/app_skeleton.dart';
import '../../../shared/models/product.dart';
import '../../auth/data/supabase_auth_repository.dart';
import '../../products/data/supabase_products_repository.dart';

class SellerCatalogScreen extends ConsumerStatefulWidget {
  const SellerCatalogScreen({super.key});

  @override
  ConsumerState<SellerCatalogScreen> createState() => _SellerCatalogScreenState();
}

class _SellerCatalogScreenState extends ConsumerState<SellerCatalogScreen> with SingleTickerProviderStateMixin {
  static const _allCategories = 'All Crafts';

  late TabController _tabController;
  final TextEditingController _searchController = TextEditingController();
  String _searchQuery = '';
  String _selectedCategory = _allCategories;
  final Set<String> _busyProductIds = {};

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    _searchController.dispose();
    super.dispose();
  }

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------

  List<Product> _applyFilters(List<Product> products) {
    final q = _searchQuery.trim().toLowerCase();
    return products.where((p) {
      final matchesSearch = q.isEmpty ||
          p.title.toLowerCase().contains(q) ||
          p.category.toLowerCase().contains(q) ||
          p.material.toLowerCase().contains(q);
      final matchesCat = _selectedCategory == _allCategories || p.category == _selectedCategory;
      return matchesSearch && matchesCat;
    }).toList();
  }

  void _showSnack(String message, {bool isError = false}) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        behavior: SnackBarBehavior.floating,
        backgroundColor: isError ? AppColors.error : null,
      ),
    );
  }

  Future<void> _runWrite(Product product, Future<void> Function() action, String successMessage) async {
    setState(() => _busyProductIds.add(product.id));
    try {
      await action();
      ref.invalidate(sellerProductsProvider);
      _showSnack(successMessage);
    } catch (e) {
      _showSnack(authErrorMessage(e), isError: true);
    } finally {
      if (mounted) setState(() => _busyProductIds.remove(product.id));
    }
  }

  Future<void> _handleAction(String action, Product product) async {
    final repo = ref.read(supabaseProductsRepositoryProvider);
    switch (action) {
      case 'details':
        _showProductDetailsSheet(product);
        break;
      case 'edit':
        context.push('/catalog-studio/create', extra: product);
        break;
      case 'publish':
        await _runWrite(
          product,
          () => repo.setStatus(product.id, ProductStatus.published),
          '"${product.title}" is now live in your store.',
        );
        break;
      case 'unpublish':
        await _runWrite(
          product,
          () => repo.setStatus(product.id, ProductStatus.draft),
          '"${product.title}" moved to drafts.',
        );
        break;
      case 'duplicate':
        await _runWrite(
          product,
          () => repo.duplicateProduct(product),
          'Duplicated "${product.title}" into drafts.',
        );
        break;
      case 'archive':
        await _runWrite(
          product,
          () => repo.setStatus(product.id, ProductStatus.archived),
          '"${product.title}" archived.',
        );
        break;
      case 'delete':
        final confirmed = await _confirmDelete(product);
        if (confirmed != true || !mounted) return;
        await _runWrite(
          product,
          () => repo.deleteProduct(product.id),
          'Listing deleted.',
        );
        break;
    }
  }

  Future<bool?> _confirmDelete(Product product) {
    return showDialog<bool>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: const Row(
            children: [
              Icon(Icons.warning_amber_rounded, color: AppColors.error),
              SizedBox(width: 8),
              Text('Delete Listing?'),
            ],
          ),
          content: Text(
            'Are you sure you want to delete "${product.title}"? This removes the product and its wholesale tiers permanently.',
          ),
          actions: [
            TextButton(onPressed: () => Navigator.of(dialogContext).pop(false), child: const Text('Cancel')),
            ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: AppColors.error, foregroundColor: Colors.white),
              onPressed: () => Navigator.of(dialogContext).pop(true),
              child: const Text('Delete'),
            ),
          ],
        );
      },
    );
  }

  // ---------------------------------------------------------------------------
  // Build
  // ---------------------------------------------------------------------------

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final productsAsync = ref.watch(sellerProductsProvider);

    final all = _applyFilters(productsAsync.valueOrNull ?? const []);
    final published = all.where((p) => p.status == ProductStatus.published).toList();
    final drafts = all.where((p) => p.status == ProductStatus.draft).toList();
    final hasData = productsAsync.hasValue;

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            const Icon(Icons.inventory_2_rounded, color: AppColors.primary),
            AppSpacing.gapH8,
            Expanded(
              child: Text(
                'Catalog & Inventory',
                style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.auto_awesome, color: AppColors.aiStudio),
            tooltip: 'Kala-AI Catalog Studio',
            onPressed: () => context.push('/catalog-studio/ai'),
          ),
          IconButton(
            icon: const Icon(Icons.add_rounded),
            tooltip: 'Add product manually',
            onPressed: () => context.push('/catalog-studio/create'),
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          labelColor: AppColors.primary,
          unselectedLabelColor: isDark ? AppColors.textSecondaryDark : AppColors.textSecondaryLight,
          indicatorColor: AppColors.primary,
          tabs: [
            Tab(text: hasData ? 'All (${all.length})' : 'All'),
            Tab(text: hasData ? 'Published (${published.length})' : 'Published'),
            Tab(text: hasData ? 'Drafts (${drafts.length})' : 'Drafts'),
          ],
        ),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            child: AppSearchBar(
              controller: _searchController,
              hintText: 'Search by title, category or material...',
              onChanged: (val) => setState(() => _searchQuery = val),
            ),
          ),
          SizedBox(
            height: 38,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16),
              children: AppConstants.craftCategories.map((cat) {
                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: AppChip(
                    label: cat,
                    isSelected: _selectedCategory == cat,
                    onSelected: (_) => setState(() => _selectedCategory = cat),
                  ),
                );
              }).toList(),
            ),
          ),
          AppSpacing.gapV8,
          Expanded(
            child: productsAsync.when(
              loading: () => ListView.separated(
                padding: AppSpacing.paddingAllBase,
                itemCount: 4,
                separatorBuilder: (_, __) => AppSpacing.gapV12,
                itemBuilder: (_, __) => const AppSkeleton(height: 150, borderRadius: AppRadius.borderMd),
              ),
              error: (e, _) => AppErrorState(
                message: authErrorMessage(e),
                onRetry: () => ref.invalidate(sellerProductsProvider),
              ),
              data: (_) => TabBarView(
                controller: _tabController,
                children: [
                  _buildProductList(all, theme, isDark),
                  _buildProductList(published, theme, isDark),
                  _buildProductList(drafts, theme, isDark),
                ],
              ),
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: AppColors.aiStudio,
        foregroundColor: Colors.white,
        icon: const Icon(Icons.auto_awesome),
        label: const Text('AI Studio', style: TextStyle(fontWeight: FontWeight.bold)),
        onPressed: () => context.push('/catalog-studio/ai'),
      ),
    );
  }

  Widget _buildProductList(List<Product> products, ThemeData theme, bool isDark) {
    if (products.isEmpty) {
      final isFiltering = _searchQuery.trim().isNotEmpty || _selectedCategory != _allCategories;
      return RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(sellerProductsProvider);
          await ref.read(sellerProductsProvider.future).catchError((_) => <Product>[]);
        },
        child: ListView(
          padding: AppSpacing.paddingAllBase,
          children: [
            AppEmptyState(
              icon: Icons.inventory_2_outlined,
              title: isFiltering ? 'No products match your filters' : 'No craft products yet',
              message: isFiltering
                  ? 'Try clearing the search or picking another category.'
                  : 'List your first handcrafted product with the AI studio or add one manually.',
              actionLabel: isFiltering ? 'Clear filters' : 'Add with AI Studio',
              onAction: isFiltering
                  ? () => setState(() {
                        _searchQuery = '';
                        _searchController.clear();
                        _selectedCategory = _allCategories;
                      })
                  : () => context.push('/catalog-studio/ai'),
            ),
            if (!isFiltering)
              Center(
                child: AppButton(
                  label: 'Add manually',
                  icon: Icons.add_rounded,
                  isFullWidth: false,
                  variant: AppButtonVariant.outline,
                  onPressed: () => context.push('/catalog-studio/create'),
                ),
              ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () async {
        ref.invalidate(sellerProductsProvider);
        await ref.read(sellerProductsProvider.future).catchError((_) => <Product>[]);
      },
      child: ListView.separated(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 88),
        itemCount: products.length,
        separatorBuilder: (_, __) => AppSpacing.gapV12,
        itemBuilder: (context, index) => _buildProductCard(products[index], theme, isDark),
      ),
    );
  }

  Widget _buildProductCard(Product product, ThemeData theme, bool isDark) {
    final isBusy = _busyProductIds.contains(product.id);
    final statusColor = switch (product.status) {
      ProductStatus.published => AppColors.success,
      ProductStatus.draft => AppColors.warning,
      ProductStatus.archived => Colors.grey,
    };
    final statusBg = switch (product.status) {
      ProductStatus.published => AppColors.successContainer,
      ProductStatus.draft => AppColors.warningContainer,
      ProductStatus.archived => Colors.grey.withValues(alpha: 0.2),
    };
    final tierCount = product.wholesaleTiers.length;
    final cheapestTier = product.sortedTiers.isEmpty ? null : product.sortedTiers.first;

    return AppCard(
      padding: AppSpacing.paddingAllBase,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              ClipRRect(
                borderRadius: AppRadius.borderMd,
                child: product.primaryImageUrl != null
                    ? Image.network(
                        product.primaryImageUrl!,
                        width: 72,
                        height: 72,
                        fit: BoxFit.cover,
                        errorBuilder: (_, __, ___) => const AppImagePlaceholder(width: 72, height: 72),
                      )
                    : const AppImagePlaceholder(width: 72, height: 72),
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
                          decoration: BoxDecoration(color: statusBg, borderRadius: AppRadius.borderXs),
                          child: Text(
                            product.status.name.toUpperCase(),
                            style: TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: statusColor),
                          ),
                        ),
                        if (isBusy)
                          const Padding(
                            padding: EdgeInsets.all(10),
                            child: SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2)),
                          )
                        else
                          PopupMenuButton<String>(
                            icon: const Icon(Icons.more_vert, size: 20),
                            onSelected: (action) => _handleAction(action, product),
                            itemBuilder: (context) => [
                              const PopupMenuItem(
                                value: 'details',
                                child: Row(children: [Icon(Icons.info_outline, size: 18), SizedBox(width: 8), Text('Details')]),
                              ),
                              const PopupMenuItem(
                                value: 'edit',
                                child: Row(children: [Icon(Icons.edit_outlined, size: 18), SizedBox(width: 8), Text('Edit')]),
                              ),
                              if (product.status == ProductStatus.published)
                                const PopupMenuItem(
                                  value: 'unpublish',
                                  child: Row(children: [Icon(Icons.visibility_off, size: 18), SizedBox(width: 8), Text('Unpublish to draft')]),
                                )
                              else
                                const PopupMenuItem(
                                  value: 'publish',
                                  child: Row(children: [Icon(Icons.visibility, size: 18), SizedBox(width: 8), Text('Publish to store')]),
                                ),
                              const PopupMenuItem(
                                value: 'duplicate',
                                child: Row(children: [Icon(Icons.copy, size: 18), SizedBox(width: 8), Text('Duplicate')]),
                              ),
                              if (product.status != ProductStatus.archived)
                                const PopupMenuItem(
                                  value: 'archive',
                                  child: Row(children: [Icon(Icons.archive_outlined, size: 18), SizedBox(width: 8), Text('Archive')]),
                                ),
                              const PopupMenuItem(
                                value: 'delete',
                                child: Row(children: [
                                  Icon(Icons.delete_outline, color: AppColors.error, size: 18),
                                  SizedBox(width: 8),
                                  Text('Delete', style: TextStyle(color: AppColors.error)),
                                ]),
                              ),
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
                      [
                        product.category,
                        if (product.material.trim().isNotEmpty) product.material.trim(),
                      ].join(' · '),
                      style: theme.textTheme.bodySmall?.copyWith(fontSize: 11),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
            ],
          ),
          AppSpacing.gapV12,
          const Divider(height: 1),
          AppSpacing.gapV8,
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Retail Price', style: theme.textTheme.bodySmall?.copyWith(fontSize: 10)),
                    Text(
                      CurrencyFormatter.formatINR(product.price),
                      style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary, fontSize: 14),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Stock', style: theme.textTheme.bodySmall?.copyWith(fontSize: 10)),
                    Text(
                      product.inStock ? '${product.stock} units' : 'Out of stock',
                      style: TextStyle(
                        fontWeight: FontWeight.w600,
                        fontSize: 12,
                        color: product.inStock ? null : AppColors.error,
                      ),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text('Wholesale', style: theme.textTheme.bodySmall?.copyWith(fontSize: 10)),
                    Text(
                      tierCount == 0
                          ? 'No tiers'
                          : '$tierCount tier${tierCount == 1 ? '' : 's'} · from ${CurrencyFormatter.formatINR(cheapestTier!.pricePerUnit)}',
                      style: const TextStyle(fontWeight: FontWeight.w600, color: AppColors.secondary, fontSize: 11),
                      textAlign: TextAlign.end,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  void _showProductDetailsSheet(Product product) {
    final theme = Theme.of(context);
    showModalBottomSheet<void>(
      context: context,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (sheetContext) {
        final tiers = product.sortedTiers;
        return Padding(
          padding: AppSpacing.paddingAllLg,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('Product Details', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.of(sheetContext).pop()),
                ],
              ),
              AppSpacing.gapV8,
              Text(product.title, style: const TextStyle(fontWeight: FontWeight.w600)),
              AppSpacing.gapV16,
              Row(
                children: [
                  Expanded(
                    child: _DetailTile(
                      label: 'Retail price',
                      value: CurrencyFormatter.formatINR(product.price),
                      color: AppColors.primary,
                      background: AppColors.primaryContainer.withValues(alpha: 0.3),
                    ),
                  ),
                  AppSpacing.gapH12,
                  Expanded(
                    child: _DetailTile(
                      label: 'Stock',
                      value: '${product.stock} units',
                      color: AppColors.secondary,
                      background: AppColors.secondaryContainer.withValues(alpha: 0.3),
                    ),
                  ),
                ],
              ),
              AppSpacing.gapV16,
              Text('Wholesale tiers', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
              AppSpacing.gapV6,
              if (tiers.isEmpty)
                Text('No wholesale tiers set.', style: theme.textTheme.bodySmall)
              else
                ...tiers.map(
                  (t) => Padding(
                    padding: const EdgeInsets.only(bottom: 4),
                    child: Text(
                      '${t.minQuantity}+ units · ${CurrencyFormatter.formatINR(t.pricePerUnit)} per unit',
                      style: theme.textTheme.bodySmall,
                    ),
                  ),
                ),
              AppSpacing.gapV12,
              Text(
                'Created ${DateFormat('d MMM yyyy').format(product.createdAt.toLocal())} · ${product.status.name.toUpperCase()}',
                style: theme.textTheme.bodySmall?.copyWith(color: Colors.grey),
              ),
              AppSpacing.gapV20,
            ],
          ),
        );
      },
    );
  }
}

class _DetailTile extends StatelessWidget {
  final String label;
  final String value;
  final Color color;
  final Color background;

  const _DetailTile({
    required this.label,
    required this.value,
    required this.color,
    required this.background,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: AppSpacing.paddingAllBase,
      decoration: BoxDecoration(color: background, borderRadius: AppRadius.borderMd),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(fontSize: 11)),
          Text(value, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: color)),
        ],
      ),
    );
  }
}
