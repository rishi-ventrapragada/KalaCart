import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/utils/currency_formatter.dart';
import '../../../core/widgets/app_card.dart';
import '../../../shared/models/buyer_models.dart';
import '../../../shared/widgets/craft_product_card.dart';
import '../../../shared/widgets/social_share_sheet.dart';
import '../data/buyer_catalog_repository.dart';

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
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final product = ref.watch(singleProductProvider(widget.productId)) ?? mockCraftCatalog.first;
    final allProducts = ref.watch(buyerCatalogProvider);
    final relatedProducts = allProducts.where((p) => p.id != product.id).toList();

    // Check wholesale discount for selected quantity
    double currentUnitPrice = product.retailPrice;
    for (final tier in product.wholesaleTiers) {
      if (_quantity >= tier.minQuantity && (tier.maxQuantity == null || _quantity <= tier.maxQuantity!)) {
        currentUnitPrice = tier.pricePerUnit;
        break;
      }
    }

    final totalPrice = currentUnitPrice * _quantity;

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
                  Container(
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [
                          AppColors.primary.withValues(alpha: 0.8),
                          AppColors.secondary.withValues(alpha: 0.9),
                        ],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                    ),
                    child: Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.palette_rounded, size: 72, color: Colors.white70),
                          AppSpacing.gapV8,
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                            decoration: const BoxDecoration(
                              color: Colors.black38,
                              borderRadius: AppRadius.borderPill,
                            ),
                            child: Text(
                              'Photo ${_selectedImageIndex + 1} of 4 · Master Artisan Crafted',
                              style: const TextStyle(color: Colors.white, fontSize: 11),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),

                  // Image thumbnails at bottom of header
                  Positioned(
                    bottom: 12,
                    left: 16,
                    right: 16,
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: List.generate(4, (index) {
                        final isSelected = _selectedImageIndex == index;
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
                tooltip: 'Save to Wishlist',
                onPressed: () {
                  setState(() => _isBookmarked = !_isBookmarked);
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text(_isBookmarked ? 'Saved to your craft collection!' : 'Removed from wishlist.'),
                      duration: const Duration(seconds: 1),
                    ),
                  );
                },
              ),
              IconButton(
                icon: const Icon(Icons.share_outlined),
                tooltip: 'Share Product',
                onPressed: () {
                  SocialShareSheet.show(
                    context,
                    title: product.title,
                    subtitle: '${product.artisanName} · ${product.villageLocation}, ${product.state}',
                    deepLink: 'https://kalacart.in/product/${product.id}',
                    entityType: 'product',
                  );
                },
              ),
            ],
          ),

          // Product Details Body
          SliverToBoxAdapter(
            child: Padding(
              padding: AppSpacing.paddingAllBase,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // GI Tag & Cluster Badge
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: const BoxDecoration(
                          color: AppColors.successContainer,
                          borderRadius: AppRadius.borderSm,
                        ),
                        child: Row(
                          children: [
                            const Icon(Icons.verified, size: 14, color: AppColors.success),
                            const SizedBox(width: 4),
                            Text(
                              product.isGiTagged ? 'VERIFIED GI TAGGED' : 'HANDMADE CERTIFIED',
                              style: const TextStyle(
                                color: AppColors.success,
                                fontSize: 10,
                                fontWeight: FontWeight.bold,
                                letterSpacing: 0.5,
                              ),
                            ),
                          ],
                        ),
                      ),
                      Row(
                        children: [
                          const Icon(Icons.star_rounded, color: Colors.amber, size: 18),
                          const SizedBox(width: 2),
                          Text('${product.rating}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                          Text(' (${product.reviewCount})', style: const TextStyle(color: Colors.grey, fontSize: 12)),
                        ],
                      ),
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

                  // Artisan Card Link
                  GestureDetector(
                    onTap: () => context.push('/artisan/${product.artisanId}'),
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
                            child: Text(product.artisanName[0], style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary)),
                          ),
                          AppSpacing.gapH12,
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  product.artisanName,
                                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                                ),
                                Row(
                                  children: [
                                    const Icon(Icons.location_on_outlined, size: 12, color: AppColors.primary),
                                    const SizedBox(width: 2),
                                    Text(
                                      '${product.villageLocation}, ${product.state}',
                                      style: TextStyle(fontSize: 11, color: isDark ? AppColors.textTertiaryDark : AppColors.textSecondaryLight),
                                    ),
                                  ],
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

                  // Price Section (Retail vs Wholesale)
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.baseline,
                    textBaseline: TextBaseline.alphabetic,
                    children: [
                      Text(
                        CurrencyFormatter.formatINR(currentUnitPrice),
                        style: theme.textTheme.headlineSmall?.copyWith(
                          fontWeight: FontWeight.w900,
                          color: AppColors.primary,
                        ),
                      ),
                      if (product.originalPrice != null && _quantity < 5) ...[
                        AppSpacing.gapH8,
                        Text(
                          CurrencyFormatter.formatINR(product.originalPrice!),
                          style: TextStyle(
                            decoration: TextDecoration.lineThrough,
                            color: isDark ? AppColors.textTertiaryDark : Colors.grey,
                            fontSize: 14,
                          ),
                        ),
                      ],
                      if (_quantity >= 5) ...[
                        AppSpacing.gapH8,
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: const BoxDecoration(
                            color: AppColors.secondaryContainer,
                            borderRadius: AppRadius.borderXs,
                          ),
                          child: const Text('WHOLESALE RATE APPLIED', style: TextStyle(color: AppColors.onSecondaryContainer, fontSize: 9, fontWeight: FontWeight.bold)),
                        ),
                      ],
                    ],
                  ),
                  AppSpacing.gapV12,

                  // Wholesale Pricing Table
                  if (product.wholesaleTiers.isNotEmpty) ...[
                    Text('Wholesale B2B Tier Pricing', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
                    AppSpacing.gapV6,
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: isDark ? AppColors.surfaceDark : Colors.white,
                        borderRadius: AppRadius.borderMd,
                        border: Border.all(color: isDark ? AppColors.borderDark : AppColors.borderLight),
                      ),
                      child: Column(
                        children: product.wholesaleTiers.map((tier) {
                          final tierActive = _quantity >= tier.minQuantity && (tier.maxQuantity == null || _quantity <= tier.maxQuantity!);
                          return Padding(
                            padding: const EdgeInsets.symmetric(vertical: 4),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(
                                  tier.maxQuantity == null ? '${tier.minQuantity}+ Units' : '${tier.minQuantity} - ${tier.maxQuantity} Units',
                                  style: TextStyle(
                                    fontWeight: tierActive ? FontWeight.bold : FontWeight.normal,
                                    color: tierActive ? AppColors.secondary : null,
                                  ),
                                ),
                                Text(
                                  '${CurrencyFormatter.formatINR(tier.pricePerUnit)} / unit',
                                  style: TextStyle(
                                    fontWeight: tierActive ? FontWeight.bold : FontWeight.normal,
                                    color: tierActive ? AppColors.secondary : null,
                                  ),
                                ),
                              ],
                            ),
                          );
                        }).toList(),
                      ),
                    ),
                    AppSpacing.gapV16,
                  ],

                  // Digital Craft Passport Box
                  GestureDetector(
                    onTap: () => _showCraftPassportModal(context, product.passport),
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
                                  'DIGITAL CRAFT PASSPORT CERTIFICATE',
                                  style: TextStyle(color: Colors.white70, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 0.8),
                                ),
                                Text(
                                  product.passport.passportId,
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

                  // Craft Specifications Grid
                  Text('Craft Specifications & Provenance', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                  AppSpacing.gapV8,
                  _buildSpecRow('Raw Materials', product.material),
                  _buildSpecRow('Dimensions', product.dimensions),
                  _buildSpecRow('Weight', product.weight),
                  _buildSpecRow('Techniques', product.craftTechniques.join(', ')),
                  _buildSpecRow('Handcrafting Time', product.passport.handcraftHours),
                  _buildSpecRow('GI Cluster', product.passport.craftClusterName),
                  AppSpacing.gapV16,

                  // Heritage Description
                  Text('Artisan Story & Description', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                  AppSpacing.gapV6,
                  Text(
                    product.description,
                    style: theme.textTheme.bodyMedium?.copyWith(
                      height: 1.45,
                      color: isDark ? AppColors.textSecondaryDark : AppColors.textSecondaryLight,
                    ),
                  ),
                  AppSpacing.gapV24,

                  // Reviews List
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text('Verified Buyer Reviews (${product.reviews.length})', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                      TextButton(onPressed: () {}, child: const Text('See All')),
                    ],
                  ),
                  AppSpacing.gapV8,
                  ...product.reviews.map((rev) => AppCard(
                        margin: const EdgeInsets.only(bottom: 8),
                        padding: const EdgeInsets.all(12),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(rev.userName, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                                Row(
                                  children: [
                                    const Icon(Icons.star, color: Colors.amber, size: 14),
                                    Text(' ${rev.rating}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                                  ],
                                ),
                              ],
                            ),
                            Text('${rev.userLocation} · ${rev.date}', style: const TextStyle(fontSize: 10, color: Colors.grey)),
                            AppSpacing.gapV6,
                            Text(rev.comment, style: const TextStyle(fontSize: 12)),
                          ],
                        ),
                      )),
                  AppSpacing.gapV24,

                  // Related Crafts
                  Text('More from this Craft Cluster', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                  AppSpacing.gapV12,
                  SizedBox(
                    height: 220,
                    child: ListView.separated(
                      scrollDirection: Axis.horizontal,
                      itemCount: relatedProducts.length,
                      separatorBuilder: (_, __) => AppSpacing.gapH12,
                      itemBuilder: (context, index) {
                        final rel = relatedProducts[index];
                        return SizedBox(
                          width: 170,
                          child: CraftProductCard(
                            product: rel.toCraftProduct(),
                            onTap: () => context.push('/products/${rel.id}'),
                          ),
                        );
                      },
                    ),
                  ),
                  const SizedBox(height: 100),
                ],
              ),
            ),
          ),
        ],
      ),

      // Bottom Checkout / Add to Cart Bar
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
          child: Row(
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
                      onPressed: () {
                        if (_quantity > 1) {
                          setState(() => _quantity -= 1);
                        }
                      },
                    ),
                    Text('$_quantity', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                    IconButton(
                      icon: const Icon(Icons.add, size: 16),
                      onPressed: () {
                        setState(() => _quantity += 1);
                      },
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
                  onPressed: () {
                    ref.read(cartProvider.notifier).addToCart(product, quantity: _quantity);
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text('Added $_quantity item(s) to Cart!'),
                        action: SnackBarAction(
                          label: 'View Cart',
                          onPressed: () => context.push('/cart'),
                        ),
                      ),
                    );
                  },
                ),
              ),
              AppSpacing.gapH8,

              // Buy Now / RFQ Button
              Expanded(
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primary,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    shape: AppRadius.shapeMd,
                  ),
                  onPressed: () {
                    ref.read(cartProvider.notifier).addToCart(product, quantity: _quantity);
                    context.push('/checkout');
                  },
                  child: Text(
                    'Buy (${CurrencyFormatter.formatINR(totalPrice)})',
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSpecRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 130,
            child: Text(label, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.grey)),
          ),
          Expanded(
            child: Text(value, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500)),
          ),
        ],
      ),
    );
  }

  void _showCraftPassportModal(BuildContext context, CraftPassportData passport) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (context) {
        return DraggableScrollableSheet(
          initialChildSize: 0.75,
          maxChildSize: 0.9,
          minChildSize: 0.5,
          expand: false,
          builder: (context, scrollController) {
            return ListView(
              controller: scrollController,
              padding: AppSpacing.paddingAllLg,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Row(
                      children: [
                        Icon(Icons.verified, color: AppColors.success, size: 24),
                        SizedBox(width: 8),
                        Text('Craft Digital Passport', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                      ],
                    ),
                    IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.pop(context)),
                  ],
                ),
                AppSpacing.gapV12,
                Container(
                  padding: AppSpacing.paddingAllBase,
                  decoration: BoxDecoration(
                    color: AppColors.successContainer.withValues(alpha: 0.3),
                    borderRadius: AppRadius.borderMd,
                    border: Border.all(color: AppColors.success),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('PASSPORT ID: ${passport.passportId}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                      Text('GI Registration: ${passport.giRegistrationNumber}', style: const TextStyle(fontSize: 12)),
                      Text('Cluster: ${passport.craftClusterName}', style: const TextStyle(fontSize: 12)),
                      Text('Geo Coordinates: ${passport.geoCoordinates}', style: const TextStyle(fontSize: 12)),
                      Text('Provenance: ${passport.rawMaterialProvenance}', style: const TextStyle(fontSize: 12)),
                      Text('Handcrafting Effort: ${passport.handcraftHours}', style: const TextStyle(fontSize: 12)),
                      Text('Sustainability: ${passport.sustainabilityRating}', style: const TextStyle(fontSize: 12)),
                      Text('Guild Seal: ${passport.artisanSignature}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: AppColors.primary)),
                    ],
                  ),
                ),
                AppSpacing.gapV16,
                ElevatedButton.icon(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primary,
                    foregroundColor: Colors.white,
                  ),
                  icon: const Icon(Icons.share_outlined),
                  label: const Text('Share Digital Passport'),
                  onPressed: () {
                    Navigator.pop(context);
                    SocialShareSheet.show(
                      context,
                      title: 'Digital Craft Passport #${passport.passportId}',
                      subtitle: passport.craftClusterName,
                      deepLink: 'https://kalacart.in/passport/${passport.passportId}',
                      entityType: 'passport',
                    );
                  },
                ),
              ],
            );
          },
        );
      },
    );
  }
}
