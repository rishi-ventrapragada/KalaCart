import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/utils/currency_formatter.dart';
import '../../../core/widgets/app_card.dart';
import '../../../shared/models/seller_models.dart';
import '../../seller/data/seller_repository.dart';

class SellerOrdersScreen extends ConsumerStatefulWidget {
  const SellerOrdersScreen({super.key});

  @override
  ConsumerState<SellerOrdersScreen> createState() => _SellerOrdersScreenState();
}

class _SellerOrdersScreenState extends ConsumerState<SellerOrdersScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 6, vsync: this);
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
    final orders = ref.watch(sellerOrdersProvider);

    final pending = orders.where((o) => o.status == OrderStatus.pending).toList();
    final accepted = orders.where((o) => o.status == OrderStatus.accepted).toList();
    final processing = orders.where((o) => o.status == OrderStatus.processing).toList();
    final shipped = orders.where((o) => o.status == OrderStatus.shipped).toList();
    final delivered = orders.where((o) => o.status == OrderStatus.delivered).toList();
    final cancelled = orders.where((o) => o.status == OrderStatus.cancelled).toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Artisan Order Fulfillment'),
        bottom: TabBar(
          controller: _tabController,
          isScrollable: true,
          labelColor: AppColors.primary,
          unselectedLabelColor: isDark ? AppColors.textSecondaryDark : AppColors.textSecondaryLight,
          indicatorColor: AppColors.primary,
          tabs: [
            Tab(text: 'Pending (${pending.length})'),
            Tab(text: 'Accepted (${accepted.length})'),
            Tab(text: 'In Kiln (${processing.length})'),
            Tab(text: 'Shipped (${shipped.length})'),
            Tab(text: 'Delivered (${delivered.length})'),
            Tab(text: 'Cancelled (${cancelled.length})'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildOrderList(pending, OrderStatus.pending),
          _buildOrderList(accepted, OrderStatus.accepted),
          _buildOrderList(processing, OrderStatus.processing),
          _buildOrderList(shipped, OrderStatus.shipped),
          _buildOrderList(delivered, OrderStatus.delivered),
          _buildOrderList(cancelled, OrderStatus.cancelled),
        ],
      ),
    );
  }

  Widget _buildOrderList(List<SellerOrder> list, OrderStatus targetStatus) {
    if (list.isEmpty) {
      return const Center(
        child: Text('No orders in this status category.'),
      );
    }

    return ListView.separated(
      padding: AppSpacing.paddingAllBase,
      itemCount: list.length,
      separatorBuilder: (_, __) => AppSpacing.gapV12,
      itemBuilder: (context, index) {
        final order = list[index];
        return AppCard(
          padding: AppSpacing.paddingAllBase,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(order.orderNumber, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                  Text(
                    CurrencyFormatter.formatINR(order.totalAmount),
                    style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary, fontSize: 14),
                  ),
                ],
              ),
              AppSpacing.gapV6,
              Text('Buyer: ${order.buyerName} · ${order.buyerPhone}', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
              Text('Address: ${order.buyerAddress}', style: const TextStyle(fontSize: 11, color: Colors.grey)),
              AppSpacing.gapV8,
              ...order.items.map((it) => Text('• ${it.quantity}x ${it.productTitle}', style: const TextStyle(fontSize: 12))),
              AppSpacing.gapV12,

              // Action Buttons based on status
              if (order.status == OrderStatus.pending) ...[
                Row(
                  children: [
                    Expanded(
                      child: ElevatedButton(
                        style: ElevatedButton.styleFrom(backgroundColor: AppColors.primary, foregroundColor: Colors.white),
                        onPressed: () {
                          ref.read(sellerOrdersProvider.notifier).updateOrderStatus(order.id, OrderStatus.accepted);
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(content: Text('Order ${order.orderNumber} accepted!')),
                          );
                        },
                        child: const Text('Accept & Confirm'),
                      ),
                    ),
                    AppSpacing.gapH8,
                    OutlinedButton(
                      onPressed: () => ref.read(sellerOrdersProvider.notifier).cancelOrder(order.id),
                      child: const Text('Decline'),
                    ),
                  ],
                ),
              ] else if (order.status == OrderStatus.accepted) ...[
                ElevatedButton.icon(
                  style: ElevatedButton.styleFrom(backgroundColor: AppColors.secondary, foregroundColor: Colors.white),
                  icon: const Icon(Icons.handyman_outlined, size: 16),
                  label: const Text('Mark Crafting in Progress (Kiln/Loom)'),
                  onPressed: () {
                    ref.read(sellerOrdersProvider.notifier).updateOrderStatus(order.id, OrderStatus.processing);
                  },
                ),
              ] else if (order.status == OrderStatus.processing) ...[
                ElevatedButton.icon(
                  style: ElevatedButton.styleFrom(backgroundColor: AppColors.primary, foregroundColor: Colors.white),
                  icon: const Icon(Icons.local_shipping_outlined, size: 16),
                  label: const Text('Print Label & Dispatch Courier'),
                  onPressed: () {
                    ref.read(sellerOrdersProvider.notifier).updateOrderStatus(
                          order.id,
                          OrderStatus.shipped,
                          tracking: 'DELHIVERY-AWB-998812',
                          courier: 'Delhivery Express SafePack',
                        );
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Shipping label generated & dispatched!')),
                    );
                  },
                ),
              ] else if (order.status == OrderStatus.shipped) ...[
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton.icon(
                        icon: const Icon(Icons.check_circle_outline, color: AppColors.success, size: 16),
                        label: const Text('Mark Delivered', style: TextStyle(color: AppColors.success)),
                        onPressed: () {
                          ref.read(sellerOrdersProvider.notifier).updateOrderStatus(order.id, OrderStatus.delivered);
                        },
                      ),
                    ),
                  ],
                ),
              ],
            ],
          ),
        );
      },
    );
  }
}
