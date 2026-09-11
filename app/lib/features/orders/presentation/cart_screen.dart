import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/utils/currency_formatter.dart';
import '../../../core/widgets/app_card.dart';
import '../../../core/widgets/app_empty_state.dart';
import '../../../core/widgets/app_image_placeholder.dart';
import '../../products/data/cart_provider.dart';

class CartScreen extends ConsumerWidget {
  const CartScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final cart = ref.watch(cartProvider);
    final subtotal = ref.watch(cartSubtotalProvider);
    final totalItems = ref.watch(cartItemCountProvider);
    final deliveryFee = ref.watch(cartDeliveryFeeProvider);
    final totalAmount = ref.watch(cartTotalProvider);
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        title: Text(totalItems == 1 ? 'My Craft Cart (1 item)' : 'My Craft Cart ($totalItems items)'),
        actions: [
          if (cart.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.delete_sweep_outlined),
              tooltip: 'Clear Cart',
              onPressed: () => ref.read(cartProvider.notifier).clearCart(),
            ),
        ],
      ),
      body: cart.isEmpty
          ? AppEmptyState(
              icon: Icons.shopping_basket_outlined,
              title: 'Your craft cart is empty',
              message: 'Explore handmade treasures directly from Indian artisans.',
              actionLabel: 'Explore Handicrafts',
              onAction: () => context.go('/discovery'),
            )
          : ListView(
              padding: AppSpacing.paddingAllBase,
              children: [
                // Free Shipping Progress
                Container(
                  padding: AppSpacing.paddingAllBase,
                  decoration: BoxDecoration(
                    color: AppColors.primaryContainer.withValues(alpha: 0.3),
                    borderRadius: AppRadius.borderMd,
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.local_shipping_outlined, color: AppColors.primary, size: 20),
                      AppSpacing.gapH10,
                      Expanded(
                        child: Text(
                          deliveryFee == 0
                              ? 'You unlocked free delivery across India!'
                              : 'Add ${CurrencyFormatter.formatINR(kFreeDeliveryThreshold - subtotal)} more for free delivery.',
                          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.primary),
                        ),
                      ),
                    ],
                  ),
                ),
                AppSpacing.gapV16,

                // Cart Items List
                ...cart.map((item) {
                  final product = item.product;
                  final imageUrl = product.primaryImageUrl;
                  final atStockCap = item.quantity >= product.stock;
                  return AppCard(
                    margin: const EdgeInsets.only(bottom: 12),
                    padding: AppSpacing.paddingAllBase,
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Thumbnail
                        SizedBox(
                          width: 80,
                          height: 80,
                          child: ClipRRect(
                            borderRadius: AppRadius.borderMd,
                            child: imageUrl == null
                                ? const AppImagePlaceholder(icon: Icons.palette_outlined)
                                : Image.network(
                                    imageUrl,
                                    fit: BoxFit.cover,
                                    errorBuilder: (_, __, ___) =>
                                        const AppImagePlaceholder(icon: Icons.palette_outlined),
                                  ),
                          ),
                        ),
                        AppSpacing.gapH12,
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Expanded(
                                    child: Text(
                                      product.title,
                                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                                      maxLines: 2,
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ),
                                  InkWell(
                                    onTap: () => ref.read(cartProvider.notifier).removeFromCart(product.id),
                                    borderRadius: AppRadius.borderSm,
                                    child: const Padding(
                                      padding: EdgeInsets.all(2),
                                      child: Icon(Icons.close_rounded, size: 18, color: Colors.grey),
                                    ),
                                  ),
                                ],
                              ),
                              AppSpacing.gapV4,
                              Text(
                                '${product.artisanName} · ${product.region}',
                                style: TextStyle(
                                  fontSize: 11,
                                  color: isDark ? AppColors.textTertiaryDark : AppColors.textSecondaryLight,
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                              AppSpacing.gapV6,
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        CurrencyFormatter.formatINR(item.unitPrice),
                                        style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary),
                                      ),
                                      if (item.isWholesaleRate)
                                        const Text(
                                          'Wholesale rate',
                                          style: TextStyle(
                                            fontSize: 10,
                                            color: AppColors.secondary,
                                            fontWeight: FontWeight.w600,
                                          ),
                                        ),
                                    ],
                                  ),
                                  // Quantity +/- Controls
                                  Container(
                                    decoration: BoxDecoration(
                                      border: Border.all(color: Colors.grey.shade400),
                                      borderRadius: AppRadius.borderSm,
                                    ),
                                    child: Row(
                                      children: [
                                        InkWell(
                                          onTap: () => ref
                                              .read(cartProvider.notifier)
                                              .updateQuantity(product.id, item.quantity - 1),
                                          child: const Padding(
                                            padding: EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                            child: Icon(Icons.remove, size: 14),
                                          ),
                                        ),
                                        Padding(
                                          padding: const EdgeInsets.symmetric(horizontal: 6),
                                          child: Text(
                                            '${item.quantity}',
                                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                                          ),
                                        ),
                                        InkWell(
                                          onTap: atStockCap
                                              ? null
                                              : () => ref
                                                  .read(cartProvider.notifier)
                                                  .updateQuantity(product.id, item.quantity + 1),
                                          child: Padding(
                                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                            child: Icon(
                                              Icons.add,
                                              size: 14,
                                              color: atStockCap ? Colors.grey.shade400 : null,
                                            ),
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                ],
                              ),
                              if (atStockCap) ...[
                                AppSpacing.gapV4,
                                Text(
                                  'Only ${product.stock} in stock',
                                  style: const TextStyle(fontSize: 10, color: AppColors.warning),
                                ),
                              ],
                            ],
                          ),
                        ),
                      ],
                    ),
                  );
                }),
                AppSpacing.gapV16,

                // Price Summary Breakdown
                AppCard(
                  padding: AppSpacing.paddingAllBase,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Order Summary', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                      AppSpacing.gapV8,
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text('Subtotal', style: TextStyle(fontSize: 13)),
                          Text(
                            CurrencyFormatter.formatINR(subtotal),
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                          ),
                        ],
                      ),
                      AppSpacing.gapV4,
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text('Packaging & Delivery', style: TextStyle(fontSize: 13)),
                          Text(
                            deliveryFee == 0 ? 'FREE' : CurrencyFormatter.formatINR(deliveryFee),
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 13,
                              color: deliveryFee == 0 ? AppColors.success : null,
                            ),
                          ),
                        ],
                      ),
                      AppSpacing.gapV8,
                      const Divider(height: 1),
                      AppSpacing.gapV8,
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text('Total', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                          Text(
                            CurrencyFormatter.formatINR(totalAmount),
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: AppColors.primary),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                AppSpacing.gapV24,

                // Checkout Button
                SizedBox(
                  width: double.infinity,
                  height: 48,
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      foregroundColor: Colors.white,
                      shape: AppRadius.shapeMd,
                    ),
                    onPressed: cart.isEmpty ? null : () => context.push('/checkout'),
                    child: Text(
                      'Proceed to Checkout (${CurrencyFormatter.formatINR(totalAmount)})',
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                    ),
                  ),
                ),
                AppSpacing.gapV32,
              ],
            ),
    );
  }
}
