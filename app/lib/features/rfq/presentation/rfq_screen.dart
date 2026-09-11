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
import '../../../core/widgets/app_loading_state.dart';
import '../../../shared/models/enquiry_models.dart';
import '../../../shared/services/user_role_service.dart';
import '../../auth/data/supabase_auth_repository.dart';
import '../data/supabase_rfq_repository.dart';
import 'seller_rfq_screen.dart';

class RfqScreen extends ConsumerWidget {
  const RfqScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final userRole = ref.watch(userRoleProvider);

    if (userRole.isArtisanSeller) {
      return const SellerRfqScreen();
    } else {
      return const BuyerRfqListView();
    }
  }
}

class BuyerRfqListView extends ConsumerWidget {
  const BuyerRfqListView({super.key});

  Future<void> _refresh(WidgetRef ref) async {
    ref.invalidate(buyerEnquiriesProvider);
    try {
      await ref.read(buyerEnquiriesProvider.future);
    } catch (_) {
      // Error surfaces through the provider's error state.
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final enquiriesAsync = ref.watch(buyerEnquiriesProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Row(
          children: [
            Icon(Icons.handshake_outlined, color: AppColors.primary),
            AppSpacing.gapH8,
            Text('Custom Quotes (RFQs)'),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.chat_bubble_outline),
            tooltip: 'Artisan messages',
            onPressed: () => context.push('/chat'),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () => _refresh(ref),
        child: ListView(
          padding: AppSpacing.paddingAllBase,
          children: [
            // Banner
            Container(
              padding: AppSpacing.paddingAllBase,
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  colors: [AppColors.primary, Color(0xFFD4623B)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: AppRadius.borderMd,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Source Direct from Indian Artisans',
                    style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                  AppSpacing.gapV4,
                  const Text(
                    'Ask an artisan for a bulk or customised quote on any listed craft. They reply with pricing and delivery timelines in chat.',
                    style: TextStyle(color: Colors.white, fontSize: 12, height: 1.35),
                  ),
                  AppSpacing.gapV12,
                  ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.white,
                      foregroundColor: AppColors.primary,
                      shape: AppRadius.shapePill,
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                    ),
                    icon: const Icon(Icons.add, size: 16),
                    label: const Text('New Enquiry', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                    onPressed: () => context.push('/rfq/create'),
                  ),
                ],
              ),
            ),
            AppSpacing.gapV20,

            Text(
              enquiriesAsync.hasValue
                  ? 'My Quotation Requests (${enquiriesAsync.value!.length})'
                  : 'My Quotation Requests',
              style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
            ),
            AppSpacing.gapV12,

            enquiriesAsync.when(
              loading: () => const Padding(
                padding: EdgeInsets.symmetric(vertical: 48),
                child: AppLoadingState(message: 'Loading your enquiries...'),
              ),
              error: (e, _) => AppErrorState(
                title: 'Could not load enquiries',
                message: authErrorMessage(e),
                onRetry: () => ref.invalidate(buyerEnquiriesProvider),
              ),
              data: (enquiries) {
                if (enquiries.isEmpty) {
                  return AppEmptyState(
                    icon: Icons.request_quote_outlined,
                    title: 'No enquiries yet',
                    message: 'Pick a craft and ask its artisan for a bulk or custom quote.',
                    actionLabel: 'New Enquiry',
                    onAction: () => context.push('/rfq/create'),
                  );
                }
                return Column(
                  children: [
                    for (final enquiry in enquiries)
                      _BuyerEnquiryCard(enquiry: enquiry, isDark: isDark),
                  ],
                );
              },
            ),
            AppSpacing.gapV32,
            AppSpacing.gapV32,
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        icon: const Icon(Icons.post_add),
        label: const Text('New Enquiry'),
        onPressed: () => context.push('/rfq/create'),
      ),
    );
  }
}

class _BuyerEnquiryCard extends StatelessWidget {
  final Enquiry enquiry;
  final bool isDark;

  const _BuyerEnquiryCard({required this.enquiry, required this.isDark});

  @override
  Widget build(BuildContext context) {
    final details = enquiry.details;
    final secondary = isDark ? AppColors.textSecondaryDark : AppColors.textSecondaryLight;

    final metaBits = <String>[
      'Qty: ${enquiry.quantity}',
      if (details.targetPricePerUnit != null)
        'Target: ${CurrencyFormatter.formatINR(details.targetPricePerUnit!)}/unit',
      if ((details.deliveryBy ?? '').isNotEmpty) 'Deliver by: ${details.deliveryBy}',
      if ((details.destinationPincode ?? '').isNotEmpty) 'PIN: ${details.destinationPincode}',
    ];

    return AppCard(
      margin: const EdgeInsets.only(bottom: 12),
      padding: AppSpacing.paddingAllBase,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              EnquiryStatusChip(status: enquiry.status),
              AppSpacing.gapH8,
              Text(enquiry.rfqNumber, style: TextStyle(fontSize: 11, color: secondary, fontWeight: FontWeight.w600)),
              const Spacer(),
              Text(
                'Budget: ${CurrencyFormatter.formatINR(enquiry.targetBudget)}',
                style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary),
              ),
            ],
          ),
          AppSpacing.gapV8,
          Text(details.title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
          if (enquiry.productTitle != null && enquiry.productTitle != details.title) ...[
            AppSpacing.gapV2,
            Text('Product: ${enquiry.productTitle}', style: TextStyle(fontSize: 12, color: secondary)),
          ],
          AppSpacing.gapV4,
          Text(metaBits.join(' · '), style: TextStyle(fontSize: 11, color: secondary)),
          if (enquiry.sellerShopName != null) ...[
            AppSpacing.gapV2,
            Row(
              children: [
                Icon(Icons.storefront_outlined, size: 12, color: secondary),
                AppSpacing.gapH4,
                Expanded(
                  child: Text(
                    enquiry.sellerShopName!,
                    style: TextStyle(fontSize: 11, color: secondary),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
          ],
          if (details.notes.isNotEmpty) ...[
            AppSpacing.gapV6,
            Text(
              details.notes,
              style: TextStyle(fontSize: 12, color: secondary),
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
            ),
          ],
          AppSpacing.gapV8,
          Text(
            'Sent ${DateFormat('d MMM yyyy, h:mm a').format(enquiry.createdAt.toLocal())}',
            style: TextStyle(fontSize: 10, color: secondary),
          ),
          AppSpacing.gapV12,
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  style: OutlinedButton.styleFrom(shape: AppRadius.shapeMd),
                  icon: const Icon(Icons.chat_bubble_outline, size: 14),
                  label: const Text('Open chat', style: TextStyle(fontSize: 11)),
                  onPressed: () => context.push('/chat/${enquiry.id}'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
