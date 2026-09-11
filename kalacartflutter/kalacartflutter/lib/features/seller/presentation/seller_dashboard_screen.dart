import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/utils/currency_formatter.dart';
import '../../../core/widgets/app_button.dart';
import '../../../core/widgets/app_card.dart';
import '../../../core/widgets/app_error_state.dart';
import '../../../core/widgets/app_image_placeholder.dart';
import '../../../core/widgets/app_skeleton.dart';
import '../../../shared/models/enquiry_models.dart';
import '../../../shared/models/order_models.dart';
import '../../../shared/models/product.dart';
import '../../auth/data/auth_repository.dart';
import '../../auth/data/supabase_auth_repository.dart';
import '../../orders/data/orders_repository.dart';
import '../../products/data/supabase_products_repository.dart';
import '../../rfq/data/supabase_rfq_repository.dart';

class SellerDashboardScreen extends ConsumerStatefulWidget {
  const SellerDashboardScreen({super.key});

  @override
  ConsumerState<SellerDashboardScreen> createState() => _SellerDashboardScreenState();
}

class _SellerDashboardScreenState extends ConsumerState<SellerDashboardScreen> {
  final Set<String> _acceptingOrderIds = {};

  Future<void> _refreshAll() async {
    ref.invalidate(sellerOrdersProvider);
    ref.invalidate(sellerProductsProvider);
    ref.invalidate(sellerEnquiriesProvider);
    try {
      await Future.wait<Object>([
        ref.read(sellerOrdersProvider.future),
        ref.read(sellerProductsProvider.future),
        ref.read(sellerEnquiriesProvider.future),
      ]);
    } catch (_) {
      // Each section renders its own error state.
    }
  }

