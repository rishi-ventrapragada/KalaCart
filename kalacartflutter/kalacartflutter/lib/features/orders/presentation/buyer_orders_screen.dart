import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/utils/currency_formatter.dart';
import '../../../core/widgets/app_card.dart';
import '../../../core/widgets/app_empty_state.dart';
import '../../../core/widgets/app_error_state.dart';
import '../../../core/widgets/app_image_placeholder.dart';
import '../../../core/widgets/app_loading_state.dart';
import '../../../shared/models/order_models.dart';
import '../../auth/data/supabase_auth_repository.dart';
import '../data/orders_repository.dart';

class BuyerOrdersScreen extends ConsumerWidget {
  const BuyerOrdersScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final ordersAsync = ref.watch(buyerOrdersProvider);

    Future<void> refresh() async {
      ref.invalidate(buyerOrdersProvider);
      try {
        await ref.read(buyerOrdersProvider.future);
      } catch (_) {
        // The error state below renders the failure.
      }
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('My Orders'),
      ),
      body: ordersAsync.when(
        loading: () => const AppLoadingState(message: 'Loading your orders...'),
        error: (e, _) => AppErrorState(
          message: authErrorMessage(e),
          onRetry: () => ref.invalidate(buyerOrdersProvider),
        ),
        data: (orders) {
          if (orders.isEmpty) {
            return RefreshIndicator(
              onRefresh: refresh,
              child: ListView(
                children: [
                  SizedBox(
                    height: MediaQuery.sizeOf(context).height * 0.7,
                    child: AppEmptyState(
                      icon: Icons.shopping_bag_outlined,
                      title: 'No orders yet',
                      message: 'Your purchases and their provenance passports will appear here.',
                      actionLabel: 'Explore Handicrafts',
                      onAction: () => context.go('/discovery'),
                    ),
                  ),
                ],
              ),
            );
          }
          return RefreshIndicator(
            onRefresh: refresh,
            child: ListView.separated(
              padding: AppSpacing.paddingAllBase,
              itemCount: orders.length,
              separatorBuilder: (_, __) => AppSpacing.gapV12,
              itemBuilder: (context, index) => _OrderCard(order: orders[index]),
            ),
          );
        },
      ),
    );
  }
}

class _OrderCard extends StatelessWidget {
  final OrderRecord order;

  const _OrderCard({required this.order});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final secondary = isDark ? AppColors.textTertiaryDark : AppColors.textSecondaryLight;
    final imageUrl = order.productImageUrl;
    final address = (order.shippingAddress ?? '').trim();
    final productId = order.productId;

    return AppCard(
      padding: AppSpacing.paddingAllBase,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(order.orderNumber, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
              _StatusBadge(status: order.status),
            ],
          ),
          AppSpacing.gapV4,
          Text(
            DateFormat('d MMM yyyy, h:mm a').format(order.createdAt.toLocal()),
            style: TextStyle(fontSize: 11, color: secondary),
          ),
          AppSpacing.gapV12,
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SizedBox(
                width: 56,
                height: 56,
                child: ClipRRect(
                  borderRadius: AppRadius.borderSm,
                  child: imageUrl == null
                      ? const AppImagePlaceholder(icon: Icons.palette_outlined)
                      : Image.network(
                          imageUrl,
                          fit: BoxFit.cover,
                          errorBuilder: (_, __, ___) => const AppImagePlaceholder(icon: Icons.palette_outlined),
                        ),
                ),
              ),
              AppSpacing.gapH12,
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '${order.productTitle ?? 'Craft item'} × ${order.quantity}',
                      style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    if ((order.sellerShopName ?? '').isNotEmpty) ...[
                      AppSpacing.gapV2,
                      Text(
                        'Sold by ${order.sellerShopName}',
                        style: TextStyle(fontSize: 11, color: secondary),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                    AppSpacing.gapV4,
                    Text(
                      '${CurrencyFormatter.formatINR(order.unitPrice)} × ${order.quantity} = ${CurrencyFormatter.formatINR(order.totalAmount)}',
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: AppColors.primary),
                    ),
                  ],
                ),
              ),
            ],
          ),
          if (address.isNotEmpty) ...[
            AppSpacing.gapV12,
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.location_on_outlined, size: 14, color: secondary),
                AppSpacing.gapH4,
                Expanded(
                  child: Text(
                    address,
                    style: TextStyle(fontSize: 11, color: secondary),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
          ],
          AppSpacing.gapV12,
          const Divider(height: 1),
          AppSpacing.gapV12,

          // Status Timeline
          _Timeline(status: order.status),
          AppSpacing.gapV12,

          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  style: OutlinedButton.styleFrom(shape: AppRadius.shapeMd),
                  icon: const Icon(Icons.verified_outlined, size: 14, color: AppColors.success),
                  label: const Text('Provenance Passport', style: TextStyle(fontSize: 11)),
                  onPressed: productId == null ? null : () => context.push('/passport/$productId'),
                ),
              ),
              if (productId != null) ...[
                AppSpacing.gapH8,
                Expanded(
                  child: ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      foregroundColor: Colors.white,
                      shape: AppRadius.shapeMd,
                    ),
                    icon: const Icon(Icons.shopping_bag_outlined, size: 14),
                    label: const Text('View Product', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                    onPressed: () => context.push('/products/$productId'),
                  ),
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  final OrderStatus status;

  const _StatusBadge({required this.status});

  @override
  Widget build(BuildContext context) {
    Color color;
    switch (status) {
      case OrderStatus.pending:
        color = Colors.orange;
        break;
      case OrderStatus.accepted:
        color = Colors.blue;
        break;
      case OrderStatus.processing:
        color = Colors.indigo;
        break;
      case OrderStatus.shipped:
        color = AppColors.primary;
        break;
      case OrderStatus.delivered:
        color = AppColors.success;
        break;
      case OrderStatus.cancelled:
        color = AppColors.error;
        break;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: AppRadius.borderXs,
      ),
      child: Text(
        status.label.toUpperCase(),
        style: TextStyle(color: color, fontSize: 9, fontWeight: FontWeight.bold, letterSpacing: 0.5),
      ),
    );
  }
}

