import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/utils/currency_formatter.dart';
import '../../../core/widgets/app_bottom_sheet.dart';
import '../../../core/widgets/app_button.dart';
import '../../../core/widgets/app_card.dart';
import '../../../core/widgets/app_chip.dart';
import '../../../core/widgets/app_empty_state.dart';
import '../../../core/widgets/app_error_state.dart';
import '../../../core/widgets/app_loading_state.dart';
import '../../../shared/models/enquiry_models.dart';
import '../../auth/data/auth_repository.dart';
import '../../auth/data/supabase_auth_repository.dart';
import '../../chat/data/supabase_chat_repository.dart';
import '../data/supabase_rfq_repository.dart';

/// Coloured badge for an [EnquiryStatus]. Shared by the RFQ and chat screens.
class EnquiryStatusChip extends StatelessWidget {
  final EnquiryStatus status;

  const EnquiryStatusChip({super.key, required this.status});

  static Color backgroundFor(EnquiryStatus status) {
    switch (status) {
      case EnquiryStatus.pending:
        return AppColors.secondaryContainer;
      case EnquiryStatus.quoted:
        return AppColors.tertiaryContainer;
      case EnquiryStatus.accepted:
        return AppColors.successContainer;
      case EnquiryStatus.rejected:
        return AppColors.errorContainer;
      case EnquiryStatus.closed:
        return AppColors.surfaceVariantLight;
    }
  }

  static Color foregroundFor(EnquiryStatus status) {
    switch (status) {
      case EnquiryStatus.pending:
        return AppColors.onSecondaryContainer;
      case EnquiryStatus.quoted:
        return AppColors.tertiaryDark;
      case EnquiryStatus.accepted:
        return AppColors.success;
      case EnquiryStatus.rejected:
        return AppColors.error;
      case EnquiryStatus.closed:
        return AppColors.textSecondaryLight;
    }
  }

  @override
  Widget build(BuildContext context) {
    return AppChip(
      label: status.label.toUpperCase(),
      variant: AppChipVariant.badge,
      color: backgroundFor(status),
      textColor: foregroundFor(status),
    );
  }
}

/// Opens the quotation bottom sheet for [enquiry]. Resolves to `true` when a
/// quotation was sent and the enquiry moved to [EnquiryStatus.quoted].
Future<bool> showQuoteSheet(BuildContext context, Enquiry enquiry) async {
  final sent = await showModalBottomSheet<bool>(
    context: context,
    isScrollControlled: true,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
    ),
    builder: (_) => QuoteSheet(enquiry: enquiry),
  );
  return sent ?? false;
}

/// Bottom-sheet form a seller fills in to quote an enquiry. Sends the quote as
/// a `QUOTE:` chat message and marks the enquiry as quoted.
class QuoteSheet extends ConsumerStatefulWidget {
  final Enquiry enquiry;

  const QuoteSheet({super.key, required this.enquiry});

  @override
  ConsumerState<QuoteSheet> createState() => _QuoteSheetState();
}

