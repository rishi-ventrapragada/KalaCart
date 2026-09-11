import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/utils/currency_formatter.dart';
import '../../../core/widgets/app_empty_state.dart';
import '../../../core/widgets/app_error_state.dart';
import '../../../core/widgets/app_image_placeholder.dart';
import '../../../core/widgets/app_loading_state.dart';
import '../../../shared/models/chat_rfq_models.dart';
import '../../../shared/models/enquiry_models.dart';
import '../../auth/data/auth_repository.dart';
import '../../auth/data/supabase_auth_repository.dart';
import '../../auth/domain/user_model.dart';
import '../../orders/data/orders_repository.dart';
import '../../rfq/data/supabase_rfq_repository.dart';
import '../../rfq/presentation/seller_rfq_screen.dart';
import '../data/supabase_chat_repository.dart';

/// Chat for one enquiry. [conversationId] is the `enquiries.id`.
class ChatScreen extends ConsumerStatefulWidget {
  final String conversationId;

  const ChatScreen({super.key, required this.conversationId});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final TextEditingController _textController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final FocusNode _inputFocus = FocusNode();

  bool _sending = false;
  String? _acceptingMessageId;

  /// `profiles.id` of the other participant, once resolved for the loaded enquiry.
  String? _receiverProfileId;
  String? _receiverResolvedForEnquiryId;
  bool _resolvingReceiver = false;

  int _lastMessageCount = -1;
  bool _markedReadOnce = false;

  @override
  void dispose() {
    _textController.dispose();
    _scrollController.dispose();
    _inputFocus.dispose();
    super.dispose();
  }

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------

  bool _isSellerSide(Enquiry enquiry, UserModel user) =>
      user.sellerId != null && user.sellerId == enquiry.sellerId;

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

  void _scrollToBottom() {
    if (!mounted || !_scrollController.hasClients) return;
    _scrollController.animateTo(
      _scrollController.position.maxScrollExtent,
      duration: const Duration(milliseconds: 250),
      curve: Curves.easeOut,
    );
  }

  Future<void> _resolveReceiver(Enquiry enquiry, UserModel user) async {
    if (_receiverResolvedForEnquiryId == enquiry.id || _resolvingReceiver) return;

    if (!_isSellerSide(enquiry, user)) {
      if (!mounted) return;
      setState(() {
        _receiverProfileId = enquiry.sellerProfileId;
        _receiverResolvedForEnquiryId = enquiry.id;
      });
      return;
    }

    final buyerId = enquiry.buyerId;
    if (buyerId == null) {
      if (!mounted) return;
      setState(() {
        _receiverProfileId = null;
        _receiverResolvedForEnquiryId = enquiry.id;
      });
      return;
    }

    _resolvingReceiver = true;
    final id = await ref.read(supabaseChatRepositoryProvider).profileIdForAuthUser(buyerId);
    _resolvingReceiver = false;
    if (!mounted) return;
    setState(() {
      _receiverProfileId = id;
      _receiverResolvedForEnquiryId = enquiry.id;
    });
  }

  Future<void> _markRead(Enquiry enquiry, UserModel user) async {
    final profileId = user.profileId;
    if (profileId == null) return;
    await ref.read(supabaseChatRepositoryProvider).markRead(enquiryId: enquiry.id, myProfileId: profileId);
    if (!mounted) return;
    // Refresh unread badges on the conversation list.
    ref.invalidate(_isSellerSide(enquiry, user) ? sellerEnquiriesProvider : buyerEnquiriesProvider);
  }

  /// Reacts to a new snapshot of the message list: scrolls to the bottom and
  /// marks incoming messages as read.
  void _onMessages(List<ChatMessage> messages, Enquiry enquiry, UserModel user) {
    if (messages.length == _lastMessageCount) return;
    final hadMessages = _lastMessageCount >= 0;
    _lastMessageCount = messages.length;
    WidgetsBinding.instance.addPostFrameCallback((_) => _scrollToBottom());

    final hasIncoming = messages.any((m) => !m.isMe);
    if (!hasIncoming) return;
    final newestIsIncoming = messages.isNotEmpty && !messages.last.isMe;
    if (!_markedReadOnce || (hadMessages && newestIsIncoming)) {
      _markedReadOnce = true;
      _markRead(enquiry, user);
    }
  }