class _Timeline extends StatelessWidget {
  final OrderStatus status;

  const _Timeline({required this.status});

  @override
  Widget build(BuildContext context) {
    if (status == OrderStatus.cancelled) {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: AppColors.errorContainer.withValues(alpha: 0.4),
          borderRadius: AppRadius.borderSm,
        ),
        child: const Row(
          children: [
            Icon(Icons.cancel_outlined, size: 16, color: AppColors.error),
            AppSpacing.gapH8,
            Expanded(
              child: Text(
                'This order was cancelled.',
                style: TextStyle(fontSize: 12, color: AppColors.error, fontWeight: FontWeight.w600),
              ),
            ),
          ],
        ),
      );
    }

    final step = _stepFor(status);
    final inactive = Colors.grey.shade300;
    return Row(
      children: [
        _Dot(label: 'Ordered', isDone: step >= 0),
        Expanded(child: Container(height: 2, color: step >= 1 ? AppColors.primary : inactive)),
        _Dot(label: 'Accepted', isDone: step >= 1),
        Expanded(child: Container(height: 2, color: step >= 2 ? AppColors.primary : inactive)),
        _Dot(label: 'Crafting', isDone: step >= 2),
        Expanded(child: Container(height: 2, color: step >= 3 ? AppColors.primary : inactive)),
        _Dot(label: 'Shipped', isDone: step >= 3),
        Expanded(child: Container(height: 2, color: step >= 4 ? AppColors.success : inactive)),
        _Dot(label: 'Delivered', isDone: step >= 4, doneColor: AppColors.success),
      ],
    );
  }

  static int _stepFor(OrderStatus status) {
    switch (status) {
      case OrderStatus.pending:
        return 0;
      case OrderStatus.accepted:
        return 1;
      case OrderStatus.processing:
        return 2;
      case OrderStatus.shipped:
        return 3;
      case OrderStatus.delivered:
        return 4;
      case OrderStatus.cancelled:
        return -1;
    }
  }
}

class _Dot extends StatelessWidget {
  final String label;
  final bool isDone;
  final Color doneColor;

  const _Dot({required this.label, required this.isDone, this.doneColor = AppColors.primary});

  @override
  Widget build(BuildContext context) {
    final color = isDone ? doneColor : Colors.grey;
    return Column(
      children: [
        Container(
          width: 10,
          height: 10,
          decoration: BoxDecoration(
            color: isDone ? doneColor : Colors.grey.shade400,
            shape: BoxShape.circle,
          ),
        ),
        const SizedBox(height: 2),
        Text(label, style: TextStyle(fontSize: 8, color: color, fontWeight: FontWeight.bold)),
      ],
    );
  }
}