class _QuoteSheetState extends ConsumerState<QuoteSheet> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _priceController;
  late final TextEditingController _moqController;
  late final TextEditingController _daysController;
  late final TextEditingController _messageController;
  bool _sending = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    final e = widget.enquiry;
    final suggested = e.details.targetPricePerUnit ?? e.productPrice;
    _priceController = TextEditingController(
      text: suggested == null || suggested <= 0 ? '' : suggested.toStringAsFixed(0),
    );
    _moqController = TextEditingController(text: '${e.quantity}');
    _daysController = TextEditingController();
    _messageController = TextEditingController();
  }

  @override
  void dispose() {
    _priceController.dispose();
    _moqController.dispose();
    _daysController.dispose();
    _messageController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    final enquiry = widget.enquiry;
    final user = ref.read(currentUserProvider);
    final senderProfileId = user?.profileId;
    if (senderProfileId == null) {
      setState(() => _error = 'Sign in to send a quotation.');
      return;
    }
    final buyerId = enquiry.buyerId;
    if (buyerId == null) {
      setState(() => _error = 'This enquiry has no buyer account to message.');
      return;
    }

    final price = double.parse(_priceController.text.trim());
    final moq = int.parse(_moqController.text.trim());
    final days = int.parse(_daysController.text.trim());

    setState(() {
      _sending = true;
      _error = null;
    });

    try {
      final chat = ref.read(supabaseChatRepositoryProvider);
      final receiverProfileId = await chat.profileIdForAuthUser(buyerId);
      if (receiverProfileId == null) {
        if (!mounted) return;
        setState(() {
          _sending = false;
          _error = 'Could not find the buyer\'s profile to deliver the quotation.';
        });
        return;
      }
      await chat.sendMessage(
        enquiryId: enquiry.id,
        senderProfileId: senderProfileId,
        receiverProfileId: receiverProfileId,
        text: QuoteDetails(
          pricePerUnit: price,
          moq: moq,
          deliveryDays: days,
          note: _messageController.text.trim(),
        ).serialize(),
      );
      await ref.read(supabaseRfqRepositoryProvider).updateStatus(enquiry.id, EnquiryStatus.quoted);
      ref.invalidate(sellerEnquiriesProvider);
      ref.invalidate(enquiryProvider(enquiry.id));
      if (!mounted) return;
      Navigator.of(context).pop(true);
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _sending = false;
        _error = authErrorMessage(e);
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final enquiry = widget.enquiry;
    final price = double.tryParse(_priceController.text.trim());
    final moq = int.tryParse(_moqController.text.trim());
    final estimate = price == null || moq == null ? null : price * (enquiry.quantity > moq ? enquiry.quantity : moq);

    return SafeArea(
      child: Padding(
        padding: EdgeInsets.only(
          bottom: MediaQuery.viewInsetsOf(context).bottom + AppSpacing.base,
          top: AppSpacing.base,
          left: AppSpacing.base,
          right: AppSpacing.base,
        ),
        child: SingleChildScrollView(
          child: Form(
            key: _formKey,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Text(
                        'Quotation for ${enquiry.rfqNumber}',
                        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.close),
                      onPressed: _sending ? null : () => Navigator.of(context).pop(false),
                    ),
                  ],
                ),
                Text(
                  '${enquiry.quantity} × ${enquiry.productTitle ?? enquiry.details.title}',
                  style: const TextStyle(fontSize: 12, color: Colors.grey),
                ),
                AppSpacing.gapV12,
                Row(
                  children: [
                    Expanded(
                      child: TextFormField(
                        controller: _priceController,
                        keyboardType: const TextInputType.numberWithOptions(decimal: true),
                        onChanged: (_) => setState(() {}),
                        decoration: const InputDecoration(labelText: 'Price / unit (₹) *'),
                        validator: (v) {
                          final n = double.tryParse((v ?? '').trim());
                          if (n == null || n <= 0) return 'Enter a price above 0';
                          return null;
                        },
                      ),
                    ),
                    AppSpacing.gapH12,
                    Expanded(
                      child: TextFormField(
                        controller: _moqController,
                        keyboardType: TextInputType.number,
                        onChanged: (_) => setState(() {}),
                        decoration: const InputDecoration(labelText: 'Minimum order qty *'),
                        validator: (v) {
                          final n = int.tryParse((v ?? '').trim());
                          if (n == null || n < 1) return 'At least 1';
                          return null;
                        },
                      ),
                    ),
                  ],
                ),
                AppSpacing.gapV12,
                TextFormField(
                  controller: _daysController,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(labelText: 'Production & delivery days *'),
                  validator: (v) {
                    final n = int.tryParse((v ?? '').trim());
                    if (n == null || n < 1) return 'Enter the number of days';
                    return null;
                  },
                ),
                AppSpacing.gapV12,
                TextFormField(
                  controller: _messageController,
                  maxLines: 3,
                  decoration: const InputDecoration(
                    labelText: 'Message to buyer (optional)',
                    hintText: 'Materials, finish, packaging, payment terms...',
                    alignLabelWithHint: true,
                  ),
                ),
                if (estimate != null) ...[
                  AppSpacing.gapV12,
                  Container(
                    padding: AppSpacing.paddingAllMd,
                    decoration: BoxDecoration(
                      color: AppColors.secondaryContainer.withValues(alpha: 0.4),
                      borderRadius: AppRadius.borderSm,
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('Estimated order value', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                        Text(
                          CurrencyFormatter.formatINR(estimate),
                          style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.secondary),
                        ),
                      ],
                    ),
                  ),
                ],
                if (_error != null) ...[
                  AppSpacing.gapV12,
                  Text(_error!, style: const TextStyle(color: AppColors.error, fontSize: 12)),
                ],
                AppSpacing.gapV16,
                AppButton(
                  label: 'Send quotation',
                  icon: Icons.send_rounded,
                  isLoading: _sending,
                  onPressed: _submit,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class SellerRfqScreen extends ConsumerStatefulWidget {
  const SellerRfqScreen({super.key});

  @override
  ConsumerState<SellerRfqScreen> createState() => _SellerRfqScreenState();
}

class _SellerRfqScreenState extends ConsumerState<SellerRfqScreen> with SingleTickerProviderStateMixin {
  late final TabController _tabController;
  final Set<String> _busyIds = <String>{};

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  void _showError(Object e) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(authErrorMessage(e)),
        backgroundColor: AppColors.error,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  void _showInfo(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), behavior: SnackBarBehavior.floating),
    );
  }

  Future<void> _refresh() async {
    ref.invalidate(sellerEnquiriesProvider);
    try {
      await ref.read(sellerEnquiriesProvider.future);
    } catch (_) {
      // Error surfaces through the provider's error state.
    }
  }

  Future<void> _quote(Enquiry enquiry) async {
    final sent = await showQuoteSheet(context, enquiry);
    if (!mounted || !sent) return;
    _showInfo('Quotation sent for ${enquiry.rfqNumber}');
  }

  Future<void> _decline(Enquiry enquiry) async {
    final confirmed = await AppBottomSheet.showConfirmation(
      context: context,
      title: 'Decline ${enquiry.rfqNumber}?',
      message: 'The buyer will see this enquiry as declined. You can still message them from the chat.',
      confirmLabel: 'Decline',
      isDestructive: true,
    );
    if (confirmed != true || !mounted) return;

    setState(() => _busyIds.add(enquiry.id));
    try {
      await ref.read(supabaseRfqRepositoryProvider).updateStatus(enquiry.id, EnquiryStatus.rejected);
      ref.invalidate(sellerEnquiriesProvider);
      ref.invalidate(enquiryProvider(enquiry.id));
      if (!mounted) return;
      _showInfo('${enquiry.rfqNumber} declined');
    } catch (e) {
      if (!mounted) return;
      _showError(e);
    } finally {
      if (mounted) setState(() => _busyIds.remove(enquiry.id));
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final enquiriesAsync = ref.watch(sellerEnquiriesProvider);
    final all = enquiriesAsync.valueOrNull ?? const <Enquiry>[];

    final incoming = all.where((e) => e.status == EnquiryStatus.pending).toList();
    final quoted = all.where((e) => e.status == EnquiryStatus.quoted).toList();
    final accepted = all.where((e) => e.status == EnquiryStatus.accepted).toList();
    final closed = all
        .where((e) => e.status == EnquiryStatus.rejected || e.status == EnquiryStatus.closed)
        .toList();

    String count(List<Enquiry> list) => enquiriesAsync.hasValue ? ' (${list.length})' : '';

    return Scaffold(
      appBar: AppBar(
        title: const Row(
          children: [
            Icon(Icons.handshake_rounded, color: AppColors.secondary),
            AppSpacing.gapH8,
            Text('Buyer Enquiries & Quotes'),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.chat_bubble_outline),
            tooltip: 'Buyer messages',
            onPressed: () => context.push('/chat'),
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          isScrollable: true,
          tabAlignment: TabAlignment.start,
          labelColor: AppColors.secondary,
          unselectedLabelColor: isDark ? AppColors.textSecondaryDark : AppColors.textSecondaryLight,
          indicatorColor: AppColors.secondary,
          tabs: [
            Tab(text: 'Incoming${count(incoming)}'),
            Tab(text: 'Quoted${count(quoted)}'),
            Tab(text: 'Accepted${count(accepted)}'),
            Tab(text: 'Closed${count(closed)}'),
          ],
        ),
      ),
      body: enquiriesAsync.when(
        loading: () => const AppLoadingState(message: 'Loading enquiries...'),
        error: (e, _) => AppErrorState(
          title: 'Could not load enquiries',
          message: authErrorMessage(e),
          onRetry: () => ref.invalidate(sellerEnquiriesProvider),
        ),
        data: (_) => TabBarView(
          controller: _tabController,
          children: [
            _buildList(incoming, theme, isDark, emptyMessage: 'New buyer enquiries about your products will appear here.'),
            _buildList(quoted, theme, isDark, emptyMessage: 'Enquiries you have quoted will appear here.'),
            _buildList(accepted, theme, isDark, emptyMessage: 'Quotes accepted by buyers will appear here.'),
            _buildList(closed, theme, isDark, emptyMessage: 'Declined and closed enquiries will appear here.'),
          ],
        ),
      ),
    );
  }

  Widget _buildList(List<Enquiry> list, ThemeData theme, bool isDark, {required String emptyMessage}) {
    return RefreshIndicator(
      onRefresh: _refresh,
      child: list.isEmpty
          ? ListView(
              children: [
                SizedBox(
                  height: MediaQuery.sizeOf(context).height * 0.6,
                  child: AppEmptyState(
                    icon: Icons.handshake_outlined,
                    title: 'No enquiries here',
                    message: emptyMessage,
                  ),
                ),
              ],
            )
          : ListView.separated(
              padding: AppSpacing.paddingAllBase,
              itemCount: list.length,
              separatorBuilder: (_, __) => AppSpacing.gapV12,
              itemBuilder: (context, index) {
                final enquiry = list[index];
                return _SellerEnquiryCard(
                  enquiry: enquiry,
                  isDark: isDark,
                  busy: _busyIds.contains(enquiry.id),
                  onChat: () => context.push('/chat/${enquiry.id}'),
                  onQuote: () => _quote(enquiry),
                  onDecline: () => _decline(enquiry),
                );
              },
            ),
    );
  }
}

class _SellerEnquiryCard extends StatelessWidget {
  final Enquiry enquiry;
  final bool isDark;
  final bool busy;
  final VoidCallback onChat;
  final VoidCallback onQuote;
  final VoidCallback onDecline;

  const _SellerEnquiryCard({
    required this.enquiry,
    required this.isDark,
    required this.busy,
    required this.onChat,
    required this.onQuote,
    required this.onDecline,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final details = enquiry.details;
    final secondary = isDark ? AppColors.textSecondaryDark : AppColors.textSecondaryLight;
    final canQuote = enquiry.status == EnquiryStatus.pending || enquiry.status == EnquiryStatus.quoted;
    final canDecline = enquiry.status == EnquiryStatus.pending || enquiry.status == EnquiryStatus.quoted;

    final metaBits = <String>[
      'Qty: ${enquiry.quantity}',
      if ((details.deliveryBy ?? '').isNotEmpty) 'Deliver by: ${details.deliveryBy}',
      if ((details.destinationPincode ?? '').isNotEmpty) 'PIN: ${details.destinationPincode}',
    ];

    return AppCard(
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
          Text(details.title, style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
          if (enquiry.productTitle != null && enquiry.productTitle != details.title) ...[
            AppSpacing.gapV2,
            Text('Product: ${enquiry.productTitle}', style: TextStyle(fontSize: 12, color: secondary)),
          ],
          AppSpacing.gapV4,
          Text(metaBits.join(' · '), style: TextStyle(fontSize: 11, color: secondary)),
          if (details.targetPricePerUnit != null) ...[
            AppSpacing.gapV2,
            Text(
              'Buyer target: ${CurrencyFormatter.formatINR(details.targetPricePerUnit!)} / unit',
              style: TextStyle(fontSize: 11, color: secondary),
            ),
          ],
          if (details.notes.isNotEmpty) ...[
            AppSpacing.gapV8,
            Text(details.notes, style: TextStyle(fontSize: 12, height: 1.35, color: secondary)),
          ],
          AppSpacing.gapV8,
          Text(
            'Received ${DateFormat('d MMM yyyy, h:mm a').format(enquiry.createdAt.toLocal())}',
            style: TextStyle(fontSize: 10, color: secondary),
          ),
          AppSpacing.gapV12,
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  style: OutlinedButton.styleFrom(shape: AppRadius.shapeMd),
                  icon: const Icon(Icons.chat_bubble_outline, size: 14),
                  label: const Text('Chat', style: TextStyle(fontSize: 11)),
                  onPressed: onChat,
                ),
              ),
              if (canDecline) ...[
                AppSpacing.gapH8,
                Expanded(
                  child: OutlinedButton.icon(
                    style: OutlinedButton.styleFrom(
                      shape: AppRadius.shapeMd,
                      foregroundColor: AppColors.error,
                      side: const BorderSide(color: AppColors.error),
                    ),
                    icon: busy
                        ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2))
                        : const Icon(Icons.close, size: 14),
                    label: const Text('Decline', style: TextStyle(fontSize: 11)),
                    onPressed: busy ? null : onDecline,
                  ),
                ),
              ],
              if (canQuote) ...[
                AppSpacing.gapH8,
                Expanded(
                  child: ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.secondary,
                      foregroundColor: Colors.white,
                      shape: AppRadius.shapeMd,
                    ),
                    icon: const Icon(Icons.send_rounded, size: 14),
                    label: Text(
                      enquiry.status == EnquiryStatus.quoted ? 'Re-quote' : 'Submit Quotation',
                      style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold),
                    ),
                    onPressed: busy ? null : onQuote,
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
