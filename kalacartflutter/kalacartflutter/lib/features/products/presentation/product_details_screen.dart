import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/utils/currency_formatter.dart';
import '../../../core/widgets/app_chip.dart';
import '../../../core/widgets/app_error_state.dart';
import '../../../core/widgets/app_image_placeholder.dart';
import '../../../core/widgets/app_loading_state.dart';
import '../../../core/widgets/app_skeleton.dart';
import '../../../shared/models/product.dart';
import '../../../shared/widgets/craft_product_card.dart';
import '../../../shared/widgets/social_share_sheet.dart';
import '../data/cart_provider.dart';
import '../data/supabase_products_repository.dart';

class ProductDetailsScreen extends ConsumerStatefulWidget {
  final String productId;

  const ProductDetailsScreen({super.key, required this.productId});

  @override
  ConsumerState<ProductDetailsScreen> createState() => _ProductDetailsScreenState();
}

class _ProductDetailsScreenState extends ConsumerState<ProductDetailsScreen> {
  int _quantity = 1;
  int _selectedImageIndex = 0;
  bool _isBookmarked = false;

  @override
  Widget build(BuildContext context) {
    final productAsync = ref.watch(productProvider(widget.productId));

    return productAsync.when(
      loading: () => Scaffold(
        appBar: AppBar(),
        body: const AppLoadingState(message: 'Loading craft details...'),
      ),
      error: (e, _) => Scaffold(
        appBar: AppBar(),
        body: AppErrorState(
          message: 'Unable to load this craft right now.',
          onRetry: () => ref.invalidate(productProvider(widget.productId)),
        ),
      ),
      data: (product) {
        if (product == null) {
          return Scaffold(
            appBar: AppBar(),
            body: AppErrorState(
              title: 'Craft not found',
              message: 'This product may have been removed or is no longer listed.',
              retryLabel: 'Back to Discovery',
              onRetry: () => context.go('/discovery'),
            ),
          );
        }
        return _buildProduct(context, product);
      },
    );
  }

  Widget _buildProduct(BuildContext context, Product product) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final images = product.imageUrls;
    final tiers = product.sortedTiers;
    final maxQty = product.stock > 0 ? product.stock : 1;
    if (_quantity > maxQty) _quantity = maxQty;
    final unitPrice = product.unitPriceFor(_quantity);
    final wholesaleApplied = unitPrice < product.price;
    final totalPrice = unitPrice * _quantity;
    final canBuy = product.inStock;
    final relatedAsync = ref.watch(filteredProductsProvider(CatalogQuery(category: product.category)));
    final imageIndex = images.isEmpty ? 0 : _selectedImageIndex.clamp(0, images.length - 1);

    return Scaffold(
      body: CustomScrollView(
        slivers: [
          // Collapsible Image Gallery AppBar
          SliverAppBar(
            expandedHeight: 340,
            pinned: true,
            flexibleSpace: FlexibleSpaceBar(
              background: Stack(
                fit: StackFit.expand,
                children: [
                  if (images.isEmpty)
                    const AppImagePlaceholder(borderRadius: BorderRadius.zero, icon: Icons.palette_rounded)
                  else
                    Image.network(
                      images[imageIndex],
                      fit: BoxFit.cover,
                      errorBuilder: (_, __, ___) =>
                          const AppImagePlaceholder(borderRadius: BorderRadius.zero, icon: Icons.palette_rounded),
                    ),
                  // Scrim so the toolbar icons stay legible over photos
                  Positioned.fill(
                    child: DecoratedBox(
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          colors: [Colors.black.withValues(alpha: 0.35), Colors.transparent],
                          begin: Alignment.topCenter,
                          end: Alignment.center,
                        ),
                      ),
                    ),
                  ),
                  if (images.length > 1)
                    Positioned(
                      bottom: 12,
                      left: 16,
                      right: 16,
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: List.generate(images.length, (index) {
                          final isSelected = imageIndex == index;
                          return GestureDetector(
                            onTap: () => setState(() => _selectedImageIndex = index),
                            child: Container(
                              margin: const EdgeInsets.symmetric(horizontal: 4),
                              width: isSelected ? 24 : 8,
                              height: 8,
                              decoration: BoxDecoration(
                                color: isSelected ? Colors.white : Colors.white54,
                                borderRadius: AppRadius.borderPill,
                              ),
                            ),
                          );
                        }),
                      ),
                    ),
                ],
              ),
            ),
            actions: [
              IconButton(
                icon: Icon(_isBookmarked ? Icons.bookmark : Icons.bookmark_border),
                tooltip: 'Save',
                onPressed: () => setState(() => _isBookmarked = !_isBookmarked),
              ),
              IconButton(
                icon: const Icon(Icons.share_outlined),
                tooltip: 'Share Product',
                onPressed: () {
                  SocialShareSheet.show(
                    context,
                    title: product.title,
                    subtitle: '${product.artisanName} · ${product.region}',
                    deepLink: 'https://kalacart.in/products/${product.id}',
                    entityType: 'product',
                  );
                },
              ),
            ],
          ),