  // ---------------------------------------------------------------------------
  // Actions
  // ---------------------------------------------------------------------------

  Future<void> _send(Enquiry enquiry, UserModel user) async {
    final text = _textController.text.trim();
    final receiver = _receiverProfileId;
    final sender = user.profileId;
    if (text.isEmpty || receiver == null || sender == null || _sending) return;

    setState(() => _sending = true);
    try {
      await ref.read(supabaseChatRepositoryProvider).sendMessage(
            enquiryId: enquiry.id,
            senderProfileId: sender,
            receiverProfileId: receiver,
            text: text,
          );
      if (!mounted) return;
      _textController.clear();
    } catch (e) {
      if (!mounted) return;
      _showError(e);
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  Future<void> _openQuoteSheet(Enquiry enquiry) async {
    final sent = await showQuoteSheet(context, enquiry);
    if (!mounted || !sent) return;
    ref.invalidate(enquiryProvider(enquiry.id));
    _showInfo('Quotation sent for ${enquiry.rfqNumber}');
  }

  Future<void> _acceptQuote({
    required ChatMessage message,
    required Enquiry enquiry,
    required UserModel user,
    required double pricePerUnit,
    required int moq,
  }) async {
    final productId = enquiry.productId;
    final sellerId = enquiry.sellerId;
    if (productId == null || sellerId == null) {
      _showInfo('This enquiry is missing product details, so an order cannot be placed.');
      return;
    }
    if (_acceptingMessageId != null) return;

    final quantity = math.max(enquiry.quantity, moq);
    setState(() => _acceptingMessageId = message.id);
    try {
      final orders = await ref.read(ordersRepositoryProvider).placeOrders(
        buyerAuthId: user.id,
        lines: [
          OrderLineInput(
            productId: productId,
            sellerId: sellerId,
            quantity: quantity,
            unitPrice: pricePerUnit,
          ),
        ],
        shippingAddress: user.regionLabel,
      );
      if (orders.isEmpty) {
        if (!mounted) return;
        _showInfo('The order could not be created. Please try again.');
        return;
      }
      final order = orders.first;

      final receiver = _receiverProfileId;
      final sender = user.profileId;
      if (receiver != null && sender != null) {
        await ref.read(supabaseChatRepositoryProvider).sendMessage(
              enquiryId: enquiry.id,
              senderProfileId: sender,
              receiverProfileId: receiver,
              text: OrderMessageDetails(
                orderId: order.id,
                totalAmount: order.totalAmount,
                quantity: quantity,
              ).serialize(),
            );
      }

      await ref.read(supabaseRfqRepositoryProvider).updateStatus(enquiry.id, EnquiryStatus.accepted);
      ref.invalidate(buyerOrdersProvider);
      ref.invalidate(enquiryProvider(enquiry.id));
      ref.invalidate(buyerEnquiriesProvider);
      if (!mounted) return;
      _showInfo('Order ${order.orderNumber} placed for ${CurrencyFormatter.formatINR(order.totalAmount)}');
    } catch (e) {
      if (!mounted) return;
      _showError(e);
    } finally {
      if (mounted) setState(() => _acceptingMessageId = null);
    }
  }

  // ---------------------------------------------------------------------------
  // Build
  // ---------------------------------------------------------------------------

  @override
  Widget build(BuildContext context) {
    final user = ref.watch(currentUserProvider);
    final enquiryAsync = ref.watch(enquiryProvider(widget.conversationId));

    if (user == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Chat')),
        body: const AppEmptyState(
          icon: Icons.lock_outline,
          title: 'Sign in to chat',
          message: 'Conversations are tied to your account.',
        ),
      );
    }

    return enquiryAsync.when(
      loading: () => Scaffold(
        appBar: AppBar(title: const Text('Chat')),
        body: const AppLoadingState(message: 'Opening conversation...'),
      ),
      error: (e, _) => Scaffold(
        appBar: AppBar(title: const Text('Chat')),
        body: AppErrorState(
          title: 'Could not open conversation',
          message: authErrorMessage(e),
          onRetry: () => ref.invalidate(enquiryProvider(widget.conversationId)),
        ),
      ),
      data: (enquiry) {
        if (enquiry == null) {
          return Scaffold(
            appBar: AppBar(title: const Text('Chat')),
            body: const AppErrorState(
              title: 'Conversation not found',
              message: 'This enquiry no longer exists or you do not have access to it.',
            ),
          );
        }
        WidgetsBinding.instance.addPostFrameCallback((_) => _resolveReceiver(enquiry, user));
        return _buildChat(context, enquiry, user);
      },
    );
  }

  Widget _buildChat(BuildContext context, Enquiry enquiry, UserModel user) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final isSellerSide = _isSellerSide(enquiry, user);
    final messagesAsync = ref.watch(enquiryMessagesProvider(enquiry.id));
    final messages = messagesAsync.valueOrNull;
    if (messages != null) _onMessages(messages, enquiry, user);

    final otherParty = isSellerSide ? 'Buyer enquiry' : (enquiry.sellerShopName ?? 'Artisan');
    final canOpenStorefront = !isSellerSide && enquiry.sellerId != null;
    final canQuote = isSellerSide &&
        (enquiry.status == EnquiryStatus.pending || enquiry.status == EnquiryStatus.quoted);
    final receiverKnown = _receiverResolvedForEnquiryId == enquiry.id;

    return Scaffold(
      appBar: AppBar(
        titleSpacing: 0,
        title: InkWell(
          onTap: canOpenStorefront ? () => context.push('/artisan/${enquiry.sellerId}') : null,
          borderRadius: AppRadius.borderSm,
          child: Row(
            children: [
              _HeaderAvatar(imageUrl: enquiry.productImageUrl, isSeller: isSellerSide, fallbackLabel: otherParty),
              AppSpacing.gapH10,
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      otherParty,
                      style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    if (enquiry.productTitle != null)
                      Text(
                        enquiry.productTitle!,
                        style: TextStyle(fontSize: 10, color: theme.colorScheme.onSurface.withValues(alpha: 0.65)),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                  ],
                ),
              ),
            ],
          ),
        ),
        actions: [
          if (canQuote)
            IconButton(
              icon: const Icon(Icons.request_quote_outlined),
              tooltip: 'Send quotation',
              onPressed: () => _openQuoteSheet(enquiry),
            ),
          if (canOpenStorefront)
            IconButton(
              icon: const Icon(Icons.storefront_outlined),
              tooltip: 'View storefront',
              onPressed: () => context.push('/artisan/${enquiry.sellerId}'),
            ),
        ],
      ),
      body: Column(
        children: [
          _EnquirySummaryBar(enquiry: enquiry, isDark: isDark),
          Expanded(
            child: messagesAsync.when(
              loading: () => const AppLoadingState(message: 'Loading messages...'),
              error: (e, _) => AppErrorState(
                title: 'Could not load messages',
                message: authErrorMessage(e),
                onRetry: () => ref.invalidate(enquiryMessagesProvider(enquiry.id)),
              ),
              data: (list) {
                if (list.isEmpty) {
                  return AppEmptyState(
                    icon: Icons.chat_bubble_outline,
                    title: 'No messages yet',
                    message: isSellerSide
                        ? 'Reply to the buyer or send a quotation to get started.'
                        : 'Say hello or ask the artisan about your enquiry.',
                  );
                }
                return ListView.builder(
                  controller: _scrollController,
                  padding: AppSpacing.paddingAllBase,
                  itemCount: list.length,
                  itemBuilder: (context, index) {
                    final msg = list[index];
                    final previous = index == 0 ? null : list[index - 1];
                    final showDay = previous == null || !_sameDay(previous.timestamp, msg.timestamp);
                    return Column(
                      children: [
                        if (showDay) _DayDivider(date: msg.timestamp),
                        Padding(
                          padding: const EdgeInsets.only(bottom: AppSpacing.md),
                          child: _buildMessage(msg, enquiry, user, isSellerSide, isDark),
                        ),
                      ],
                    );
                  },
                );
              },
            ),
          ),
          _buildInputBar(enquiry, user, isDark, receiverKnown: receiverKnown),
        ],
      ),
    );
  }

  static bool _sameDay(DateTime a, DateTime b) {
    final la = a.toLocal();
    final lb = b.toLocal();
    return la.year == lb.year && la.month == lb.month && la.day == lb.day;
  }

  Widget _buildInputBar(Enquiry enquiry, UserModel user, bool isDark, {required bool receiverKnown}) {
    final canSend = !_sending && receiverKnown && _receiverProfileId != null && user.profileId != null;
    final String? hint;
    if (!receiverKnown) {
      hint = 'Connecting to the conversation...';
    } else if (_receiverProfileId == null) {
      hint = 'Messaging is unavailable for this enquiry: the other participant has no profile.';
    } else if (enquiry.status == EnquiryStatus.rejected || enquiry.status == EnquiryStatus.closed) {
      hint = 'This enquiry is ${enquiry.status.label.toLowerCase()}. You can still send messages.';
    } else {
      hint = null;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: isDark ? AppColors.surfaceDark : Colors.white,
        border: Border(top: BorderSide(color: isDark ? AppColors.borderDark : AppColors.borderLight)),
      ),
      child: SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (hint != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Text(
                  hint,
                  style: const TextStyle(fontSize: 10, color: Colors.grey),
                  textAlign: TextAlign.center,
                ),
              ),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _textController,
                    focusNode: _inputFocus,
                    enabled: !_sending,
                    minLines: 1,
                    maxLines: 4,
                    textInputAction: TextInputAction.send,
                    decoration: InputDecoration(
                      hintText: 'Type a message...',
                      contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                      border: OutlineInputBorder(
                        borderRadius: AppRadius.borderPill,
                        borderSide: BorderSide(color: Colors.grey.shade400),
                      ),
                    ),
                    onSubmitted: canSend ? (_) => _send(enquiry, user) : null,
                  ),
                ),
                AppSpacing.gapH8,
                IconButton.filled(
                  style: IconButton.styleFrom(
                    backgroundColor: AppColors.primary,
                    disabledBackgroundColor: AppColors.primary.withValues(alpha: 0.35),
                  ),
                  icon: _sending
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                        )
                      : const Icon(Icons.send_rounded, size: 18, color: Colors.white),
                  onPressed: canSend ? () => _send(enquiry, user) : null,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Message renderers
  // ---------------------------------------------------------------------------

  Widget _buildMessage(ChatMessage msg, Enquiry enquiry, UserModel user, bool isSellerSide, bool isDark) {
    switch (msg.type) {
      case ChatMessageType.system:
        return _SystemBubble(text: msg.text);
      case ChatMessageType.quotation:
        return _buildQuotationBubble(msg, enquiry, user, isSellerSide, isDark);
      case ChatMessageType.order:
        return _buildOrderBubble(msg);
      case ChatMessageType.image:
        return _ImageBubble(message: msg, isDark: isDark);
      case ChatMessageType.text:
      case ChatMessageType.voice:
      case ChatMessageType.product:
      case ChatMessageType.rfq:
        return _TextBubble(message: msg, isDark: isDark);
    }
  }

  Widget _buildQuotationBubble(ChatMessage msg, Enquiry enquiry, UserModel user, bool isSellerSide, bool isDark) {
    final meta = msg.metadata ?? const <String, dynamic>{};
    final pricePerUnit = (meta['pricePerUnit'] as num?)?.toDouble();
    if (pricePerUnit == null) return _TextBubble(message: msg, isDark: isDark);
    final moq = (meta['moq'] as num?)?.toInt() ?? 1;
    final days = (meta['deliveryDays'] as num?)?.toInt() ?? 0;
    final terms = (meta['terms'] as String?)?.trim() ?? '';
    final orderQty = math.max(enquiry.quantity, moq);
    final total = pricePerUnit * orderQty;

    final canAccept = !isSellerSide &&
        (enquiry.status == EnquiryStatus.pending || enquiry.status == EnquiryStatus.quoted);
    final accepting = _acceptingMessageId == msg.id;
    final busy = _acceptingMessageId != null;

    return Align(
      alignment: msg.isMe ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: BoxConstraints(maxWidth: MediaQuery.sizeOf(context).width * 0.85),
        padding: AppSpacing.paddingAllBase,
        decoration: BoxDecoration(
          color: isDark ? AppColors.surfaceDark : Colors.white,
          borderRadius: AppRadius.borderLg,
          border: Border.all(color: AppColors.secondary, width: 1.5),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.08),
              blurRadius: 8,
              offset: const Offset(0, 3),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.receipt_long_rounded, color: AppColors.secondary, size: 20),
                AppSpacing.gapH8,
                Expanded(
                  child: Text(
                    msg.isMe ? 'Your quotation' : 'Quotation from ${msg.senderName}',
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppColors.secondary),
                  ),
                ),
              ],
            ),
            AppSpacing.gapV8,
            _QuoteLine(label: 'Price per unit', value: CurrencyFormatter.formatINR(pricePerUnit), bold: true),
            _QuoteLine(label: 'Minimum order', value: '$moq units'),
            _QuoteLine(label: 'Delivery', value: days > 0 ? '$days days' : 'To be confirmed'),
            _QuoteLine(label: 'Total for $orderQty units', value: CurrencyFormatter.formatINR(total), bold: true),
            if (terms.isNotEmpty) ...[
              AppSpacing.gapV8,
              Text(terms, style: TextStyle(fontSize: 12, height: 1.35, color: isDark ? AppColors.textSecondaryDark : AppColors.textSecondaryLight)),
            ],
            AppSpacing.gapV4,
            Text(
              DateFormat('h:mm a').format(msg.timestamp.toLocal()),
              style: const TextStyle(fontSize: 9, color: Colors.grey),
            ),
            if (canAccept) ...[
              AppSpacing.gapV12,
              Row(
                children: [
                  Expanded(
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.primary,
                        foregroundColor: Colors.white,
                        shape: AppRadius.shapePill,
                        padding: const EdgeInsets.symmetric(vertical: 8),
                      ),
                      onPressed: busy
                          ? null
                          : () => _acceptQuote(
                                message: msg,
                                enquiry: enquiry,
                                user: user,
                                pricePerUnit: pricePerUnit,
                                moq: moq,
                              ),
                      child: accepting
                          ? const SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                            )
                          : const Text('Accept & Place Order', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11)),
                    ),
                  ),
                  AppSpacing.gapH8,
                  OutlinedButton(
                    style: OutlinedButton.styleFrom(
                      shape: AppRadius.shapePill,
                      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
                    ),
                    onPressed: busy ? null : () => _inputFocus.requestFocus(),
                    child: const Text('Negotiate', style: TextStyle(fontSize: 11)),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildOrderBubble(ChatMessage msg) {
    final meta = msg.metadata ?? const <String, dynamic>{};
    final orderNumber = meta['orderNumber'] as String?;
    final total = (meta['totalAmount'] as num?)?.toDouble();
    final quantity = (meta['quantity'] as num?)?.toInt();

    return Center(
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 6),
        padding: AppSpacing.paddingAllBase,
        decoration: BoxDecoration(
          color: AppColors.successContainer.withValues(alpha: 0.3),
          borderRadius: AppRadius.borderMd,
          border: Border.all(color: AppColors.success),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.check_circle, color: AppColors.success, size: 18),
                SizedBox(width: 6),
                Text('ORDER CONFIRMED', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11, color: AppColors.success)),
              ],
            ),
            AppSpacing.gapV4,
            if (orderNumber != null)
              Text('Order $orderNumber', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
            Text(
              [
                if (quantity != null) '$quantity units',
                if (total != null) CurrencyFormatter.formatINR(total),
              ].join(' · '),
              style: const TextStyle(fontSize: 12),
            ),
            AppSpacing.gapV2,
            Text(
              DateFormat('d MMM, h:mm a').format(msg.timestamp.toLocal()),
              style: const TextStyle(fontSize: 9, color: Colors.grey),
            ),
            AppSpacing.gapV8,
            ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: AppColors.primary, foregroundColor: Colors.white),
              onPressed: () => context.go('/orders'),
              child: const Text('View orders', style: TextStyle(fontSize: 11)),
            ),
          ],
        ),
      ),
    );
  }
}

