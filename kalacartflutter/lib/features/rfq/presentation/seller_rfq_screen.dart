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

class SellerRfqScreen extends ConsumerStatefulWidget {
  const SellerRfqScreen({super.key});

  @override
  ConsumerState<SellerRfqScreen> createState() => _SellerRfqScreenState();
}

class _SellerRfqScreenState extends ConsumerState<SellerRfqScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
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
    final rfqs = ref.watch(sellerRfqsProvider);

    final incoming = rfqs.where((r) => r.status == RfqStatus.incoming).toList();
    final matched = rfqs.where((r) => r.status == RfqStatus.matched).toList();
    final quoted = rfqs.where((r) => r.status == RfqStatus.quoted).toList();

    return Scaffold(
      appBar: AppBar(
        title: const Row(
          children: [
            Icon(Icons.handshake_rounded, color: AppColors.secondary),
            AppSpacing.gapH8,
            Text('Custom RFQs & Bulk Quotes'),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.chat_bubble_outline),
            tooltip: 'Buyer Messages',
            onPressed: () => context.push('/chat'),
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          labelColor: AppColors.secondary,
          unselectedLabelColor: isDark ? AppColors.textSecondaryDark : AppColors.textSecondaryLight,
          indicatorColor: AppColors.secondary,
          tabs: [
            Tab(text: 'Incoming (${incoming.length})'),
            Tab(text: 'AI Matched (${matched.length})'),
            Tab(text: 'Quoted (${quoted.length})'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildRfqList(incoming, theme, isDark),
          _buildRfqList(matched, theme, isDark),
          _buildRfqList(quoted, theme, isDark),
        ],
      ),
    );
  }

  Widget _buildRfqList(List<SellerRfq> list, ThemeData theme, bool isDark) {
    if (list.isEmpty) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.handshake_outlined, size: 48, color: Colors.grey),
            AppSpacing.gapV12,
            Text('No RFQs in this category', style: TextStyle(fontWeight: FontWeight.bold)),
            AppSpacing.gapV4,
            Text('You will be alerted when new wholesale buyers submit quote requests.', style: TextStyle(color: Colors.grey)),
          ],
        ),
      );
    }

    return ListView.separated(
      padding: AppSpacing.paddingAllBase,
      itemCount: list.length,
      separatorBuilder: (_, __) => AppSpacing.gapV12,
      itemBuilder: (context, index) {
        final rfq = list[index];
        return AppCard(
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
                      color: rfq.status == RfqStatus.quoted ? AppColors.successContainer : AppColors.secondaryContainer,
                      borderRadius: AppRadius.borderXs,
                    ),
                    child: Text(
                      rfq.status == RfqStatus.quoted ? 'QUOTE SUBMITTED' : (rfq.status == RfqStatus.matched ? 'AI MATCHED' : 'INCOMING BID'),
                      style: TextStyle(
                        fontSize: 9,
                        fontWeight: FontWeight.bold,
                        color: rfq.status == RfqStatus.quoted ? AppColors.success : AppColors.onSecondaryContainer,
                      ),
                    ),
                  ),
                  Text(
                    'Budget: ${CurrencyFormatter.formatINR(rfq.targetBudget)}',
                    style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary),
                  ),
                ],
              ),
              AppSpacing.gapV8,
              Text(
                rfq.craftRequired,
                style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold),
              ),
              AppSpacing.gapV4,
              Text(
                'Buyer: ${rfq.buyerCompany} (${rfq.buyerLocation}) · Qty: ${rfq.quantityRequired} Units',
                style: const TextStyle(fontSize: 11, color: Colors.grey),
              ),
              AppSpacing.gapV8,
              Text(
                rfq.specifications,
                style: TextStyle(fontSize: 12, height: 1.35, color: isDark ? AppColors.textSecondaryDark : AppColors.textSecondaryLight),
              ),
              AppSpacing.gapV12,

              if (rfq.quote != null) ...[
                Container(
                  padding: AppSpacing.paddingAllBase,
                  decoration: BoxDecoration(
                    color: AppColors.successContainer.withValues(alpha: 0.2),
                    borderRadius: AppRadius.borderSm,
                    border: Border.all(color: AppColors.success),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Your Active Quotation:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11, color: AppColors.success)),
                      Text('• Price / Unit: ${CurrencyFormatter.formatINR(rfq.quote!.pricePerUnit)} (MOQ: ${rfq.quote!.moq} units)', style: const TextStyle(fontSize: 11)),
                      Text('• Delivery Timeline: ${rfq.quote!.deliveryDays} Days', style: const TextStyle(fontSize: 11)),
                      Text('• Note: "${rfq.quote!.message}"', style: const TextStyle(fontSize: 11, fontStyle: FontStyle.italic)),
                    ],
                  ),
                ),
                AppSpacing.gapV12,
              ],

              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      style: OutlinedButton.styleFrom(shape: AppRadius.shapeMd),
                      icon: const Icon(Icons.chat_bubble_outline, size: 14),
                      label: const Text('Direct Chat', style: TextStyle(fontSize: 11)),
                      onPressed: () => context.push('/chat/conv-01'),
                    ),
                  ),
                  if (rfq.quote == null) ...[
                    AppSpacing.gapH8,
                    Expanded(
                      child: ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.secondary,
                          foregroundColor: Colors.white,
                          shape: AppRadius.shapeMd,
                        ),
                        icon: const Icon(Icons.send_rounded, size: 14),
                        label: const Text('Submit Quotation', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                        onPressed: () => _showQuotationDialog(context, rfq),
                      ),
                    ),
                  ],
                ],
              ),
            ],
          ),
        );
      },
    );
  }

  void _showQuotationDialog(BuildContext context, SellerRfq rfq) {
    final priceController = TextEditingController(text: (rfq.targetBudget / rfq.quantityRequired).toStringAsFixed(0));
    final moqController = TextEditingController(text: '${(rfq.quantityRequired / 2).toInt()}');
    final daysController = TextEditingController(text: '25');
    final messageController = TextEditingController(text: 'Greetings! We are master craftsmen certified in GI heritage. We can handcraft this batch with 100% natural materials.');
    bool voiceAttached = false;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            return Padding(
              padding: EdgeInsets.only(
                bottom: MediaQuery.of(context).viewInsets.bottom + 16,
                top: 16,
                left: 16,
                right: 16,
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text('Send Quotation for ${rfq.rfqNumber}', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                      IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.pop(context)),
                    ],
                  ),
                  AppSpacing.gapV8,
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: priceController,
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(labelText: 'Price / Unit (₹) *'),
                        ),
                      ),
                      AppSpacing.gapH12,
                      Expanded(
                        child: TextField(
                          controller: moqController,
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(labelText: 'Min Order Qty (MOQ) *'),
                        ),
                      ),
                    ],
                  ),
                  AppSpacing.gapV12,
                  TextField(
                    controller: daysController,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(labelText: 'Production & Delivery Days *'),
                  ),
                  AppSpacing.gapV12,
                  TextField(
                    controller: messageController,
                    maxLines: 2,
                    decoration: const InputDecoration(labelText: 'Message / Technical Note to Buyer'),
                  ),
                  AppSpacing.gapV12,
                  Row(
                    children: [
                      IconButton(
                        icon: Icon(voiceAttached ? Icons.check_circle : Icons.mic_rounded, color: AppColors.primary),
                        onPressed: () {
                          setModalState(() => voiceAttached = !voiceAttached);
                        },
                      ),
                      Text(voiceAttached ? 'Audio Note Attached (0:35)' : 'Record Voice Note for Buyer', style: const TextStyle(fontSize: 12)),
                    ],
                  ),
                  AppSpacing.gapV16,
                  SizedBox(
                    width: double.infinity,
                    height: 44,
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.secondary,
                        foregroundColor: Colors.white,
                        shape: AppRadius.shapeMd,
                      ),
                      onPressed: () {
                        final price = double.tryParse(priceController.text) ?? 1200;
                        final moq = int.tryParse(moqController.text) ?? 20;
                        final days = int.tryParse(daysController.text) ?? 25;

                        ref.read(sellerRfqsProvider.notifier).submitQuotation(
                              rfqId: rfq.id,
                              pricePerUnit: price,
                              moq: moq,
                              deliveryDays: days,
                              message: messageController.text,
                              hasVoiceNote: voiceAttached,
                              portfolioIds: ['sp-001', 'sp-002'],
                            );

                        Navigator.pop(context);
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(content: Text('Quotation submitted for ${rfq.rfqNumber}!')),
                        );
                      },
                      child: const Text('Send Formal Quotation', style: TextStyle(fontWeight: FontWeight.bold)),
                    ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }
}
