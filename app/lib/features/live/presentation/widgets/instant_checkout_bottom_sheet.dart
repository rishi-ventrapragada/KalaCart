import 'package:flutter/material.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_radius.dart';
import '../../../../core/constants/app_spacing.dart';
import '../../../../core/utils/currency_formatter.dart';
import '../../domain/live_session_model.dart';

class InstantCheckoutBottomSheet extends StatefulWidget {
  final LiveProductItem product;
  final String artisanName;
  final VoidCallback onOrderCompleted;

  const InstantCheckoutBottomSheet({
    super.key,
    required this.product,
    required this.artisanName,
    required this.onOrderCompleted,
  });

  static void show(
    BuildContext context, {
    required LiveProductItem product,
    required String artisanName,
    required VoidCallback onOrderCompleted,
  }) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (context) => InstantCheckoutBottomSheet(
        product: product,
        artisanName: artisanName,
        onOrderCompleted: onOrderCompleted,
      ),
    );
  }

  @override
  State<InstantCheckoutBottomSheet> createState() => _InstantCheckoutBottomSheetState();
}

class _InstantCheckoutBottomSheetState extends State<InstantCheckoutBottomSheet> {
  int _quantity = 1;
  bool _isProcessing = false;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final totalAmount = widget.product.price * _quantity;

    return Container(
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
      ),
      padding: EdgeInsets.fromLTRB(
        20,
        12,
        20,
        MediaQuery.of(context).viewInsets.bottom + 24,
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
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: const BoxDecoration(
                  color: Color(0xFFD32F2F),
                  borderRadius: AppRadius.borderSm,
                ),
                child: const Row(
                  children: [
                    Icon(Icons.bolt, color: Colors.white, size: 14),
                    SizedBox(width: 2),
                    Text('LIVE BUY', style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold)),
                  ],
                ),
              ),
              AppSpacing.gapH8,
              Text(
                'Instant Artisan Checkout',
                style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
              ),
            ],
          ),
          AppSpacing.gapV16,

          // Product preview
          Container(
            padding: AppSpacing.paddingAllBase,
            decoration: BoxDecoration(
              color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.4),
              borderRadius: AppRadius.borderMd,
            ),
            child: Row(
              children: [
                ClipRRect(
                  borderRadius: AppRadius.borderMd,
                  child: Image.network(
                    widget.product.imageUrl,
                    width: 60,
                    height: 60,
                    fit: BoxFit.cover,
                    errorBuilder: (_, __, ___) => Container(
                      width: 60,
                      height: 60,
                      color: Colors.grey.shade300,
                      child: const Icon(Icons.inventory_2_outlined),
                    ),
                  ),
                ),
                AppSpacing.gapH12,
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        widget.product.title,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                      ),
                      AppSpacing.gapV4,
                      Text(
                        'Direct from ${widget.artisanName}',
                        style: TextStyle(fontSize: 11, color: Colors.grey.shade600),
                      ),
                      AppSpacing.gapV4,
                      Text(
                        CurrencyFormatter.formatINR(widget.product.price),
                        style: const TextStyle(
                          color: AppColors.primary,
                          fontWeight: FontWeight.bold,
                          fontSize: 14,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          AppSpacing.gapV16,

          // Quantity Selector
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Quantity', style: TextStyle(fontWeight: FontWeight.w600)),
              Container(
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.grey.shade300),
                  borderRadius: AppRadius.borderPill,
                ),
                child: Row(
                  children: [
                    IconButton(
                      icon: const Icon(Icons.remove, size: 16),
                      onPressed: _quantity > 1 ? () => setState(() => _quantity--) : null,
                    ),
                    Text(
                      '$_quantity',
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                    ),
                    IconButton(
                      icon: const Icon(Icons.add, size: 16),
                      onPressed: () => setState(() => _quantity++),
                    ),
                  ],
                ),
              ),
            ],
          ),
          AppSpacing.gapV16,

          // Payment option
          const Text('Payment Method', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 12)),
          AppSpacing.gapV6,
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              border: Border.all(color: AppColors.primary.withValues(alpha: 0.5)),
              borderRadius: AppRadius.borderMd,
              color: AppColors.primaryContainer.withValues(alpha: 0.2),
            ),
            child: const Row(
              children: [
                Icon(Icons.shield_outlined, color: AppColors.primary, size: 18),
                SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'UPI Escrow (Instant Live Lock)',
                    style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
                  ),
                ),
                Icon(Icons.check_circle, color: AppColors.primary, size: 18),
              ],
            ),
          ),
          AppSpacing.gapV20,

          // Total & Pay Button
          Row(
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Total Amount', style: TextStyle(fontSize: 11, color: Colors.grey)),
                  Text(
                    CurrencyFormatter.formatINR(totalAmount),
                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppColors.primary),
                  ),
                ],
              ),
              AppSpacing.gapH16,
              Expanded(
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primary,
                    foregroundColor: Colors.white,
                    shape: AppRadius.shapePill,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                  ),
                  onPressed: _isProcessing ? null : _processLiveOrder,
                  child: _isProcessing
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                        )
                      : const Text('Pay & Lock Craft', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  void _processLiveOrder() async {
    setState(() => _isProcessing = true);
    await Future.delayed(const Duration(milliseconds: 1000));
    if (mounted) {
      Navigator.pop(context);
      widget.onOrderCompleted();
    }
  }
}