// -----------------------------------------------------------------------------
// Small presentational widgets
// -----------------------------------------------------------------------------

class _HeaderAvatar extends StatelessWidget {
  final String? imageUrl;
  final bool isSeller;
  final String fallbackLabel;

  const _HeaderAvatar({required this.imageUrl, required this.isSeller, required this.fallbackLabel});

  @override
  Widget build(BuildContext context) {
    final url = imageUrl;
    if (url != null && url.isNotEmpty) {
      return ClipRRect(
        borderRadius: AppRadius.borderSm,
        child: Image.network(
          url,
          width: 36,
          height: 36,
          fit: BoxFit.cover,
          errorBuilder: (_, __, ___) => const AppImagePlaceholder(width: 36, height: 36),
        ),
      );
    }
    final initial = fallbackLabel.trim().isEmpty ? '?' : fallbackLabel.trim()[0].toUpperCase();
    return CircleAvatar(
      radius: 18,
      backgroundColor: AppColors.primaryContainer,
      child: isSeller
          ? const Icon(Icons.person_outline, color: AppColors.primary, size: 18)
          : Text(initial, style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary)),
    );
  }
}

class _EnquirySummaryBar extends StatelessWidget {
  final Enquiry enquiry;
  final bool isDark;

  const _EnquirySummaryBar({required this.enquiry, required this.isDark});

