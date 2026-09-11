import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/utils/currency_formatter.dart';
import '../../../core/widgets/app_card.dart';
import '../../../core/widgets/app_empty_state.dart';
import '../../../core/widgets/app_error_state.dart';
import '../../../core/widgets/app_skeleton.dart';
import '../../../shared/models/order_models.dart';
import '../../auth/data/supabase_auth_repository.dart';
import '../data/orders_repository.dart';

class SellerOrdersScreen extends ConsumerStatefulWidget {
  const SellerOrdersScreen({super.key});

  @override
  ConsumerState<SellerOrdersScreen> createState() => _SellerOrdersScreenState();
}

class _SellerOrdersScreenState extends ConsumerState<SellerOrdersScreen> with SingleTickerProviderStateMixin {
  static const _tabs = OrderStatus.values;

  late TabController _tabController;
  final Set<String> _busyOrderIds = {};

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: _tabs.length, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _refresh() async {
    ref.invalidate(sellerOrdersProvider);
    try {
      await ref.read(sellerOrdersProvider.future);
    } catch (_) {
      // The list renders its own error state.
    }
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

  Future<void> _updateStatus(OrderRecord order, OrderStatus next, {String? successMessage}) async {
    setState(() => _busyOrderIds.add(order.id));
    try {
      await ref.read(ordersRepositoryProvider).updateStatus(order.id, next);
      ref.invalidate(sellerOrdersProvider);
      _showSnack(successMessage ?? 'Order ${order.orderNumber} marked ${next.label.toLowerCase()}.');
    } catch (e) {
      _showSnack(authErrorMessage(e), isError: true);
    } finally {
      if (mounted) setState(() => _busyOrderIds.remove(order.id));
    }
  }

  Future<void> _declineOrder(OrderRecord order) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Decline this order?'),
        content: Text(
          'Order ${order.orderNumber} for ${order.quantity} × ${order.productTitle ?? 'craft product'} will be cancelled. The buyer will see it as cancelled.',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.of(dialogContext).pop(false), child: const Text('Keep order')),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.error, foregroundColor: Colors.white),
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: const Text('Decline'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    await _updateStatus(order, OrderStatus.cancelled, successMessage: 'Order ${order.orderNumber} declined.');
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final ordersAsync = ref.watch(sellerOrdersProvider);
    final orders = ordersAsync.valueOrNull;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Order Fulfilment'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            tooltip: 'Refresh',
            onPressed: _refresh,
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          isScrollable: true,
          tabAlignment: TabAlignment.start,
          labelColor: AppColors.primary,
          unselectedLabelColor: isDark ? AppColors.textSecondaryDark : AppColors.textSecondaryLight,
          indicatorColor: AppColors.primary,
          tabs: _tabs.map((status) {
            final count = orders?.where((o) => o.status == status).length;
            return Tab(text: count == null ? status.label : '${status.label} ($count)');
          }).toList(),
        ),
      ),
      body: ordersAsync.when(
        loading: () => ListView.separated(
          padding: AppSpacing.paddingAllBase,
          itemCount: 4,
          separatorBuilder: (_, __) => AppSpacing.gapV12,
          itemBuilder: (_, __) => const AppSkeleton(height: 170, borderRadius: AppRadius.borderMd),
        ),
        error: (e, _) => AppErrorState(
          message: authErrorMessage(e),
          onRetry: () => ref.invalidate(sellerOrdersProvider),
        ),
        data: (all) => TabBarView(
          controller: _tabController,
          children: _tabs.map((status) {
            final list = all.where((o) => o.status == status).toList();
            return _buildOrderList(list, status, theme, isDark);
          }).toList(),
        ),
      ),
    );
  }

  Widget _buildOrderList(List<OrderRecord> list, OrderStatus status, ThemeData theme, bool isDark) {
    return RefreshIndicator(
      onRefresh: _refresh,
      child: list.isEmpty
          ? ListView(
              padding: AppSpacing.paddingAllBase,
              children: [
                AppEmptyState(
                  icon: Icons.receipt_long_outlined,
                  title: 'No ${status.label.toLowerCase()} orders',
                  message: status == OrderStatus.pending
                      ? 'New orders from buyers will appear here for you to accept.'
                      : 'Orders move here as you update their status.',
                ),
              ],
            )
          : ListView.separated(
              padding: AppSpacing.paddingAllBase,
              itemCount: list.length,
              separatorBuilder: (_, __) => AppSpacing.gapV12,
              itemBuilder: (context, index) => _buildOrderCard(list[index], theme, isDark),
            ),
    );
  }

  Widget _buildOrderCard(OrderRecord order, ThemeData theme, bool isDark) {
    final isBusy = _busyOrderIds.contains(order.id);
    final secondary = isDark ? AppColors.textSecondaryDark : AppColors.textSecondaryLight;
    final paymentPaid = order.paymentStatus.toLowerCase() == 'paid';

    return AppCard(
      padding: AppSpacing.paddingAllBase,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Text(order.orderNumber, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                  if (order.isWholesale) ...[
                    AppSpacing.gapH8,
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: const BoxDecoration(
                        color: AppColors.secondaryContainer,
                        borderRadius: AppRadius.borderXs,
                      ),
                      child: const Text(
                        'WHOLESALE',
                        style: TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: AppColors.onSecondaryContainer),
                      ),
                    ),
                  ],
                ],
              ),
              Text(
                CurrencyFormatter.formatINR(order.totalAmount),
                style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary, fontSize: 14),
              ),
            ],
          ),
          AppSpacing.gapV4,
          Text(
            DateFormat('d MMM yyyy, h:mm a').format(order.createdAt.toLocal()),
            style: theme.textTheme.bodySmall?.copyWith(fontSize: 11, color: secondary),
          ),
          AppSpacing.gapV8,
          Text(
            '${order.quantity} × ${order.productTitle ?? 'Craft product'} @ ${CurrencyFormatter.formatINR(order.unitPrice)}',
            style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
          AppSpacing.gapV8,
          const Divider(height: 1),
          AppSpacing.gapV8,
          _InfoRow(icon: Icons.person_outline, text: order.buyerName ?? 'Buyer'),
          if ((order.buyerPhone ?? '').trim().isNotEmpty) ...[
            AppSpacing.gapV4,
            _InfoRow(icon: Icons.phone_outlined, text: order.buyerPhone!.trim()),
          ],
          if ((order.shippingAddress ?? '').trim().isNotEmpty) ...[
            AppSpacing.gapV4,
            _InfoRow(icon: Icons.location_on_outlined, text: order.shippingAddress!.trim(), maxLines: 3),
          ],
          AppSpacing.gapV4,
          _InfoRow(
            icon: paymentPaid ? Icons.verified_outlined : Icons.schedule_outlined,
            text: 'Payment: ${order.paymentStatus}',
            color: paymentPaid ? AppColors.success : AppColors.warning,
          ),
          AppSpacing.gapV12,
          _buildActions(order, isBusy),
        ],
      ),
    );
  }

  Widget _buildActions(OrderRecord order, bool isBusy) {
    if (isBusy) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(8),
          child: SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2)),
        ),
      );
    }

    switch (order.status) {
      case OrderStatus.pending:
        return Row(
          children: [
            Expanded(
              child: ElevatedButton.icon(
                style: ElevatedButton.styleFrom(backgroundColor: AppColors.primary, foregroundColor: Colors.white),
                icon: const Icon(Icons.check_rounded, size: 16),
                label: const Text('Accept & Confirm'),
                onPressed: () => _updateStatus(order, OrderStatus.accepted, successMessage: 'Order ${order.orderNumber} accepted.'),
              ),
            ),
            AppSpacing.gapH8,
            OutlinedButton(
              style: OutlinedButton.styleFrom(foregroundColor: AppColors.error),
              onPressed: () => _declineOrder(order),
              child: const Text('Decline'),
            ),
          ],
        );
      case OrderStatus.accepted:
        return ElevatedButton.icon(
          style: ElevatedButton.styleFrom(backgroundColor: AppColors.secondary, foregroundColor: Colors.white),
          icon: const Icon(Icons.handyman_outlined, size: 16),
          label: const Text('Mark crafting in progress'),
          onPressed: () => _updateStatus(order, OrderStatus.processing),
        );
      case OrderStatus.processing:
        return ElevatedButton.icon(
          style: ElevatedButton.styleFrom(backgroundColor: AppColors.primary, foregroundColor: Colors.white),
          icon: const Icon(Icons.local_shipping_outlined, size: 16),
          label: const Text('Mark as shipped'),
          onPressed: () => _updateStatus(order, OrderStatus.shipped),
        );
      case OrderStatus.shipped:
        return OutlinedButton.icon(
          style: OutlinedButton.styleFrom(foregroundColor: AppColors.success),
          icon: const Icon(Icons.check_circle_outline, size: 16),
          label: const Text('Mark delivered'),
          onPressed: () => _updateStatus(order, OrderStatus.delivered),
        );
      case OrderStatus.delivered:
        return const _StatusNote(icon: Icons.check_circle, color: AppColors.success, text: 'Delivered to buyer');
      case OrderStatus.cancelled:
        return const _StatusNote(icon: Icons.cancel_outlined, color: AppColors.error, text: 'Order cancelled');
    }
  }
}

class _InfoRow extends StatelessWidget {
  final IconData icon;
  final String text;
  final int maxLines;
  final Color? color;

  const _InfoRow({required this.icon, required this.text, this.maxLines = 1, this.color});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 14, color: color ?? theme.colorScheme.onSurface.withValues(alpha: 0.6)),
        AppSpacing.gapH6,
        Expanded(
          child: Text(
            text,
            maxLines: maxLines,
            overflow: TextOverflow.ellipsis,
            style: theme.textTheme.bodySmall?.copyWith(fontSize: 12, color: color),
          ),
        ),
      ],
    );
  }
}

class _StatusNote extends StatelessWidget {
  final IconData icon;
  final Color color;
  final String text;

  const _StatusNote({required this.icon, required this.color, required this.text});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, size: 16, color: color),
        AppSpacing.gapH6,
        Text(text, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: color)),
      ],
    );
  }
}
