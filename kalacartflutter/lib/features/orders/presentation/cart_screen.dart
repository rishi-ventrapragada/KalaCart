import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/utils/currency_formatter.dart';
import '../../../core/widgets/app_button.dart';
import '../../../core/widgets/app_card.dart';
import '../../products/data/buyer_catalog_repository.dart';

class CartScreen extends ConsumerWidget {
  const CartScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final cart = ref.watch(cartProvider);
    final subtotal = ref.watch(cartSubtotalProvider);
    final totalItems = ref.watch(cartItemCountProvider);
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    const deliveryFee = 150.0;
    final totalAmount = subtotal > 0 ? subtotal + (subtotal > 3000 ? 0 : deliveryFee) : 0.0;

    return Scaffold(
      appBar: AppBar(
        title: Text('My Craft Cart ($totalItems items)'),
        actions: [
          if (cart.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.delete_sweep_outlined),
              tooltip: 'Clear Cart',
              onPressed: () {
                ref.read(cartProvider.notifier).clearCart();
              },
            ),
        ],
      ),
      body: cart.isEmpty
          ? Center(
              child: Padding(
                padding: AppSpacing.paddingAllXl,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.shopping_basket_outlined, size: 64, color: Colors.grey),
                    AppSpacing.gapV16,
                    Text('Your craft cart is empty', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                    AppSpacing.gapV8,
                    const Text('Explore GI-certified handmade treasures directly from Indian artisans.', textAlign: TextAlign.center, style: TextStyle(color: Colors.grey)),
                    AppSpacing.gapV24,
                    AppButton(
                      label: 'Explore Handicrafts',
                      icon: Icons.explore_rounded,
                      onPressed: () => context.go('/discovery'),
                    ),
                  ],
                ),
              ),
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
                          subtotal > 3000 ? '🎉 You unlocked Free Artisanal Delivery across India!' : 'Add ${CurrencyFormatter.formatINR(3000 - subtotal)} more for Free Shipping!',
                          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.primary),
                        ),
                      ),
                    ],
                  ),
                ),
                AppSpacing.gapV16,

                // Cart Items List
                ...cart.map((item) {
                  return AppCard(
                    margin: const EdgeInsets.only(bottom: 12),
                    padding: AppSpacing.paddingAllBase,
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Thumbnail
                        Container(
                          width: 80,
                          height: 80,
                          decoration: BoxDecoration(
                            color: AppColors.primary.withValues(alpha: 0.1),
                            borderRadius: AppRadius.borderMd,
                          ),
                          child: const Center(
                            child: Icon(Icons.palette_outlined, size: 36, color: AppColors.primary),
                          ),
                        ),
                        AppSpacing.gapH12,
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                item.product.title,
                                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                                maxLines: 2,
                                overflow: TextOverflow.ellipsis,
                              ),
                              AppSpacing.gapV4,
                              Text(
                                '${item.product.artisanName} · ${item.product.villageLocation}',
                                style: TextStyle(fontSize: 11, color: isDark ? AppColors.textTertiaryDark : AppColors.textSecondaryLight),
                              ),
                              AppSpacing.gapV6,
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Text(
                                    CurrencyFormatter.formatINR(item.unitPrice),
                                    style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary),
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
                                          onTap: () => ref.read(cartProvider.notifier).updateQuantity(item.product.id, item.quantity - 1),
                                          child: const Padding(
                                            padding: EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                            child: Icon(Icons.remove, size: 14),
                                          ),
                                        ),
                                        Padding(
                                          padding: const EdgeInsets.symmetric(horizontal: 6),
                                          child: Text('${item.quantity}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                                        ),
                                        InkWell(
                                          onTap: () => ref.read(cartProvider.notifier).updateQuantity(item.product.id, item.quantity + 1),
                                          child: const Padding(
                                            padding: EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                            child: Icon(Icons.add, size: 14),
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                ],
                              ),
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
                          Text(CurrencyFormatter.formatINR(subtotal), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                        ],
                      ),
                      AppSpacing.gapV4,
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text('Artisan Safe Packaging & Courier', style: TextStyle(fontSize: 13)),
                          Text(subtotal > 3000 ? 'FREE' : CurrencyFormatter.formatINR(deliveryFee), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppColors.success)),
                        ],
                      ),
                      AppSpacing.gapV8,
                      const Divider(height: 1),
                      AppSpacing.gapV8,
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text('Total (Inclusive of all taxes)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                          Text(CurrencyFormatter.formatINR(totalAmount), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: AppColors.primary)),
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
                    onPressed: () => context.push('/checkout'),
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