  @override
  Widget build(BuildContext context) {
    final details = enquiry.details;
    final secondary = isDark ? AppColors.textSecondaryDark : AppColors.textSecondaryLight;
    final bits = <String>[
      '${enquiry.quantity} units',
      if (details.targetPricePerUnit != null) 'Target ${CurrencyFormatter.formatINR(details.targetPricePerUnit!)}/unit',
      'Budget ${CurrencyFormatter.formatINR(enquiry.targetBudget)}',
      if ((details.deliveryBy ?? '').isNotEmpty) 'By ${details.deliveryBy}',
    ];

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      color: AppColors.primaryContainer.withValues(alpha: isDark ? 0.15 : 0.25),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              EnquiryStatusChip(status: enquiry.status),
              AppSpacing.gapH8,
              Text(enquiry.rfqNumber, style: TextStyle(fontSize: 11, color: secondary, fontWeight: FontWeight.w600)),
            ],
          ),
          AppSpacing.gapV4,
          Text(
            details.title,
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          Text(
            bits.join(' · '),
            style: TextStyle(fontSize: 11, color: secondary),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }
}

class _DayDivider extends StatelessWidget {
  final DateTime date;

  const _DayDivider({required this.date});

  @override
  Widget build(BuildContext context) {
    final local = date.toLocal();
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final day = DateTime(local.year, local.month, local.day);
    final String label;
    if (day == today) {
      label = 'Today';
    } else if (day == today.subtract(const Duration(days: 1))) {
      label = 'Yesterday';
    } else {
      label = DateFormat(local.year == now.year ? 'EEE, d MMM' : 'd MMM yyyy').format(local);
    }
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.md),
      child: Center(
        child: Text(label, style: const TextStyle(fontSize: 10, color: Colors.grey, fontWeight: FontWeight.w600)),
      ),
    );
  }
}

