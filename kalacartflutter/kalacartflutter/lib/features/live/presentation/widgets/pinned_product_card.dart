import 'package:flutter/material.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_radius.dart';
import '../../../../core/constants/app_spacing.dart';
import '../../../../core/utils/currency_formatter.dart';
import '../../domain/live_session_model.dart';

class PinnedProductCard extends StatelessWidget {
  final LiveProductItem product;
  final VoidCallback onTap;
  final VoidCallback onBuyNow;
  final bool isBroadcaster;
  final VoidCallback? onUnpin;

  const PinnedProductCard({
    super.key,
    required this.product,
    required this.onTap,
    required this.onBuyNow,
    this.isBroadcaster = false,
    this.onUnpin,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 12),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: Colors.black.withValues(alpha: 0.85),
        borderRadius: AppRadius.borderLg,
        border: Border.all(color: AppColors.secondary.withValues(alpha: 0.8), width: 1.5),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.4),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Row(
        children: [
          // Product Thumbnail with Pinned Badge
          Stack(
            children: [
              ClipRRect(
                borderRadius: AppRadius.borderMd,
                child: Image.network(
                  product.imageUrl,
                  width: 58,
                  height: 58,
                  fit: BoxFit.cover,
                  errorBuilder: (_, __, ___) => Container(
                    width: 58,
                    height: 58,
                    color: Colors.grey.shade800,
                    child: const Icon(Icons.inventory_2_outlined, color: Colors.white70),
                  ),
                ),
              ),
              Positioned(
                top: 2,
                left: 2,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                  decoration: BoxDecoration(
                    color: AppColors.primary,
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: const Row(
                    children: [
                      Icon(Icons.push_pin, size: 8, color: Colors.white),
                      SizedBox(width: 2),
                      Text(
                        'FEATURED',
                        style: TextStyle(color: Colors.white, fontSize: 8, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
          AppSpacing.gapH12,

          // Product Details
          Expanded(
            child: InkWell(
              onTap: onTap,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    product.title,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  AppSpacing.gapV4,
                  Row(
                    children: [
                      Text(
                        CurrencyFormatter.formatINR(product.price),
                        style: const TextStyle(
                          color: AppColors.secondaryContainer,
                          fontSize: 14,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                      if (product.wholesalePrice != null) ...[
                        AppSpacing.gapH8,
                        Text(
                          'Bulk: ${CurrencyFormatter.formatINR(product.wholesalePrice!)}',
                          style: const TextStyle(
                            color: Colors.white60,
                            fontSize: 10,
                          ),
                        ),
                      ],
                    ],
                  ),
                ],
              ),
            ),
          ),

          AppSpacing.gapH8,

          // Action Button
          if (isBroadcaster)
            IconButton(
              icon: const Icon(Icons.close, color: Colors.white70, size: 20),
              tooltip: 'Unpin Craft',
              onPressed: onUnpin,
            )
          else
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                foregroundColor: Colors.white,
                shape: AppRadius.shapePill,
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                minimumSize: Size.zero,
                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
              ),
              onPressed: onBuyNow,
              child: const Text('Buy Now', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
            ),
        ],
      ),
    );
  }
}
