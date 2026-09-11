import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/utils/currency_formatter.dart';
import '../../../core/widgets/app_card.dart';
import '../../../shared/services/user_role_service.dart';
import '../data/rfq_chat_repository.dart';
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

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final rfqs = ref.watch(buyerRfqProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Row(
          children: [
            Icon(Icons.handshake_outlined, color: AppColors.primary),
            AppSpacing.gapH8,
            Text('Custom B2B Quotes (RFQs)'),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.chat_bubble_outline),
            tooltip: 'Artisan Messages',
            onPressed: () => context.push('/chat'),
          ),
        ],
      ),
      body: ListView(
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
                  'Post bespoke craft requests, custom corporate gifting batches, or wholesale orders directly to master guilds.',
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
                  label: const Text('Post New Custom RFQ', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                  onPressed: () => context.push('/rfq/create'),
                ),
              ],
            ),
          ),
          AppSpacing.gapV20,

          // Active Buyer RFQs
          Text('My Active Quotation Requests (${rfqs.length})', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
          AppSpacing.gapV12,

          ...rfqs.map((rfq) {
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
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: rfq.status == 'quotes_received' ? AppColors.successContainer : AppColors.secondaryContainer,
                          borderRadius: AppRadius.borderXs,
                        ),
                        child: Text(
                          rfq.status == 'quotes_received' ? 'QUOTES RECEIVED' : 'OPEN FOR BIDS',
                          style: TextStyle(
                            color: rfq.status == 'quotes_received' ? AppColors.success : AppColors.onSecondaryContainer,
                            fontSize: 9,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      Text('Target: ${CurrencyFormatter.formatINR(rfq.totalTargetBudget)}', style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary)),
                    ],
                  ),
                  AppSpacing.gapV8,
                  Text(rfq.title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                  AppSpacing.gapV4,
                  Text('Qty: ${rfq.quantity} units · Destination: ${rfq.destinationPincode}', style: const TextStyle(fontSize: 11, color: Colors.grey)),
                  AppSpacing.gapV6,
                  Text(rfq.customizationNotes, style: TextStyle(fontSize: 12, color: isDark ? AppColors.textSecondaryDark : AppColors.textSecondaryLight)),
                  AppSpacing.gapV12,
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton.icon(
                          style: OutlinedButton.styleFrom(shape: AppRadius.shapeMd),
                          icon: const Icon(Icons.chat_bubble_outline, size: 14),
                          label: const Text('Open Artisan Chat', style: TextStyle(fontSize: 11)),
                          onPressed: () => context.push('/chat/conv-01'),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            );
          }),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        icon: const Icon(Icons.post_add),
        label: const Text('Post Custom RFQ'),
        onPressed: () => context.push('/rfq/create'),
      ),
    );
  }
}