class _SystemBubble extends StatelessWidget {
  final String text;

  const _SystemBubble({required this.text});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: AppColors.successContainer.withValues(alpha: 0.5),
          borderRadius: AppRadius.borderPill,
        ),
        child: Text(
          text,
          textAlign: TextAlign.center,
          style: const TextStyle(fontSize: 11, color: AppColors.success, fontWeight: FontWeight.bold),
        ),
      ),
    );
  }
}

class _TextBubble extends StatelessWidget {
  final ChatMessage message;
  final bool isDark;

  const _TextBubble({required this.message, required this.isDark});

  @override
  Widget build(BuildContext context) {
    final isMe = message.isMe;
    return Align(
      alignment: isMe ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: BoxConstraints(maxWidth: MediaQuery.sizeOf(context).width * 0.78),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: isMe ? AppColors.primary : (isDark ? AppColors.surfaceVariantDark : Colors.grey.shade200),
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: Radius.circular(isMe ? 16 : 4),
            bottomRight: Radius.circular(isMe ? 4 : 16),
          ),
        ),
        child: Column(
          crossAxisAlignment: isMe ? CrossAxisAlignment.end : CrossAxisAlignment.start,
          children: [
            Text(
              message.text,
              style: TextStyle(
                color: isMe ? Colors.white : (isDark ? Colors.white : Colors.black87),
                fontSize: 13,
                height: 1.35,
              ),
            ),
            AppSpacing.gapV4,
            Text(
              DateFormat('h:mm a').format(message.timestamp.toLocal()),
              style: TextStyle(color: isMe ? Colors.white70 : Colors.grey, fontSize: 9),
            ),
          ],
        ),
      ),
    );
  }
}