          if (images.length > 1)
            SliverToBoxAdapter(
              child: SizedBox(
                height: 72,
                child: ListView.separated(
                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
                  scrollDirection: Axis.horizontal,
                  itemCount: images.length,
                  separatorBuilder: (_, __) => AppSpacing.gapH8,
                  itemBuilder: (context, index) {
                    final selected = imageIndex == index;
                    return GestureDetector(
                      onTap: () => setState(() => _selectedImageIndex = index),
                      child: Container(
                        width: 60,
                        decoration: BoxDecoration(
                          borderRadius: AppRadius.borderSm,
                          border: Border.all(
                            color: selected ? AppColors.primary : Colors.transparent,
                            width: 2,
                          ),
                        ),
                        child: ClipRRect(
                          borderRadius: AppRadius.borderSm,
                          child: Image.network(
                            images[index],
                            fit: BoxFit.cover,
                            errorBuilder: (_, __, ___) => const AppImagePlaceholder(),
                          ),
                        ),
                      ),
                    );
                  },
                ),
              ),
            ),

          // Product Details Body
          SliverToBoxAdapter(
            child: Padding(
              padding: AppSpacing.paddingAllBase,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      AppChip(
                        label: product.category.toUpperCase(),
                        variant: AppChipVariant.badge,
                        color: AppColors.primary,
                        icon: const Icon(Icons.category_outlined, size: 12, color: Colors.white),
                      ),
                      _StockLabel(stock: product.stock),
                    ],
                  ),
                  AppSpacing.gapV12,

