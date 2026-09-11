import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/widgets/app_empty_state.dart';
import '../../../core/widgets/app_error_state.dart';
import '../../../core/widgets/app_loading_state.dart';
import '../../../shared/models/chat_rfq_models.dart';
import '../../../shared/models/enquiry_models.dart';
import '../../../shared/services/user_role_service.dart';
import '../../auth/data/auth_repository.dart';
import '../../auth/data/supabase_auth_repository.dart';
import '../../rfq/data/supabase_rfq_repository.dart';
import '../data/supabase_chat_repository.dart';

/// One row of the conversation list: an enquiry plus its chat preview data.
class _ConversationItem {
  final Enquiry enquiry;
  final ChatMessage? lastMessage;
  final int unreadCount;

  const _ConversationItem({required this.enquiry, this.lastMessage, this.unreadCount = 0});

  DateTime get lastActivity => lastMessage?.timestamp ?? enquiry.createdAt;
}

/// Enquiries for the signed-in user (buyer or seller side) joined with their
/// last message and unread count, sorted by most recent activity.
final _conversationsProvider = FutureProvider.autoDispose<List<_ConversationItem>>((ref) async {
  final user = ref.watch(currentUserProvider);
  final isSeller = ref.watch(userRoleProvider).isArtisanSeller;
  final enquiries = await ref.watch(isSeller ? sellerEnquiriesProvider.future : buyerEnquiriesProvider.future);

  final profileId = user?.profileId;
  if (profileId == null || enquiries.isEmpty) {
    return [for (final e in enquiries) _ConversationItem(enquiry: e)];
  }

  final chat = ref.watch(supabaseChatRepositoryProvider);
  final ids = enquiries.map((e) => e.id).toList();
  final lastMessages = await chat.lastMessages(ids, myProfileId: profileId);
  final unread = await chat.unreadCounts(profileId);

  final items = [
    for (final e in enquiries)
      _ConversationItem(enquiry: e, lastMessage: lastMessages[e.id], unreadCount: unread[e.id] ?? 0),
  ]..sort((a, b) => b.lastActivity.compareTo(a.lastActivity));
  return items;
});

class ConversationListScreen extends ConsumerWidget {
  const ConversationListScreen({super.key});

  Future<void> _refresh(WidgetRef ref, bool isSeller) async {
    ref.invalidate(isSeller ? sellerEnquiriesProvider : buyerEnquiriesProvider);
    ref.invalidate(_conversationsProvider);
    try {
      await ref.read(_conversationsProvider.future);
    } catch (_) {
      // Error surfaces through the provider's error state.
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final isSeller = ref.watch(userRoleProvider).isArtisanSeller;
    final conversationsAsync = ref.watch(_conversationsProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(isSeller ? 'Buyer Messages' : 'Artisan Messages'),
      ),
      body: conversationsAsync.when(
        loading: () => const AppLoadingState(message: 'Loading conversations...'),
        error: (e, _) => AppErrorState(
          title: 'Could not load conversations',
          message: authErrorMessage(e),
          onRetry: () => _refresh(ref, isSeller),
        ),
        data: (items) => RefreshIndicator(
          onRefresh: () => _refresh(ref, isSeller),
          child: items.isEmpty
              ? ListView(
                  children: [
                    SizedBox(
                      height: MediaQuery.sizeOf(context).height * 0.7,
                      child: AppEmptyState(
                        icon: Icons.chat_outlined,
                        title: 'No conversations yet',
                        message: isSeller
                            ? 'When buyers enquire about your crafts, the conversation appears here.'
                            : 'Send an enquiry about a craft to start chatting with its artisan.',
                        actionLabel: isSeller ? null : 'New Enquiry',
                        onAction: isSeller ? null : () => context.push('/rfq/create'),
                      ),
                    ),
                  ],
                )
              : ListView.separated(
                  itemCount: items.length,
                  separatorBuilder: (_, __) => const Divider(height: 1),
                  itemBuilder: (context, index) => _ConversationTile(
                    item: items[index],
                    isSeller: isSeller,
                    isDark: isDark,
                  ),
                ),
        ),
      ),
    );
  }
}

class _ConversationTile extends StatelessWidget {
  final _ConversationItem item;
  final bool isSeller;
  final bool isDark;

  const _ConversationTile({required this.item, required this.isSeller, required this.isDark});

  static String previewFor(ChatMessage? message, Enquiry enquiry) {
    if (message == null) return enquiry.details.title;
    switch (message.type) {
      case ChatMessageType.quotation:
        return message.isMe ? 'Quotation sent' : 'Quotation received';
      case ChatMessageType.order:
        return 'Order confirmed';
      case ChatMessageType.image:
        return message.text.trim().isEmpty ? 'Photo' : message.text;
      case ChatMessageType.text:
      case ChatMessageType.voice:
      case ChatMessageType.product:
      case ChatMessageType.rfq:
      case ChatMessageType.system:
        return message.text.trim().isEmpty ? enquiry.details.title : message.text;
    }
  }

  static String relativeTime(DateTime time) {
    final now = DateTime.now();
    final diff = now.difference(time.toLocal());
    if (diff.inMinutes < 1) return 'now';
    if (diff.inHours < 1) return '${diff.inMinutes}m';
    if (diff.inDays < 1) return '${diff.inHours}h';
    if (diff.inDays < 7) return '${diff.inDays}d';
    if (time.year == now.year) return DateFormat('d MMM').format(time.toLocal());
    return DateFormat('d MMM yy').format(time.toLocal());
  }

  @override
  Widget build(BuildContext context) {
    final enquiry = item.enquiry;
    final title = isSeller ? 'Buyer enquiry' : (enquiry.sellerShopName ?? 'Artisan');
    final contextLine = [
      enquiry.rfqNumber,
      if (enquiry.productTitle != null) enquiry.productTitle!,
    ].join(' · ');
    final preview = previewFor(item.lastMessage, enquiry);
    final hasUnread = item.unreadCount > 0;
    final secondary = isDark ? AppColors.textSecondaryDark : AppColors.textSecondaryLight;
    final initial = title.trim().isEmpty ? '?' : title.trim()[0].toUpperCase();

    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      leading: CircleAvatar(
        radius: 26,
        backgroundColor: AppColors.primaryContainer,
        child: isSeller
            ? const Icon(Icons.person_outline, color: AppColors.primary)
            : Text(
                initial,
                style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary, fontSize: 18),
              ),
      ),
      title: Row(
        children: [
          Expanded(
            child: Text(
              title,
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          AppSpacing.gapH8,
          Text(
            relativeTime(item.lastActivity),
            style: TextStyle(fontSize: 10, color: hasUnread ? AppColors.primary : secondary),
          ),
        ],
      ),
      subtitle: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            contextLine,
            style: const TextStyle(fontSize: 11, color: AppColors.primary, fontWeight: FontWeight.w600),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          AppSpacing.gapV2,
          Text(
            preview,
            style: TextStyle(
              fontSize: 12,
              color: secondary,
              fontWeight: hasUnread ? FontWeight.bold : FontWeight.normal,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
      trailing: hasUnread
          ? Container(
              padding: const EdgeInsets.all(6),
              decoration: const BoxDecoration(
                color: AppColors.primary,
                shape: BoxShape.circle,
              ),
              child: Text(
                '${item.unreadCount}',
                style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
              ),
            )
          : null,
      onTap: () => context.push('/chat/${enquiry.id}'),
    );
  }
}