class _ImageBubble extends StatelessWidget {
  final ChatMessage message;
  final bool isDark;

  const _ImageBubble({required this.message, required this.isDark});

  @override
  Widget build(BuildContext context) {
    final url = message.metadata?['mediaUrl'] as String?;
    if (url == null || url.isEmpty) return _TextBubble(message: message, isDark: isDark);
    final isMe = message.isMe;
    final width = MediaQuery.sizeOf(context).width * 0.6;
    return Align(
      alignment: isMe ? Alignment.centerRight : Alignment.centerLeft,
      child: Column(
        crossAxisAlignment: isMe ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        children: [
          ClipRRect(
            borderRadius: AppRadius.borderMd,
            child: Image.network(
              url,
              width: width,
              fit: BoxFit.cover,
              errorBuilder: (_, __, ___) => AppImagePlaceholder(width: width, height: width * 0.75),
            ),
          ),
          if (message.text.trim().isNotEmpty) ...[
            AppSpacing.gapV4,
            _TextBubble(message: message, isDark: isDark),
          ] else ...[
            AppSpacing.gapV2,
            Text(
              DateFormat('h:mm a').format(message.timestamp.toLocal()),
              style: const TextStyle(color: Colors.grey, fontSize: 9),
            ),
          ],
        ],
      ),
    );
  }
}

class _QuoteLine extends StatelessWidget {
  final String label;
  final String value;
  final bool bold;

  const _QuoteLine({required this.label, required this.value, this.bold = false});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 2),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey)),
          AppSpacing.gapH12,
          Text(value, style: TextStyle(fontSize: 12, fontWeight: bold ? FontWeight.bold : FontWeight.w500)),
        ],
      ),
    );
  }
}