  void _showError(Object e) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(authErrorMessage(e)),
        behavior: SnackBarBehavior.floating,
        backgroundColor: AppColors.error,
      ),
    );
  }

  void _showMessage(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), behavior: SnackBarBehavior.floating),
    );
  }

  Future<void> _acceptOrder(OrderRecord order) async {
    setState(() => _acceptingOrderIds.add(order.id));
    try {
      await ref.read(ordersRepositoryProvider).updateStatus(order.id, OrderStatus.accepted);
      ref.invalidate(sellerOrdersProvider);
      _showMessage('Order ${order.orderNumber} accepted. Ready for packing.');
    } catch (e) {
      _showError(e);
    } finally {
      if (mounted) setState(() => _acceptingOrderIds.remove(order.id));
    }
  }

  Future<void> _copyStorefrontLink(String? sellerId) async {
    if (sellerId == null) {
      _showMessage('Complete your artisan storefront first to get a shareable link.');
      return;
    }
    await Clipboard.setData(ClipboardData(text: 'https://kalacart.in/artisan/$sellerId'));
    _showMessage('Storefront link copied to clipboard.');
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final user = ref.watch(currentUserProvider);
    final ordersAsync = ref.watch(sellerOrdersProvider);
    final productsAsync = ref.watch(sellerProductsProvider);
    final enquiriesAsync = ref.watch(sellerEnquiriesProvider);

    final shopName = (user?.shopName ?? '').trim().isNotEmpty ? user!.shopName!.trim() : (user?.fullName ?? 'Artisan Studio');
    final subtitle = [
      if ((user?.artisanType ?? '').trim().isNotEmpty) user!.artisanType!.trim(),
      user?.regionLabel ?? 'India',
    ].join(' · ');

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
              child: const Icon(Icons.storefront_rounded, color: Colors.white, size: 20),
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
                          shopName,
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
                    subtitle,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
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
            onPressed: () => _copyStorefrontLink(user?.sellerId),
          ),
          IconButton(
            icon: const Icon(Icons.notifications_none_rounded),
            tooltip: 'Notifications',
            onPressed: () => context.push('/notifications'),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _refreshAll,
        child: ListView(
          padding: AppSpacing.paddingAllBase,
          children: [
            if (user != null && user.sellerId == null) ...[
              _buildStorefrontIncompleteBanner(theme),
              AppSpacing.gapV16,
            ],
            if (user != null) ...[
              _buildWelcomeStrip(theme, isDark, user.fullName),
              AppSpacing.gapV16,
            ],

            // AI Studio Quick Action Banner
            _buildAiStudioBanner(context),
            AppSpacing.gapV24,

            // Sales & Financial Overview
            Text('Sales & Catalog Overview', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
            AppSpacing.gapV12,
            _buildKpiGrid(theme, ordersAsync, productsAsync, enquiriesAsync),
            AppSpacing.gapV24,

            // Pending Orders Section
            _buildSectionHeader(
              theme,
              title: ordersAsync.maybeWhen(
                data: (orders) => 'Pending Orders (${orders.where((o) => o.status == OrderStatus.pending).length})',
                orElse: () => 'Pending Orders',
              ),
              actionLabel: 'View All Orders',
              onAction: () => context.push('/orders'),
            ),
            AppSpacing.gapV8,
            _buildPendingOrders(theme, isDark, ordersAsync),
            AppSpacing.gapV16,

            // Incoming RFQs Section
            _buildSectionHeader(
              theme,
              title: enquiriesAsync.maybeWhen(
                data: (list) => 'Incoming RFQs (${list.where((e) => e.status == EnquiryStatus.pending).length})',
                orElse: () => 'Incoming RFQs',
              ),
              actionLabel: 'View All RFQs',
              onAction: () => context.go('/rfq'),
            ),
            AppSpacing.gapV8,
            _buildIncomingRfqs(theme, isDark, enquiriesAsync),
            AppSpacing.gapV24,

            // Inventory strip
            _buildSectionHeader(
              theme,
              title: 'Craft Inventory',
              actionLabel: 'Manage Catalog',
              onAction: () => context.go('/catalog-studio'),
            ),
            AppSpacing.gapV8,
            _buildInventoryStrip(theme, isDark, productsAsync),
            AppSpacing.gapV32,
          ],
        ),
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Header pieces
  // ---------------------------------------------------------------------------

  Widget _buildStorefrontIncompleteBanner(ThemeData theme) {
    return Container(
      padding: AppSpacing.paddingAllBase,
      decoration: BoxDecoration(
        color: AppColors.warningContainer,
        borderRadius: AppRadius.borderMd,
        border: Border.all(color: AppColors.warning.withValues(alpha: 0.4)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.storefront_outlined, color: AppColors.warning, size: 20),
              AppSpacing.gapH8,
              Expanded(
                child: Text(
                  'Complete your artisan storefront',
                  style: TextStyle(fontWeight: FontWeight.bold, color: AppColors.warning),
                ),
              ),
            ],
          ),
          AppSpacing.gapV6,
          Text(
            'You need a storefront before you can list products, receive orders or answer RFQs.',
            style: theme.textTheme.bodySmall?.copyWith(color: AppColors.textPrimaryLight),
          ),
          AppSpacing.gapV12,
          AppButton(
            label: 'Set up storefront',
            icon: Icons.arrow_forward_rounded,
            height: 40,
            isFullWidth: false,
            onPressed: () => context.push('/artisan-onboarding'),
          ),
        ],
      ),
    );
  }

  Widget _buildWelcomeStrip(ThemeData theme, bool isDark, String fullName) {
    final hour = DateTime.now().hour;
    final greeting = hour < 12 ? 'Good morning' : (hour < 17 ? 'Good afternoon' : 'Good evening');
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: isDark ? AppColors.surfaceDark : Colors.white,
        borderRadius: AppRadius.borderMd,
        border: Border.all(color: isDark ? AppColors.borderDark : AppColors.borderLight),
      ),
      child: Row(
        children: [
          const Icon(Icons.waving_hand_outlined, color: AppColors.tertiary, size: 20),
          AppSpacing.gapH8,
          Expanded(
            child: Text(
              '$greeting, ${fullName.trim().isEmpty ? 'Artisan' : fullName.trim()}',
              style: theme.textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          Text(
            DateFormat('d MMM').format(DateTime.now()),
            style: theme.textTheme.bodySmall?.copyWith(
              color: isDark ? AppColors.textTertiaryDark : AppColors.textSecondaryLight,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAiStudioBanner(BuildContext context) {
    return Container(
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
            color: AppColors.aiStudio.withValues(alpha: 0.3),
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
            'Photograph & list a craft in minutes',
            style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
          ),
          AppSpacing.gapV8,
          Text(
            'Try the simulated AI cataloguer to draft a listing, or add a product manually with full control over pricing and wholesale tiers.',
            style: TextStyle(color: Colors.white.withValues(alpha: 0.9), fontSize: 13, height: 1.4),
          ),
          AppSpacing.gapV16,
          Wrap(
            spacing: 12,
            runSpacing: 8,
            children: [
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.white,
                  foregroundColor: AppColors.aiStudio,
                  shape: AppRadius.shapeMd,
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                ),
                icon: const Icon(Icons.auto_awesome_rounded, size: 16),
                label: const Text('Open AI Studio', style: TextStyle(fontWeight: FontWeight.bold)),
                onPressed: () => context.push('/catalog-studio/ai'),
              ),
              OutlinedButton.icon(
                style: OutlinedButton.styleFrom(
                  foregroundColor: Colors.white,
                  side: const BorderSide(color: Colors.white, width: 1.2),
                  shape: AppRadius.shapeMd,
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                ),
                icon: const Icon(Icons.add_rounded, size: 16),
                label: const Text('Add manually'),
                onPressed: () => context.push('/catalog-studio/create'),
              ),
              OutlinedButton.icon(
                style: OutlinedButton.styleFrom(
                  foregroundColor: Colors.white,
                  side: const BorderSide(color: Colors.white, width: 1.2),
                  shape: AppRadius.shapeMd,
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                ),
                icon: const Icon(Icons.sensors_rounded, size: 16),
                label: const Text('Go Live'),
                onPressed: () => _showGoLiveSheet(context),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // KPI cards
  // ---------------------------------------------------------------------------

  Widget _buildKpiGrid(
    ThemeData theme,
    AsyncValue<List<OrderRecord>> ordersAsync,
    AsyncValue<List<Product>> productsAsync,
    AsyncValue<List<Enquiry>> enquiriesAsync,
  ) {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: ordersAsync.when(
                loading: () => const _KpiSkeleton(),
                error: (e, _) => const _KpiCard(
                  label: 'Total Revenue',
                  icon: Icons.currency_rupee,
                  iconColor: AppColors.success,
                  value: '—',
                  caption: 'Could not load orders',
                  captionColor: AppColors.error,
                ),
                data: (orders) {
                  final revenue = orders
                      .where((o) => o.status != OrderStatus.cancelled)
                      .fold<double>(0, (sum, o) => sum + o.totalAmount);
                  final delivered = orders.where((o) => o.status == OrderStatus.delivered).length;
                  return _KpiCard(
                    label: 'Total Revenue',
                    icon: Icons.currency_rupee,
                    iconColor: AppColors.success,
                    value: CurrencyFormatter.formatINR(revenue),
                    valueColor: AppColors.success,
                    caption: '$delivered delivered',
                  );
                },
              ),
            ),
            AppSpacing.gapH12,
            Expanded(
              child: ordersAsync.when(
                loading: () => const _KpiSkeleton(),
                error: (e, _) => const _KpiCard(
                  label: 'Orders',
                  icon: Icons.shopping_bag_outlined,
                  iconColor: AppColors.primary,
                  value: '—',
                  caption: 'Could not load orders',
                  captionColor: AppColors.error,
                ),
                data: (orders) {
                  final pending = orders.where((o) => o.status == OrderStatus.pending).length;
                  return _KpiCard(
                    label: 'Orders',
                    icon: Icons.shopping_bag_outlined,
                    iconColor: AppColors.primary,
                    value: '${orders.length}',
                    valueColor: AppColors.primary,
                    caption: '$pending pending action',
                    captionColor: pending > 0 ? AppColors.warning : null,
                  );
                },
              ),
            ),
          ],
        ),
        AppSpacing.gapV12,
        Row(
          children: [
            Expanded(
              child: productsAsync.when(
                loading: () => const _KpiSkeleton(),
                error: (e, _) => const _KpiCard(
                  label: 'Catalog',
                  icon: Icons.category_outlined,
                  iconColor: AppColors.secondary,
                  value: '—',
                  caption: 'Could not load products',
                  captionColor: AppColors.error,
                ),
                data: (products) {
                  final published = products.where((p) => p.status == ProductStatus.published).length;
                  final drafts = products.where((p) => p.status == ProductStatus.draft).length;
                  return _KpiCard(
                    label: 'Catalog',
                    icon: Icons.category_outlined,
                    iconColor: AppColors.secondary,
                    value: '$published Published',
                    caption: '$drafts drafts in studio',
                    captionColor: drafts > 0 ? AppColors.warning : null,
                  );
                },
              ),
            ),
            AppSpacing.gapH12,
            Expanded(
              child: enquiriesAsync.when(
                loading: () => const _KpiSkeleton(),
                error: (e, _) => const _KpiCard(
                  label: 'Open RFQs',
                  icon: Icons.request_quote_outlined,
                  iconColor: AppColors.tertiary,
                  value: '—',
                  caption: 'Could not load RFQs',
                  captionColor: AppColors.error,
                ),
                data: (list) {
                  final open = list.where((e) => e.status == EnquiryStatus.pending).length;
                  final quoted = list.where((e) => e.status == EnquiryStatus.quoted).length;
                  return _KpiCard(
                    label: 'Open RFQs',
                    icon: Icons.request_quote_outlined,
                    iconColor: AppColors.tertiary,
                    value: '$open',
                    valueColor: AppColors.tertiary,
                    caption: '$quoted awaiting buyer reply',
                  );
                },
              ),
            ),
          ],
        ),
      ],
    );
  }

  // ---------------------------------------------------------------------------
  // Sections
  // ---------------------------------------------------------------------------

  Widget _buildSectionHeader(
    ThemeData theme, {
    required String title,
    required String actionLabel,
    required VoidCallback onAction,
  }) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Expanded(
          child: Text(
            title,
            style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ),
        TextButton(onPressed: onAction, child: Text(actionLabel)),
      ],
    );
  }

  Widget _buildEmptyBox(bool isDark, String message) {
    return Container(
      padding: AppSpacing.paddingAllBase,
      decoration: BoxDecoration(
        color: isDark ? AppColors.surfaceDark : AppColors.surfaceLight,
        borderRadius: AppRadius.borderMd,
      ),
      child: Center(child: Text(message, textAlign: TextAlign.center)),
    );
  }

  Widget _buildListSkeleton() {
    return Column(
      children: List.generate(
        2,
        (_) => const Padding(
          padding: EdgeInsets.only(bottom: 12),
          child: AppSkeleton(height: 110, borderRadius: AppRadius.borderMd),
        ),
      ),
    );
  }

  Widget _buildPendingOrders(ThemeData theme, bool isDark, AsyncValue<List<OrderRecord>> ordersAsync) {
    return ordersAsync.when(
      loading: _buildListSkeleton,
      error: (e, _) => AppErrorState(
        message: authErrorMessage(e),
        onRetry: () => ref.invalidate(sellerOrdersProvider),
      ),
      data: (orders) {
        final pending = orders.where((o) => o.status == OrderStatus.pending).take(3).toList();
        if (pending.isEmpty) {
          return _buildEmptyBox(isDark, 'No pending orders. Everything is packed and on its way.');
        }
        return Column(
          children: pending.map((order) {
            final isBusy = _acceptingOrderIds.contains(order.id);
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
                        child: const Text(
                          'ACTION REQUIRED',
                          style: TextStyle(color: AppColors.warning, fontSize: 10, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ],
                  ),
                  AppSpacing.gapV8,
                  Text(
                    'Buyer: ${order.buyerName ?? 'Buyer'} · ${DateFormat('d MMM, h:mm a').format(order.createdAt.toLocal())}',
                    style: theme.textTheme.bodySmall,
                  ),
                  if ((order.shippingAddress ?? '').trim().isNotEmpty) ...[
                    AppSpacing.gapV2,
                    Text(
                      order.shippingAddress!.trim(),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: isDark ? AppColors.textTertiaryDark : AppColors.textSecondaryLight,
                      ),
                    ),
                  ],
                  AppSpacing.gapV4,
                  Text(
                    '${order.quantity} × ${order.productTitle ?? 'Craft product'}',
                    style: const TextStyle(fontWeight: FontWeight.w600),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  AppSpacing.gapV8,
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        CurrencyFormatter.formatINR(order.totalAmount),
                        style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary),
                      ),
                      ElevatedButton(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.primary,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                          shape: AppRadius.shapePill,
                        ),
                        onPressed: isBusy ? null : () => _acceptOrder(order),
                        child: isBusy
                            ? const SizedBox(
                                width: 16,
                                height: 16,
                                child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                              )
                            : const Text('Accept & Pack', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                      ),
                    ],
                  ),
                ],
              ),
            );
          }).toList(),
        );
      },
    );
  }

  Widget _buildIncomingRfqs(ThemeData theme, bool isDark, AsyncValue<List<Enquiry>> enquiriesAsync) {
    return enquiriesAsync.when(
      loading: _buildListSkeleton,
      error: (e, _) => AppErrorState(
        message: authErrorMessage(e),
        onRetry: () => ref.invalidate(sellerEnquiriesProvider),
      ),
      data: (list) {
        final incoming = list.where((e) => e.status == EnquiryStatus.pending).take(3).toList();
        if (incoming.isEmpty) {
          return _buildEmptyBox(isDark, 'No open RFQs right now.');
        }
        return Column(
          children: incoming.map((rfq) {
            final details = rfq.details;
            return AppCard(
              margin: const EdgeInsets.only(bottom: 12),
              padding: AppSpacing.paddingAllBase,
              onTap: () => context.go('/rfq'),
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
                          rfq.rfqNumber,
                          style: const TextStyle(
                            color: AppColors.onSecondaryContainer,
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      if (rfq.targetBudget > 0)
                        Text(
                          'Budget: ${CurrencyFormatter.formatINR(rfq.targetBudget)}',
                          style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary),
                        ),
                    ],
                  ),
                  AppSpacing.gapV8,
                  Text(
                    details.title,
                    style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  AppSpacing.gapV4,
                  Text(
                    [
                      'Qty: ${rfq.quantity} units',
                      if ((rfq.productTitle ?? '').isNotEmpty) rfq.productTitle!,
                      if ((details.deliveryBy ?? '').isNotEmpty) 'Deliver by ${details.deliveryBy}',
                    ].join(' · '),
                    style: theme.textTheme.bodySmall,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  if (details.notes.isNotEmpty) ...[
                    AppSpacing.gapV8,
                    Text(
                      details.notes,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: isDark ? AppColors.textSecondaryDark : AppColors.textSecondaryLight,
                      ),
                    ),
                  ],
                  AppSpacing.gapV12,
                  AppButton(
                    label: 'Review & Submit Quotation',
                    icon: Icons.send_rounded,
                    height: 36,
                    variant: AppButtonVariant.secondary,
                    onPressed: () => context.go('/rfq'),
                  ),
                ],
              ),
            );
          }).toList(),
        );
      },
    );
  }

  Widget _buildInventoryStrip(ThemeData theme, bool isDark, AsyncValue<List<Product>> productsAsync) {
    return productsAsync.when(
      loading: () => SizedBox(
        height: 130,
        child: ListView.separated(
          scrollDirection: Axis.horizontal,
          itemCount: 3,
          separatorBuilder: (_, __) => AppSpacing.gapH12,
          itemBuilder: (_, __) => const AppSkeleton(width: 220, height: 130, borderRadius: AppRadius.borderMd),
        ),
      ),
      error: (e, _) => AppErrorState(
        message: authErrorMessage(e),
        onRetry: () => ref.invalidate(sellerProductsProvider),
      ),
      data: (products) {
        if (products.isEmpty) {
          return Container(
            padding: AppSpacing.paddingAllBase,
            decoration: BoxDecoration(
              color: isDark ? AppColors.surfaceDark : AppColors.surfaceLight,
              borderRadius: AppRadius.borderMd,
            ),
            child: Column(
              children: [
                const Text('No products yet. Add your first craft to start selling.', textAlign: TextAlign.center),
                AppSpacing.gapV12,
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  alignment: WrapAlignment.center,
                  children: [
                    AppButton(
                      label: 'AI Studio',
                      icon: Icons.auto_awesome,
                      height: 36,
                      isFullWidth: false,
                      variant: AppButtonVariant.secondary,
                      onPressed: () => context.push('/catalog-studio/ai'),
                    ),
                    AppButton(
                      label: 'Add manually',
                      icon: Icons.add_rounded,
                      height: 36,
                      isFullWidth: false,
                      variant: AppButtonVariant.outline,
                      onPressed: () => context.push('/catalog-studio/create'),
                    ),
                  ],
                ),
              ],
            ),
          );
        }
        return SizedBox(
          height: 130,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            itemCount: products.length,
            separatorBuilder: (_, __) => AppSpacing.gapH12,
            itemBuilder: (context, index) {
              final p = products[index];
              final isPublished = p.status == ProductStatus.published;
              final chipColor = p.status == ProductStatus.archived
                  ? Colors.grey
                  : (isPublished ? AppColors.success : AppColors.warning);
              final chipBg = p.status == ProductStatus.archived
                  ? Colors.grey.withValues(alpha: 0.2)
                  : (isPublished ? AppColors.successContainer : AppColors.warningContainer);
              final chipText = p.status == ProductStatus.archived
                  ? 'ARCHIVED'
                  : (isPublished ? 'Stock: ${p.stock}' : 'DRAFT');
              return Container(
                width: 240,
                padding: AppSpacing.paddingAllMd,
                decoration: BoxDecoration(
                  color: isDark ? AppColors.surfaceDark : AppColors.surfaceLight,
                  borderRadius: AppRadius.borderMd,
                  border: Border.all(color: isDark ? AppColors.borderDark : AppColors.borderLight),
                ),
                child: Row(
                  children: [
                    ClipRRect(
                      borderRadius: AppRadius.borderSm,
                      child: p.primaryImageUrl != null
                          ? Image.network(
                              p.primaryImageUrl!,
                              width: 64,
                              height: 64,
                              fit: BoxFit.cover,
                              errorBuilder: (_, __, ___) => const AppImagePlaceholder(width: 64, height: 64),
                            )
                          : const AppImagePlaceholder(width: 64, height: 64),
                    ),
                    AppSpacing.gapH12,
                    Expanded(
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
                          AppSpacing.gapV6,
                          Text(
                            CurrencyFormatter.formatINR(p.price),
                            style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary),
                          ),
                          AppSpacing.gapV4,
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(color: chipBg, borderRadius: AppRadius.borderXs),
                            child: Text(
                              chipText,
                              style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: chipColor),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              );
            },
          ),
        );
      },
    );
  }

  // ---------------------------------------------------------------------------
  // Go Live sheet
  // ---------------------------------------------------------------------------

  void _showGoLiveSheet(BuildContext context) {
    showModalBottomSheet<void>(
      context: context,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (sheetContext) {
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
                  Icon(Icons.sensors, color: AppColors.liveBadge, size: 24),
                  AppSpacing.gapH8,
                  Text('Artisan Live Workshop', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                ],
              ),
              AppSpacing.gapV12,
              const Text(
                'Broadcast your studio work live to buyers, demonstrate traditional techniques, and feature products from your catalog.',
                style: TextStyle(fontSize: 13, height: 1.4),
              ),
              AppSpacing.gapV20,
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.liveBadge,
                  foregroundColor: Colors.white,
                  minimumSize: const Size(double.infinity, 48),
                  shape: AppRadius.shapeMd,
                ),
                icon: const Icon(Icons.videocam),
                label: const Text('Set up a live session'),
                onPressed: () {
                  Navigator.of(sheetContext).pop();
                  context.push('/seller/live/schedule');
                },
              ),
            ],
          ),
        );
      },
    );
  }
}