                  // Product Title
                  Text(
                    product.title,
                    style: theme.textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w800,
                      height: 1.25,
                    ),
                  ),
                  AppSpacing.gapV8,

                  // Artisan Row
                  GestureDetector(
                    onTap: product.sellerId.isEmpty ? null : () => context.push('/artisan/${product.sellerId}'),
                    child: Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: isDark ? AppColors.surfaceDark : Colors.grey.shade100,
                        borderRadius: AppRadius.borderMd,
                        border: Border.all(
                          color: isDark ? AppColors.borderDark : AppColors.borderLight,
                        ),
                      ),
                      child: Row(
                        children: [
                          CircleAvatar(
                            radius: 20,
                            backgroundColor: AppColors.primaryContainer,
                            child: Text(
                              product.artisanName.isNotEmpty ? product.artisanName[0].toUpperCase() : 'A',
                              style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary),
                            ),
                          ),
                          AppSpacing.gapH12,
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  product.artisanName,
                                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                                Row(
                                  children: [
                                    const Icon(Icons.location_on_outlined, size: 12, color: AppColors.primary),
                                    const SizedBox(width: 2),
                                    Expanded(
                                      child: Text(
                                        product.region,
                                        style: TextStyle(
                                          fontSize: 11,
                                          color: isDark ? AppColors.textTertiaryDark : AppColors.textSecondaryLight,
                                        ),
                                        maxLines: 1,
                                        overflow: TextOverflow.ellipsis,
                                      ),
                                    ),
                                  ],
                                ),
                                if ((product.sellerArtisanType ?? '').isNotEmpty)
                                  Text(
                                    product.sellerArtisanType!,
                                    style: const TextStyle(fontSize: 11, color: AppColors.secondary, fontWeight: FontWeight.w600),
                                  ),
                              ],
                            ),
                          ),
                          const Icon(Icons.chevron_right, color: Colors.grey),
                        ],
                      ),
                    ),
                  ),
                  AppSpacing.gapV16,

                  // Price Section
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.baseline,
                    textBaseline: TextBaseline.alphabetic,
                    children: [
                      Text(
                        CurrencyFormatter.formatINR(unitPrice),
                        style: theme.textTheme.headlineSmall?.copyWith(
                          fontWeight: FontWeight.w900,
                          color: AppColors.primary,
                        ),
                      ),
                      AppSpacing.gapH4,
                      Text(
                        '/ unit',
                        style: TextStyle(fontSize: 12, color: isDark ? AppColors.textTertiaryDark : Colors.grey),
                      ),
                      if (wholesaleApplied) ...[
                        AppSpacing.gapH8,
                        Text(
                          CurrencyFormatter.formatINR(product.price),
                          style: TextStyle(
                            decoration: TextDecoration.lineThrough,
                            color: isDark ? AppColors.textTertiaryDark : Colors.grey,
                            fontSize: 14,
                          ),
                        ),
                        AppSpacing.gapH8,
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: const BoxDecoration(
                            color: AppColors.secondaryContainer,
                            borderRadius: AppRadius.borderXs,
                          ),
                          child: const Text(
                            'WHOLESALE RATE',
                            style: TextStyle(color: AppColors.onSecondaryContainer, fontSize: 9, fontWeight: FontWeight.bold),
                          ),
                        ),
                      ],
                    ],
                  ),
                  AppSpacing.gapV12,

                  // Wholesale Pricing Table
                  if (tiers.isNotEmpty) ...[
                    Text('Wholesale Tier Pricing', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
                    AppSpacing.gapV6,
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: isDark ? AppColors.surfaceDark : Colors.white,
                        borderRadius: AppRadius.borderMd,
                        border: Border.all(color: isDark ? AppColors.borderDark : AppColors.borderLight),
                      ),
                      child: Column(
                        children: [
                          _TierRow(
                            label: tiers.first.minQuantity > 1 ? '1 - ${tiers.first.minQuantity - 1} units' : 'Retail',
                            price: product.price,
                            isActive: !wholesaleApplied,
                          ),
                          for (var i = 0; i < tiers.length; i++)
                            _TierRow(
                              label: i + 1 < tiers.length
                                  ? '${tiers[i].minQuantity} - ${tiers[i + 1].minQuantity - 1} units'
                                  : '${tiers[i].minQuantity}+ units',
                              price: tiers[i].pricePerUnit,
                              isActive: wholesaleApplied &&
                                  _quantity >= tiers[i].minQuantity &&
                                  (i + 1 >= tiers.length || _quantity < tiers[i + 1].minQuantity),
                            ),
                        ],
                      ),
                    ),
                    AppSpacing.gapV16,
                  ],

                  // Provenance Passport Tile
                  GestureDetector(
                    onTap: () => context.push('/passport/${product.id}'),
                    child: Container(
                      padding: AppSpacing.paddingAllBase,
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [Color(0xFF1B5E20), Color(0xFF2E7D32)],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ),
                        borderRadius: AppRadius.borderMd,
                        boxShadow: [
                          BoxShadow(
                            color: Colors.green.withValues(alpha: 0.2),
                            blurRadius: 8,
                            offset: const Offset(0, 3),
                          ),
                        ],
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.verified_outlined, color: Colors.white, size: 28),
                          AppSpacing.gapH12,
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  'PROVENANCE PASSPORT',
                                  style: TextStyle(color: Colors.white70, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 0.8),
                                ),
                                Text(
                                  product.passportCode,
                                  style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.bold),
                                ),
                              ],
                            ),
                          ),
                          const Icon(Icons.arrow_forward_ios_rounded, color: Colors.white, size: 14),
                        ],
                      ),
                    ),
                  ),
                  AppSpacing.gapV20,

                  // Specifications
                  Text('Craft Specifications', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                  AppSpacing.gapV8,
                  _SpecRow(label: 'Category', value: product.category),
                  _SpecRow(label: 'Material', value: product.material.trim().isEmpty ? 'Not provided' : product.material),
                  _SpecRow(label: 'Region', value: product.region),
                  _SpecRow(label: 'Stock', value: product.inStock ? '${product.stock} available' : 'Out of stock'),
                  AppSpacing.gapV16,

                  // Description
                  Text('About this craft', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                  AppSpacing.gapV6,
                  Text(
                    product.description.trim().isEmpty ? 'The artisan has not added a description yet.' : product.description,
                    style: theme.textTheme.bodyMedium?.copyWith(
                      height: 1.45,
                      color: isDark ? AppColors.textSecondaryDark : AppColors.textSecondaryLight,
                    ),
                  ),
                  AppSpacing.gapV24,

                  // Related Crafts
                  Text('More in ${product.category}', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                  AppSpacing.gapV12,
                  relatedAsync.when(
                    loading: () => SizedBox(
                      height: 240,
                      child: ListView.separated(
                        scrollDirection: Axis.horizontal,
                        itemCount: 2,
                        separatorBuilder: (_, __) => AppSpacing.gapH12,
                        itemBuilder: (_, __) => const SizedBox(width: 170, child: ProductCardSkeleton()),
                      ),
                    ),
                    error: (_, __) => const SizedBox.shrink(),
                    data: (related) {
                      final others = related.where((p) => p.id != product.id).toList();
                      if (others.isEmpty) {
                        return Text(
                          'No other crafts in this category yet.',
                          style: theme.textTheme.bodySmall?.copyWith(color: Colors.grey),
                        );
                      }
                      return SizedBox(
                        height: 240,
                        child: ListView.separated(
                          scrollDirection: Axis.horizontal,
                          itemCount: others.length,
                          separatorBuilder: (_, __) => AppSpacing.gapH12,
                          itemBuilder: (context, index) {
                            final rel = others[index];
                            return SizedBox(
                              width: 170,
                              child: CraftProductCard(
                                product: rel,
                                onTap: () => context.push('/products/${rel.id}'),
                              ),
                            );
                          },
                        ),
                      );
                    },
                  ),
                  const SizedBox(height: 140),
                ],
              ),
            ),
          ),
        ],
      ),

      // Bottom Bar
      bottomSheet: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: isDark ? AppColors.surfaceDark : Colors.white,
          border: Border(top: BorderSide(color: isDark ? AppColors.borderDark : AppColors.borderLight)),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.1),
              blurRadius: 10,
              offset: const Offset(0, -2),
            ),
          ],
        ),
        child: SafeArea(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Row(
                children: [
                  // Quantity +/- Controls
                  Container(
                    decoration: BoxDecoration(
                      border: Border.all(color: Colors.grey.shade400),
                      borderRadius: AppRadius.borderMd,
                    ),
                    child: Row(
                      children: [
                        IconButton(
                          icon: const Icon(Icons.remove, size: 16),
                          onPressed: _quantity > 1 ? () => setState(() => _quantity -= 1) : null,
                        ),
                        Text('$_quantity', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                        IconButton(
                          icon: const Icon(Icons.add, size: 16),
                          onPressed: _quantity < maxQty ? () => setState(() => _quantity += 1) : null,
                        ),
                      ],
                    ),
                  ),
                  AppSpacing.gapH8,

                  // Add to Cart Button
                  Expanded(
                    child: OutlinedButton.icon(
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        shape: AppRadius.shapeMd,
                      ),
                      icon: const Icon(Icons.add_shopping_cart, size: 16),
                      label: const Text('Add to Cart', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                      onPressed: !canBuy ? null : () => _addToCart(product),
                    ),
                  ),
                  AppSpacing.gapH8,

                  // Buy Now Button
                  Expanded(
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.primary,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        shape: AppRadius.shapeMd,
                      ),
                      onPressed: !canBuy
                          ? null
                          : () {
                              ref.read(cartProvider.notifier).addToCart(product, quantity: _quantity);
                              context.push('/checkout');
                            },
                      child: Text(
                        canBuy ? 'Buy ${CurrencyFormatter.formatINR(totalPrice)}' : 'Out of stock',
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ),
                ],
              ),
              AppSpacing.gapV8,
              SizedBox(
                width: double.infinity,
                height: 40,
                child: TextButton.icon(
                  style: TextButton.styleFrom(
                    foregroundColor: AppColors.secondary,
                    shape: AppRadius.shapeMd,
                  ),
                  icon: const Icon(Icons.request_quote_outlined, size: 16),
                  label: const Text(
                    'Request a custom / bulk quote',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                  ),
                  onPressed: () => context.push('/rfq/create?productId=${product.id}'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _addToCart(Product product) {
    ref.read(cartProvider.notifier).addToCart(product, quantity: _quantity);
    final router = GoRouter.of(context);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(_quantity == 1 ? 'Added to cart.' : 'Added $_quantity items to cart.'),
        behavior: SnackBarBehavior.floating,
        action: SnackBarAction(
          label: 'View Cart',
          onPressed: () => router.push('/cart'),
        ),
      ),
    );
  }
}

class _StockLabel extends StatelessWidget {
  final int stock;

  const _StockLabel({required this.stock});

  @override
  Widget build(BuildContext context) {
    final inStock = stock > 0;
    final color = inStock ? AppColors.success : AppColors.error;
    return Row(
      children: [
        Icon(inStock ? Icons.check_circle_outline : Icons.remove_circle_outline, size: 14, color: color),
        const SizedBox(width: 4),
        Text(
          inStock ? '$stock in stock' : 'Out of stock',
          style: TextStyle(color: color, fontSize: 12, fontWeight: FontWeight.w600),
        ),
      ],
    );
  }
}

class _TierRow extends StatelessWidget {
  final String label;
  final double price;
  final bool isActive;

  const _TierRow({required this.label, required this.price, required this.isActive});

  @override
  Widget build(BuildContext context) {
    final style = TextStyle(
      fontWeight: isActive ? FontWeight.bold : FontWeight.normal,
      color: isActive ? AppColors.secondary : null,
      fontSize: 13,
    );
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              if (isActive) ...[
                const Icon(Icons.check_rounded, size: 14, color: AppColors.secondary),
                const SizedBox(width: 4),
              ],
              Text(label, style: style),
            ],
          ),
          Text('${CurrencyFormatter.formatINR(price)} / unit', style: style),
        ],
      ),
    );
  }
}

class _SpecRow extends StatelessWidget {
  final String label;
  final String value;

  const _SpecRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 110,
            child: Text(label, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.grey)),
          ),
          Expanded(
            child: Text(value, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500)),
          ),
        ],
      ),
    );
  }
}
