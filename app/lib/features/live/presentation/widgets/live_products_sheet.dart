import 'package:flutter/material.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_radius.dart';
import '../../../../core/constants/app_spacing.dart';
import '../../../../core/utils/currency_formatter.dart';
import '../../domain/live_session_model.dart';

class LiveProductsSheet extends StatelessWidget {
  final List<LiveProductItem> products;
  final String? currentPinnedId;
  final bool isBroadcaster;
  final Function(LiveProductItem) onSelectProduct;
  final Function(LiveProductItem)? onPinProduct;
  final Function(LiveProductItem)? onInstantCheckout;

  const LiveProductsSheet({
    super.key,
    required this.products,
    this.currentPinnedId,
    required this.isBroadcaster,
    required this.onSelectProduct,
    this.onPinProduct,
    this.onInstantCheckout,
  });

  static void show(
    BuildContext context, {
    required List<LiveProductItem> products,
    String? currentPinnedId,
    required bool isBroadcaster,
    required Function(LiveProductItem) onSelectProduct,
    Function(LiveProductItem)? onPinProduct,
    Function(LiveProductItem)? onInstantCheckout,
  }) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (context) => LiveProductsSheet(
        products: products,
        currentPinnedId: currentPinnedId,
        isBroadcaster: isBroadcaster,
        onSelectProduct: onSelectProduct,
        onPinProduct: onPinProduct,
        onInstantCheckout: onInstantCheckout,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
      ),
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.65,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Center(
            child: Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: Colors.grey.withValues(alpha: 0.4),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          AppSpacing.gapV16,
          Row(
            children: [
              const Icon(Icons.shopping_bag_outlined, color: AppColors.primary, size: 22),
              AppSpacing.gapH8,
              Text(
                'Live Showcase Crafts (${products.length})',
                style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
              ),
            ],
          ),
          AppSpacing.gapV12,
          if (products.isEmpty)
            const Padding(
              padding: EdgeInsets.all(24.0),
              child: Center(
                child: Text('No products attached to this live session yet.'),
              ),
            )
          else
            Flexible(
              child: ListView.separated(
                shrinkWrap: true,
                itemCount: products.length,
                separatorBuilder: (_, __) => const Divider(height: 16),
                itemBuilder: (context, index) {
                  final product = products[index];
                  final isPinned = product.id == currentPinnedId;

                  return Row(
                    children: [
                      ClipRRect(
                        borderRadius: AppRadius.borderMd,
                        child: Image.network(
                          product.imageUrl,
                          width: 64,
                          height: 64,
                          fit: BoxFit.cover,
                          errorBuilder: (_, __, ___) => Container(
                            width: 64,
                            height: 64,
                            color: Colors.grey.shade200,
                            child: const Icon(Icons.image_outlined, color: Colors.grey),
                          ),
                        ),
                      ),
                      AppSpacing.gapH12,
                      Expanded(
                        child: InkWell(
                          onTap: () {
                            Navigator.pop(context);
                            onSelectProduct(product);
                          },
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                product.title,
                                maxLines: 2,
                                overflow: TextOverflow.ellipsis,
                                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                              ),
                              AppSpacing.gapV4,
                              Text(
                                CurrencyFormatter.formatINR(product.price),
                                style: const TextStyle(
                                  color: AppColors.primary,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 14,
                                ),
                              ),
                              if (product.wholesalePrice != null)
                                Text(
                                  'Wholesale MOQ price: ${CurrencyFormatter.formatINR(product.wholesalePrice!)}',
                                  style: TextStyle(fontSize: 11, color: Colors.grey.shade600),
                                ),
                            ],
                          ),
                        ),
                      ),
                      AppSpacing.gapH8,
                      if (isBroadcaster)
                        ElevatedButton.icon(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: isPinned ? Colors.grey.shade300 : AppColors.primary,
                            foregroundColor: isPinned ? Colors.black87 : Colors.white,
                            elevation: 0,
                            shape: AppRadius.shapePill,
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                          ),
                          icon: Icon(isPinned ? Icons.check : Icons.push_pin, size: 14),
                          label: Text(isPinned ? 'Pinned' : 'Pin', style: const TextStyle(fontSize: 11)),
                          onPressed: () {
                            Navigator.pop(context);
                            onPinProduct?.call(product);
                          },
                        )
                      else
                        ElevatedButton(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.primary,
                            foregroundColor: Colors.white,
                            shape: AppRadius.shapePill,
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          ),
                          onPressed: () {
                            Navigator.pop(context);
                            onInstantCheckout?.call(product);
                          },
                          child: const Text('Buy Now', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                        ),
                    ],
                  );
                },
              ),
            ),
        ],
      ),
    );
  }
}
