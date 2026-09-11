import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/utils/currency_formatter.dart';
import '../../../core/widgets/app_card.dart';
import '../../../shared/models/seller_models.dart';
import '../../seller/data/seller_repository.dart';

class BuyerOrdersScreen extends ConsumerWidget {
  const BuyerOrdersScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final orders = ref.watch(sellerOrdersProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('My Handicraft Orders & Provenance'),
      ),
      body: orders.isEmpty
          ? const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.shopping_bag_outlined, size: 54, color: Colors.grey),
                  AppSpacing.gapV12,
                  Text('No orders yet', style: TextStyle(fontWeight: FontWeight.bold)),
                  AppSpacing.gapV4,
                  Text('Your purchases with verified digital passports will appear here.', style: TextStyle(color: Colors.grey)),
                ],
              ),
            )
          : ListView.separated(
              padding: AppSpacing.paddingAllBase,
              itemCount: orders.length,
              separatorBuilder: (_, __) => AppSpacing.gapV12,
              itemBuilder: (context, index) {
                final order = orders[index];
                return AppCard(
                  padding: AppSpacing.paddingAllBase,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(order.orderNumber, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                          _buildStatusBadge(order.status),
                        ],
                      ),
                      AppSpacing.gapV8,
                      ...order.items.map((item) => Padding(
                            padding: const EdgeInsets.symmetric(vertical: 2),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Expanded(
                                  child: Text(
                                    '${item.quantity}x ${item.productTitle}',
                                    style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 12),
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ),
                                Text(CurrencyFormatter.formatINR(item.totalPrice), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                              ],
                            ),
                          )),
                      AppSpacing.gapV8,
                      const Divider(height: 1),
                      AppSpacing.gapV8,

                      // Status Timeline
                      _buildTimelineRow(order.status),
                      AppSpacing.gapV12,

                      // Actions: View Craft Passport & Track
                      Row(
                        children: [
                          Expanded(
                            child: OutlinedButton.icon(
                              style: OutlinedButton.styleFrom(shape: AppRadius.shapeMd),
                              icon: const Icon(Icons.verified_outlined, size: 14, color: AppColors.success),
                              label: const Text('Digital Passport', style: TextStyle(fontSize: 11)),
                              onPressed: () => context.push('/passport/GI-IN-RAJ-2026-BP-0941'),
                            ),
                          ),
                          AppSpacing.gapH8,
                          Expanded(
                            child: ElevatedButton.icon(
                              style: ElevatedButton.styleFrom(
                                backgroundColor: AppColors.primary,
                                foregroundColor: Colors.white,
                                shape: AppRadius.shapeMd,
                              ),
                              icon: const Icon(Icons.local_shipping_outlined, size: 14),
                              label: const Text('Track Courier', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                              onPressed: () => _showTrackingModal(context, order),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                );
              },
            ),
    );
  }

  Widget _buildStatusBadge(OrderStatus status) {
    Color color;
    String label;
    switch (status) {
      case OrderStatus.pending:
        color = Colors.orange;
        label = 'PENDING ARTISAN ACCEPTANCE';
        break;
      case OrderStatus.accepted:
        color = Colors.blue;
        label = 'ACCEPTED · PACKING';
        break;
      case OrderStatus.processing:
        color = Colors.indigo;
        label = 'KILN & WEAVING IN PROGRESS';
        break;
      case OrderStatus.shipped:
        color = AppColors.primary;
        label = 'IN TRANSIT WITH COURIER';
        break;
      case OrderStatus.delivered:
        color = AppColors.success;
        label = 'DELIVERED & VERIFIED';
        break;
      case OrderStatus.cancelled:
        color = Colors.red;
        label = 'CANCELLED';
        break;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: AppRadius.borderXs,
      ),
      child: Text(label, style: TextStyle(color: color, fontSize: 9, fontWeight: FontWeight.bold)),
    );
  }

  Widget _buildTimelineRow(OrderStatus status) {
    return Row(
      children: [
        _buildTimelineDot('Ordered', true),
        Expanded(child: Container(height: 2, color: AppColors.primary)),
        _buildTimelineDot('Handcrafted', status != OrderStatus.pending),
        Expanded(child: Container(height: 2, color: status == OrderStatus.shipped || status == OrderStatus.delivered ? AppColors.primary : Colors.grey.shade300)),
        _buildTimelineDot('Shipped', status == OrderStatus.shipped || status == OrderStatus.delivered),
        Expanded(child: Container(height: 2, color: status == OrderStatus.delivered ? AppColors.success : Colors.grey.shade300)),
        _buildTimelineDot('Delivered', status == OrderStatus.delivered),
      ],
    );
  }

  Widget _buildTimelineDot(String label, bool isDone) {
    return Column(
      children: [
        Container(
          width: 10,
          height: 10,
          decoration: BoxDecoration(
            color: isDone ? AppColors.primary : Colors.grey.shade400,
            shape: BoxShape.circle,
          ),
        ),
        const SizedBox(height: 2),
        Text(label, style: TextStyle(fontSize: 8, color: isDone ? AppColors.primary : Colors.grey, fontWeight: FontWeight.bold)),
      ],
    );
  }

  void _showTrackingModal(BuildContext context, SellerOrder order) {
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
                  const Text('Live Courier Tracking', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.pop(context)),
                ],
              ),
              AppSpacing.gapV8,
              Text('Carrier: ${order.courierPartner ?? 'Delhivery Artisan Express'}', style: const TextStyle(fontWeight: FontWeight.bold)),
              Text('AWB Number: ${order.trackingNumber ?? 'AWB-IN-2026-99410'}', style: const TextStyle(fontSize: 12, color: AppColors.primary)),
              AppSpacing.gapV12,
              const Text('• Current Status: Package in transit from Jaipur Hub to Bengaluru Delivery Station.', style: TextStyle(fontSize: 12)),
              const Text('• Expected Delivery: Tomorrow before 5:00 PM.', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.success)),
              AppSpacing.gapV16,
            ],
          ),
        );
      },
    );
  }
}