class _KpiCard extends StatelessWidget {
  final String label;
  final IconData icon;
  final Color iconColor;
  final String value;
  final Color? valueColor;
  final String caption;
  final Color? captionColor;

  const _KpiCard({
    required this.label,
    required this.icon,
    required this.iconColor,
    required this.value,
    this.valueColor,
    required this.caption,
    this.captionColor,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return AppCard(
      padding: AppSpacing.paddingAllBase,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(label, style: theme.textTheme.bodySmall),
              Icon(icon, size: 16, color: iconColor),
            ],
          ),
          AppSpacing.gapV6,
          Text(
            value,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: theme.textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.bold,
              color: valueColor,
              fontSize: 18,
            ),
          ),
          AppSpacing.gapV4,
          Text(
            caption,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: theme.textTheme.bodySmall?.copyWith(fontSize: 10, color: captionColor),
          ),
        ],
      ),
    );
  }
}

class _KpiSkeleton extends StatelessWidget {
  const _KpiSkeleton();

  @override
  Widget build(BuildContext context) {
    return const AppCard(
      padding: AppSpacing.paddingAllBase,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppSkeleton(width: 80, height: 12, borderRadius: AppRadius.borderXs),
          AppSpacing.gapV8,
          AppSkeleton(width: 110, height: 20, borderRadius: AppRadius.borderXs),
          AppSpacing.gapV8,
          AppSkeleton(width: 90, height: 10, borderRadius: AppRadius.borderXs),
        ],
      ),
    );
  }
}
