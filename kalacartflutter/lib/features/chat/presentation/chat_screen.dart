import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/utils/currency_formatter.dart';
import '../../../shared/models/chat_rfq_models.dart';
import '../../rfq/data/rfq_chat_repository.dart';

class ChatScreen extends ConsumerStatefulWidget {
  final String conversationId;

  const ChatScreen({super.key, required this.conversationId});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final TextEditingController _textController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  @override
  void dispose() {
    _textController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _sendMessage({String? customText, ChatMessageType type = ChatMessageType.text, Map<String, dynamic>? metadata}) {
    final text = customText ?? _textController.text.trim();
    if (text.isEmpty && metadata == null) return;

    final newMsg = ChatMessage(
      id: 'msg-${DateTime.now().millisecondsSinceEpoch}',
      conversationId: widget.conversationId,
      senderId: 'buyer-01',
      senderName: 'You',
      isMe: true,
      type: type,
      text: text,
      timestamp: DateTime.now(),
      metadata: metadata,
    );

    ref.read(chatMessagesProvider.notifier).sendMessage(widget.conversationId, newMsg);
    ref.read(chatConversationsProvider.notifier).updateLastMessage(widget.conversationId, text);

    _textController.clear();
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final messagesMap = ref.watch(chatMessagesProvider);
    final messages = messagesMap[widget.conversationId] ?? [];

    return Scaffold(
      appBar: AppBar(
        titleSpacing: 0,
        title: Row(
          children: [
            const CircleAvatar(
              radius: 18,
              backgroundColor: AppColors.primaryContainer,
              child: Text('🏺', style: TextStyle(fontSize: 16)),
            ),
            AppSpacing.gapH10,
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Dr. Kripal Kumbh Studio',
                    style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                  ),
                  Text(
                    'Jaipur Blue Pottery Cluster · Active now',
                    style: TextStyle(fontSize: 10, color: Colors.green.shade600, fontWeight: FontWeight.bold),
                  ),
                ],
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.call_outlined),
            tooltip: 'Audio Call with Live Translation',
            onPressed: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Starting AI real-time translated voice session (Hindi <-> English)...')),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.storefront_outlined),
            tooltip: 'View Storefront',
            onPressed: () => context.push('/artisan/art-002'),
          ),
        ],
      ),
      body: Column(
        children: [
          // Translation Active Banner
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
            color: AppColors.primaryContainer.withValues(alpha: 0.25),
            child: const Row(
              children: [
                Icon(Icons.translate, size: 14, color: AppColors.primary),
                SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Kala-AI Auto Translation Active: English ⇄ Hindi',
                    style: TextStyle(fontSize: 11, color: AppColors.primary, fontWeight: FontWeight.bold),
                  ),
                ),
              ],
            ),
          ),

          // Message Stream
          Expanded(
            child: ListView.separated(
              controller: _scrollController,
              padding: AppSpacing.paddingAllBase,
              itemCount: messages.length,
              separatorBuilder: (_, __) => AppSpacing.gapV12,
              itemBuilder: (context, index) {
                final msg = messages[index];
                return _buildMessageBubble(msg, theme, isDark);
              },
            ),
          ),

          // Input Bar
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: isDark ? AppColors.surfaceDark : Colors.white,
              border: Border(top: BorderSide(color: isDark ? AppColors.borderDark : AppColors.borderLight)),
            ),
            child: SafeArea(
              child: Row(
                children: [
                  IconButton(
                    icon: const Icon(Icons.add_circle_outline, color: AppColors.primary),
                    onPressed: () => _showAttachmentOptions(context),
                  ),
                  Expanded(
                    child: TextField(
                      controller: _textController,
                      decoration: InputDecoration(
                        hintText: 'Type message or RFQ query...',
                        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                        border: OutlineInputBorder(
                          borderRadius: AppRadius.borderPill,
                          borderSide: BorderSide(color: Colors.grey.shade400),
                        ),
                      ),
                      onSubmitted: (_) => _sendMessage(),
                    ),
                  ),
                  AppSpacing.gapH8,
                  IconButton(
                    icon: const Icon(Icons.mic_outlined, color: AppColors.primary),
                    onPressed: () {
                      _sendMessage(
                        customText: '🎤 Audio voice note (0:24) with Hindi translation attached.',
                        type: ChatMessageType.voice,
                      );
                    },
                  ),
                  IconButton.filled(
                    style: IconButton.styleFrom(backgroundColor: AppColors.primary),
                    icon: const Icon(Icons.send_rounded, size: 18, color: Colors.white),
                    onPressed: () => _sendMessage(),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMessageBubble(ChatMessage msg, ThemeData theme, bool isDark) {
    if (msg.type == ChatMessageType.system) {
      return Center(
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: BoxDecoration(
            color: Colors.green.shade50,
            borderRadius: AppRadius.borderPill,
            border: Border.all(color: Colors.green.shade200),
          ),
          child: Text(
            msg.text,
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 11, color: Colors.green.shade900, fontWeight: FontWeight.bold),
          ),
        ),
      );
    }

    if (msg.type == ChatMessageType.quotation) {
      return _buildQuotationBubble(msg, isDark);
    }

    if (msg.type == ChatMessageType.order) {
      return _buildOrderBubble(msg, isDark);
    }

    final isMe = msg.isMe;

    return Align(
      alignment: isMe ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.78),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: isMe ? AppColors.primary : (isDark ? AppColors.surfaceDark : Colors.grey.shade200),
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
              msg.text,
              style: TextStyle(
                color: isMe ? Colors.white : (isDark ? Colors.white : Colors.black87),
                fontSize: 13,
                height: 1.35,
              ),
            ),
            AppSpacing.gapV4,
            Text(
              '${msg.timestamp.hour.toString().padLeft(2, '0')}:${msg.timestamp.minute.toString().padLeft(2, '0')}',
              style: TextStyle(
                color: isMe ? Colors.white70 : Colors.grey,
                fontSize: 9,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildQuotationBubble(ChatMessage msg, bool isDark) {
    final metadata = msg.metadata ?? {};
    final pricePerUnit = (metadata['pricePerUnit'] as num?)?.toDouble() ?? 1350.0;
    final moq = (metadata['moq'] as num?)?.toInt() ?? 50;
    final days = (metadata['deliveryDays'] as num?)?.toInt() ?? 28;

    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.85),
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
            const Row(
              children: [
                Icon(Icons.receipt_long_rounded, color: AppColors.secondary, size: 20),
                AppSpacing.gapH8,
                Text('Formal Master Guild Quotation', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppColors.secondary)),
              ],
            ),
            AppSpacing.gapV8,
            Text(msg.text, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
            AppSpacing.gapV4,
            Text('• Price Per Unit: ${CurrencyFormatter.formatINR(pricePerUnit)}', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
            Text('• Minimum Order Qty (MOQ): $moq Units', style: const TextStyle(fontSize: 12)),
            Text('• Production Timeline: $days Days', style: const TextStyle(fontSize: 12)),
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
                    onPressed: () {
                      ref.read(chatMessagesProvider.notifier).acceptQuotationAndCreateOrder(
                            ref: ref,
                            conversationId: widget.conversationId,
                            rfqId: 'rfq-203',
                            pricePerUnit: pricePerUnit,
                            quantity: moq,
                            craftTitle: 'Royal Blue Pottery Plates',
                          );
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text('🎉 Quotation Accepted! Order #KC-2026-89215 confirmed.'),
                          behavior: SnackBarBehavior.floating,
                        ),
                      );
                    },
                    child: const Text('Accept & Place Order', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11)),
                  ),
                ),
                AppSpacing.gapH8,
                OutlinedButton(
                  style: OutlinedButton.styleFrom(
                    shape: AppRadius.shapePill,
                    padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
                  ),
                  onPressed: () {
                    _sendMessage(
                      customText: 'Could we negotiate to ₹1,250/unit for an increased batch of 150 units?',
                    );
                  },
                  child: const Text('Negotiate', style: TextStyle(fontSize: 11)),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildOrderBubble(ChatMessage msg, bool isDark) {
    final meta = msg.metadata ?? {};
    final orderNum = meta['orderNumber'] ?? 'KC-2026-89215';
    final total = (meta['totalAmount'] as num?)?.toDouble() ?? 67500.0;

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
          children: [
            const Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.check_circle, color: AppColors.success, size: 18),
                SizedBox(width: 6),
                Text('ORDER IN ESCROW TRANSIT', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11, color: AppColors.success)),
              ],
            ),
            AppSpacing.gapV4,
            Text('Order #$orderNum (${CurrencyFormatter.formatINR(total)})', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
            AppSpacing.gapV8,
            ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: AppColors.primary, foregroundColor: Colors.white),
              onPressed: () => context.push('/orders'),
              child: const Text('Track Order Status', style: TextStyle(fontSize: 11)),
            ),
          ],
        ),
      ),
    );
  }

  void _showAttachmentOptions(BuildContext context) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return Padding(
          padding: AppSpacing.paddingAllLg,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text('Share Commerce Attachment', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
              AppSpacing.gapV16,
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  _buildAttachTile(Icons.shopping_bag_outlined, 'Share Product', AppColors.primary, () {
                    Navigator.pop(context);
                    _sendMessage(
                      customText: 'Referencing Craft: Heritage Cobalt Floral Blue Pottery Vase (GI Tagged)',
                      type: ChatMessageType.product,
                    );
                  }),
                  _buildAttachTile(Icons.handshake_outlined, 'Send RFQ Spec', AppColors.secondary, () {
                    Navigator.pop(context);
                    _sendMessage(
                      customText: 'Custom Spec: Need 100 units with custom corporate engraving.',
                      type: ChatMessageType.rfq,
                    );
                  }),
                  _buildAttachTile(Icons.camera_alt_outlined, 'Send Photo', Colors.blue, () {
                    Navigator.pop(context);
                    _sendMessage(
                      customText: '📷 Reference sample image sent.',
                      type: ChatMessageType.image,
                    );
                  }),
                  _buildAttachTile(Icons.verified_outlined, 'Craft Passport', AppColors.success, () {
                    Navigator.pop(context);
                    _sendMessage(
                      customText: '📜 Mapped Digital Craft Passport #GI-IN-RAJ-2026-BP-0941',
                      type: ChatMessageType.system,
                    );
                  }),
                ],
              ),
              AppSpacing.gapV16,
            ],
          ),
        );
      },
    );
  }

  Widget _buildAttachTile(IconData icon, String label, Color color, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(color: color.withValues(alpha: 0.15), shape: BoxShape.circle),
            child: Icon(icon, color: color, size: 24),
          ),
          const SizedBox(height: 6),
          Text(label, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }
}
