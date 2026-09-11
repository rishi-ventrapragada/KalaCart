import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/utils/currency_formatter.dart';
import '../../../core/widgets/app_button.dart';
import '../../../core/widgets/app_card.dart';
import '../../../shared/models/seller_models.dart';
import '../../../shared/services/user_role_service.dart';
import '../data/seller_repository.dart';

class SellerDashboardScreen extends ConsumerWidget {
  const SellerDashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final userRole = ref.watch(userRoleProvider);
    final analytics = ref.watch(sellerAnalyticsProvider);
    final storefrontConfig = ref.watch(storefrontConfigProvider);
    final orders = ref.watch(sellerOrdersProvider);
    final pendingOrders = orders.where((o) => o.status == OrderStatus.pending).toList();
    final rfqs = ref.watch(sellerRfqsProvider);
    final incomingRfqs = rfqs.where((r) => r.status == RfqStatus.incoming || r.status == RfqStatus.matched).toList();
    final products = ref.watch(sellerProductsProvider);

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(7),
              decoration: const BoxDecoration(
                color: AppColors.secondary,
                borderRadius: AppRadius.borderSm,
              ),
              child: const Icon(
                Icons.storefront_rounded,
                color: Colors.white,
                size: 20,
              ),
            ),
            AppSpacing.gapH12,
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Flexible(
                        child: Text(
                          storefrontConfig.storeName,
                          style: theme.textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.w800,
                            letterSpacing: -0.2,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      AppSpacing.gapH6,
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: const BoxDecoration(
                          color: AppColors.secondaryContainer,
                          borderRadius: AppRadius.borderXs,
                        ),
                        child: const Text(
                          'ARTISAN HUB',
                          style: TextStyle(
                            color: AppColors.onSecondaryContainer,
                            fontSize: 9,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ],
                  ),
                  Text(
                    '${userRole.craftCluster} · ${userRole.region}',
                    style: theme.textTheme.bodySmall?.copyWith(
                      fontSize: 11,
                      color: isDark ? AppColors.textTertiaryDark : AppColors.textSecondaryLight,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.share_outlined),
            tooltip: 'Share Storefront Link',
            onPressed: () => _showShareStorefrontDialog(context, storefrontConfig),
          ),
          IconButton(
            icon: const Icon(Icons.notifications_none_rounded),
            tooltip: 'Notifications',
            onPressed: () => context.push('/notifications'),
          ),
        ],
      ),
      body: ListView(
        padding: AppSpacing.paddingAllBase,
        children: [
          // Store Status & Live Workshop Bar
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: isDark ? AppColors.surfaceDark : Colors.white,
              borderRadius: AppRadius.borderMd,
              border: Border.all(
                color: isDark ? AppColors.borderDark : AppColors.borderLight,
              ),
            ),
            child: Row(
              children: [
                Container(
                  width: 10,
                  height: 10,
                  decoration: BoxDecoration(
                    color: storefrontConfig.isStoreOpen ? AppColors.success : Colors.grey,
                    shape: BoxShape.circle,
                  ),
                ),
                AppSpacing.gapH8,
                Text(
                  storefrontConfig.isStoreOpen ? 'Storefront Live & Accepting Orders' : 'Storefront Paused',
                  style: theme.textTheme.bodySmall?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: storefrontConfig.isStoreOpen ? AppColors.success : Colors.grey,
                  ),
                ),
                const Spacer(),
                Switch(
                  value: storefrontConfig.isStoreOpen,
                  activeThumbColor: AppColors.success,
                  onChanged: (_) {
                    ref.read(storefrontConfigProvider.notifier).toggleStoreOpen();
                  },
                ),
              ],
            ),
          ),
          AppSpacing.gapV16,

          // AI Studio Quick Action Banner
          Container(
            padding: AppSpacing.paddingAllLg,
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF5B1B9A), Color(0xFF8E24AA)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: AppRadius.borderLg,
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFF6A1B9A).withValues(alpha: 0.3),
                  blurRadius: 16,
                  offset: const Offset(0, 6),
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.2),
                        borderRadius: AppRadius.borderSm,
                      ),
                      child: const Row(
                        children: [
                          Icon(Icons.auto_awesome, size: 12, color: Colors.white),
                          SizedBox(width: 4),
                          Text(
                            'KALA-AI CATALOG STUDIO',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                              letterSpacing: 0.8,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const Icon(Icons.camera_alt_outlined, color: Colors.white70, size: 20),
                  ],
                ),
                AppSpacing.gapV12,
                const Text(
                  'Photograph & List Craft in 60s',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                AppSpacing.gapV8,
                Text(
                  'AI background enhancer, multi-language craft translation in 12 languages, and instant GI tag certification.',
                  style: TextStyle(
                    color: Colors.white.withValues(alpha: 0.9),
                    fontSize: 13,
                    height: 1.4,
                  ),
                ),
                AppSpacing.gapV16,
                Row(
                  children: [
                    ElevatedButton.icon(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.white,
                        foregroundColor: const Color(0xFF6A1B9A),
                        shape: AppRadius.shapeMd,
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                      ),
                      icon: const Icon(Icons.add_a_photo_rounded, size: 16),
                      label: const Text('Add New Craft', style: TextStyle(fontWeight: FontWeight.bold)),
                      onPressed: () => context.push('/catalog-studio/create'),
                    ),
                    AppSpacing.gapH12,
                    OutlinedButton.icon(
                      style: OutlinedButton.styleFrom(
                        foregroundColor: Colors.white,
                        side: const BorderSide(color: Colors.white, width: 1.2),
                        shape: AppRadius.shapeMd,
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                      ),
                      icon: const Icon(Icons.sensors_rounded, size: 16),
                      label: const Text('Go Live'),
                      onPressed: () => _handleGoLiveWorkshop(context, ref, storefrontConfig),
                    ),
                  ],
                ),
              ],
            ),
          ),
          AppSpacing.gapV24,

          // Sales & Financial Overview
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Sales & Financial Overview', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
              Text('This Month', style: theme.textTheme.bodySmall?.copyWith(color: AppColors.primary, fontWeight: FontWeight.bold)),
            ],
          ),
          AppSpacing.gapV12,
          Row(
            children: [
              Expanded(
                child: AppCard(
                  padding: AppSpacing.paddingAllBase,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text('Total Revenue', style: theme.textTheme.bodySmall),
                          const Icon(Icons.currency_rupee, size: 16, color: AppColors.success),
                        ],
                      ),
                      AppSpacing.gapV6,
                      Text(
                        CurrencyFormatter.formatINR(analytics['totalRevenue'] as double),
                        style: theme.textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.bold,
                          color: AppColors.success,
                          fontSize: 20,
                        ),
                      ),
                      AppSpacing.gapV4,
                      Text('+24.8% vs last month', style: theme.textTheme.bodySmall?.copyWith(fontSize: 10, color: AppColors.success)),
                    ],
                  ),
                ),
              ),
              AppSpacing.gapH12,
              Expanded(
                child: AppCard(
                  padding: AppSpacing.paddingAllBase,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text('Units Sold', style: theme.textTheme.bodySmall),
                          const Icon(Icons.shopping_bag_outlined, size: 16, color: AppColors.primary),
                        ],
                      ),
                      AppSpacing.gapV6,
                      Text(
                        '${analytics['totalSalesCount']} Craft Pieces',
                        style: theme.textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.bold,
                          color: AppColors.primary,
                          fontSize: 18,
                        ),
                      ),
                      AppSpacing.gapV4,
                      Text('${analytics['totalOrdersCount']} Total Orders', style: theme.textTheme.bodySmall?.copyWith(fontSize: 10)),
                    ],
                  ),
                ),
              ),
            ],
          ),
          AppSpacing.gapV12,
          Row(
            children: [
              Expanded(
                child: AppCard(
                  padding: AppSpacing.paddingAllBase,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text('Active Catalog', style: theme.textTheme.bodySmall),
                          const Icon(Icons.category_outlined, size: 16, color: AppColors.secondary),
                        ],
                      ),
                      AppSpacing.gapV4,
                      Text('${analytics['activeProductsCount']} Published', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                      AppSpacing.gapV4,
                      Text('${analytics['draftProductsCount']} Drafts in Studio', style: theme.textTheme.bodySmall?.copyWith(fontSize: 10, color: Colors.orange)),
                    ],
                  ),
                ),
              ),
              AppSpacing.gapH12,
              Expanded(
                child: AppCard(
                  padding: AppSpacing.paddingAllBase,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text('Store Visits', style: theme.textTheme.bodySmall),
                          const Icon(Icons.visibility_outlined, size: 16, color: Color(0xFF00796B)),
                        ],
                      ),
                      AppSpacing.gapV4,
                      Text('${storefrontConfig.totalStoreVisits} Buyers', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                      AppSpacing.gapV4,
                      Text('4.9 Rating (142 Reviews)', style: theme.textTheme.bodySmall?.copyWith(fontSize: 10, color: AppColors.tertiary)),
                    ],
                  ),
                ),
              ),
            ],
          ),
          AppSpacing.gapV24,

          // Pending Orders Section
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Pending Orders (${pendingOrders.length})', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
              TextButton(onPressed: () => context.push('/orders'), child: const Text('View All Orders')),
            ],
          ),
          AppSpacing.gapV8,
          if (pendingOrders.isEmpty)
            Container(
              padding: AppSpacing.paddingAllBase,
              decoration: BoxDecoration(
                color: isDark ? AppColors.surfaceDark : AppColors.surfaceLight,
                borderRadius: AppRadius.borderMd,
              ),
              child: const Center(
                child: Text('No pending orders. All orders are packed and dispatched!'),
              ),
            )
          else
            ...pendingOrders.map((order) {
              return AppCard(
                margin: const EdgeInsets.only(bottom: 12),
                padding: AppSpacing.paddingAllBase,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(order.orderNumber, style: const TextStyle(fontWeight: FontWeight.bold)),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                          decoration: const BoxDecoration(
                            color: AppColors.warningContainer,
                            borderRadius: AppRadius.borderXs,
                          ),
                          child: const Text('ACTION REQUIRED', style: TextStyle(color: AppColors.warning, fontSize: 10, fontWeight: FontWeight.bold)),
                        ),
                      ],
                    ),
                    AppSpacing.gapV8,
                    Text('Buyer: ${order.buyerName} (${order.buyerAddress})', style: theme.textTheme.bodySmall),
                    AppSpacing.gapV4,
                    Text('${order.items.first.quantity}x ${order.items.first.productTitle}', style: const TextStyle(fontWeight: FontWeight.w600)),
                    AppSpacing.gapV8,
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(CurrencyFormatter.formatINR(order.totalAmount), style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary)),
                        ElevatedButton(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.primary,
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                            shape: AppRadius.shapePill,
                          ),
                          onPressed: () {
                            ref.read(sellerOrdersProvider.notifier).updateOrderStatus(order.id, OrderStatus.accepted);
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text('Order ${order.orderNumber} accepted! Ready for packing.')),
                            );
                          },
                          child: const Text('Accept & Pack', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                        ),
                      ],
                    ),
                  ],
                ),
              );
            }),
          AppSpacing.gapV16,

          // Pending RFQs Section
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Incoming Custom RFQs (${incomingRfqs.length})', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
              TextButton(onPressed: () => context.push('/rfq'), child: const Text('View All RFQs')),
            ],
          ),
          AppSpacing.gapV8,
          if (incomingRfqs.isEmpty)
            Container(
              padding: AppSpacing.paddingAllBase,
              decoration: BoxDecoration(
                color: isDark ? AppColors.surfaceDark : AppColors.surfaceLight,
                borderRadius: AppRadius.borderMd,
              ),
              child: const Center(
                child: Text('No pending custom RFQ bids right now.'),
              ),
            )
          else
            ...incomingRfqs.map((rfq) {
              return AppCard(
                margin: const EdgeInsets.only(bottom: 12),
                padding: AppSpacing.paddingAllBase,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                          decoration: const BoxDecoration(
                            color: AppColors.secondaryContainer,
                            borderRadius: AppRadius.borderXs,
                          ),
                          child: Text(
                            rfq.status == RfqStatus.matched ? 'AI MATCHED RFQ' : 'NEW RFQ',
                            style: const TextStyle(color: AppColors.onSecondaryContainer, fontSize: 10, fontWeight: FontWeight.bold),
                          ),
                        ),
                        Text('Budget: ${CurrencyFormatter.formatINR(rfq.targetBudget)}', style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary)),
                      ],
                    ),
                    AppSpacing.gapV8,
                    Text(rfq.craftRequired, style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
                    AppSpacing.gapV4,
                    Text('Qty: ${rfq.quantityRequired} units · ${rfq.buyerCompany} (${rfq.buyerLocation})', style: theme.textTheme.bodySmall),
                    AppSpacing.gapV8,
                    Text(rfq.specifications, maxLines: 2, overflow: TextOverflow.ellipsis, style: theme.textTheme.bodySmall?.copyWith(color: isDark ? AppColors.textSecondaryDark : AppColors.textSecondaryLight)),
                    AppSpacing.gapV12,
                    SizedBox(
                      width: double.infinity,
                      child: AppButton(
                        label: 'Review & Submit Quotation',
                        icon: Icons.send_rounded,
                        height: 36,
                        variant: AppButtonVariant.secondary,
                        onPressed: () => context.push('/rfq'),
                      ),
                    ),
                  ],
                ),
              );
            }),
          AppSpacing.gapV24,

          // Quick Catalog Shortcut Preview
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Active Craft Inventory', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
              TextButton(onPressed: () => context.push('/catalog-studio'), child: const Text('Manage Catalog')),
            ],
          ),
          AppSpacing.gapV8,
          SizedBox(
            height: 130,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: products.length,
              separatorBuilder: (_, __) => AppSpacing.gapH12,
              itemBuilder: (context, index) {
                final p = products[index];
                return Container(
                  width: 220,
                  padding: AppSpacing.paddingAllBase,
                  decoration: BoxDecoration(
                    color: isDark ? AppColors.surfaceDark : AppColors.surfaceLight,
                    borderRadius: AppRadius.borderMd,
                    border: Border.all(
                      color: isDark ? AppColors.borderDark : AppColors.borderLight,
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        p.title,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                      ),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(CurrencyFormatter.formatINR(p.retailPrice), style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary)),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: p.status == ProductStatus.published ? AppColors.successContainer : AppColors.warningContainer,
                              borderRadius: AppRadius.borderXs,
                            ),
                            child: Text(
                              p.status == ProductStatus.published ? 'Stock: ${p.stockQuantity}' : 'DRAFT',
                              style: TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.bold,
                                color: p.status == ProductStatus.published ? AppColors.success : AppColors.warning,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                );
              },
            ),
          ),
          AppSpacing.gapV32,
        ],
      ),
    );
  }

  void _showShareStorefrontDialog(BuildContext context, ArtisanStorefrontConfig config) {
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Row(
            children: [
              Icon(Icons.qr_code_2_rounded, color: AppColors.primary, size: 28),
              SizedBox(width: 8),
              Text('Share Storefront'),
            ],
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                height: 140,
                width: 140,
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: AppRadius.borderMd,
                  border: Border.all(color: Colors.black12),
                ),
                child: const Center(
                  child: Icon(Icons.qr_code_rounded, size: 110, color: Colors.black87),
                ),
              ),
              AppSpacing.gapV12,
              Text(
                config.shareUrl,
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.primary),
              ),
              AppSpacing.gapV8,
              const Text(
                'Buyers scanning this QR code get direct access to your verified GI catalog and custom RFQ form.',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 11, color: Colors.grey),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Close'),
            ),
            ElevatedButton.icon(
              style: ElevatedButton.styleFrom(backgroundColor: AppColors.primary, foregroundColor: Colors.white),
              icon: const Icon(Icons.copy, size: 16),
              label: const Text('Copy Link'),
              onPressed: () {
                Navigator.pop(context);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Storefront URL copied to clipboard!')),
                );
              },
            ),
          ],
        );
      },
    );
  }

  void _handleGoLiveWorkshop(BuildContext context, WidgetRef ref, ArtisanStorefrontConfig config) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (context) {
        return Padding(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(color: Colors.grey.shade300, borderRadius: BorderRadius.circular(2)),
                ),
              ),
              AppSpacing.gapV16,
              const Row(
                children: [
                  Icon(Icons.sensors, color: Color(0xFFD32F2F), size: 24),
                  AppSpacing.gapH8,
                  Text('Artisan Live Workshop Studio', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                ],
              ),
              AppSpacing.gapV12,
              const Text(
                'Broadcast your studio work live to thousands of Indian handicraft buyers, demonstrate traditional GI techniques, and take instant live orders.',
                style: TextStyle(fontSize: 13, height: 1.4),
              ),
              AppSpacing.gapV20,
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      icon: const Icon(Icons.schedule),
                      label: const Text('Schedule'),
                      onPressed: () {
                        Navigator.pop(context);
                        context.push('/seller/live/schedule');
                      },
                    ),
                  ),
                  AppSpacing.gapH12,
                  Expanded(
                    child: ElevatedButton.icon(
                      style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFFD32F2F), foregroundColor: Colors.white),
                      icon: const Icon(Icons.videocam),
                      label: const Text('Start Live'),
                      onPressed: () {
                        Navigator.pop(context);
                        context.push('/seller/live/live-01');
                      },
                    ),
                  ),
                ],
              ),
            ],
          ),
        );
      },
    );
  }
}
