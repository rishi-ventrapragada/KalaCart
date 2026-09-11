import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../../../shared/models/chat_rfq_models.dart';
import '../../../shared/models/enquiry_models.dart';
import '../../auth/data/auth_repository.dart';
import '../../auth/data/supabase_auth_repository.dart';

/// Chat is scoped to an enquiry: every conversation is one `enquiries` row and
/// its `messages`. `sender_id` / `receiver_id` are `profiles.id` values.
class SupabaseChatRepository {
  final SupabaseClient _client;

  SupabaseChatRepository(this._client);

  ChatMessage _mapRow(Map<String, dynamic> row, {required String myProfileId, Map<String, String> names = const {}}) {
    final senderId = row['sender_id'] as String? ?? '';
    final text = row['message'] as String? ?? '';
    final isMe = senderId == myProfileId;

    ChatMessageType type = ChatMessageType.text;
    Map<String, dynamic>? metadata;

    final quote = QuoteDetails.tryParse(text);
    final order = OrderMessageDetails.tryParse(text);
    if (quote != null) {
      type = ChatMessageType.quotation;
      metadata = {
        'pricePerUnit': quote.pricePerUnit,
        'moq': quote.moq,
        'deliveryDays': quote.deliveryDays,
        'terms': quote.note,
      };
    } else if (order != null) {
      type = ChatMessageType.order;
      metadata = {
        'orderId': order.orderId,
        'orderNumber': 'KC-${order.orderId.replaceAll('-', '').substring(0, 8).toUpperCase()}',
        'totalAmount': order.totalAmount,
        'quantity': order.quantity,
      };
    } else if ((row['media_url'] as String?)?.isNotEmpty == true) {
      type = ChatMessageType.image;
      metadata = {'mediaUrl': row['media_url']};
    }

    return ChatMessage(
      id: row['id'] as String,
      conversationId: row['enquiry_id'] as String? ?? '',
      senderId: senderId,
      senderName: isMe ? 'You' : (names[senderId] ?? 'Participant'),
      isMe: isMe,
      type: type,
      text: text,
      timestamp: DateTime.tryParse(row['created_at']?.toString() ?? '') ?? DateTime.now(),
      metadata: metadata,
    );
  }

  Future<List<ChatMessage>> getMessages({required String enquiryId, required String myProfileId}) async {
    final res = await _client
        .from('messages')
        .select()
        .eq('enquiry_id', enquiryId)
        .order('created_at', ascending: true);
    final rows = (res as List).cast<Map<String, dynamic>>();
    final names = await _resolveNames(rows);
    return rows.map((r) => _mapRow(r, myProfileId: myProfileId, names: names)).toList();
  }

  /// Realtime stream of a conversation's messages.
  Stream<List<ChatMessage>> streamMessages({required String enquiryId, required String myProfileId}) {
    return _client
        .from('messages')
        .stream(primaryKey: ['id'])
        .eq('enquiry_id', enquiryId)
        .order('created_at', ascending: true)
        .asyncMap((rows) async {
          final list = rows.cast<Map<String, dynamic>>();
          final names = await _resolveNames(list);
          return list.map((r) => _mapRow(r, myProfileId: myProfileId, names: names)).toList();
        });
  }

  Future<Map<String, String>> _resolveNames(List<Map<String, dynamic>> rows) async {
    final ids = rows.map((r) => r['sender_id'] as String?).whereType<String>().toSet().toList();
    if (ids.isEmpty) return const {};
    try {
      final res = await _client.from('profiles').select('id, full_name').inFilter('id', ids);
      return {
        for (final p in (res as List).cast<Map<String, dynamic>>())
          p['id'] as String: (p['full_name'] as String?) ?? 'Participant',
      };
    } catch (_) {
      return const {};
    }
  }

  Future<void> sendMessage({
    required String enquiryId,
    required String senderProfileId,
    required String receiverProfileId,
    required String text,
    String? mediaUrl,
  }) async {
    await _client.from('messages').insert({
      'sender_id': senderProfileId,
      'receiver_id': receiverProfileId,
      'enquiry_id': enquiryId,
      'message': text,
      'media_url': mediaUrl,
      'is_read': false,
    });
  }

  /// `profiles.id` for an auth user id (needed because `enquiries.buyer_id`
  /// stores the auth id while `messages.receiver_id` needs the profile id).
  Future<String?> profileIdForAuthUser(String authUserId) async {
    try {
      final row = await _client.from('profiles').select('id').eq('auth_user_id', authUserId).maybeSingle();
      return row?['id'] as String?;
    } catch (_) {
      return null;
    }
  }

  Future<void> markRead({required String enquiryId, required String myProfileId}) async {
    try {
      await _client
          .from('messages')
          .update({'is_read': true})
          .eq('enquiry_id', enquiryId)
          .eq('receiver_id', myProfileId)
          .eq('is_read', false);
    } catch (_) {}
  }

  /// Unread message counts per enquiry for the signed-in profile.
  Future<Map<String, int>> unreadCounts(String myProfileId) async {
    try {
      final res = await _client
          .from('messages')
          .select('enquiry_id')
          .eq('receiver_id', myProfileId)
          .eq('is_read', false);
      final counts = <String, int>{};
      for (final r in (res as List).cast<Map<String, dynamic>>()) {
        final id = r['enquiry_id'] as String?;
        if (id != null) counts[id] = (counts[id] ?? 0) + 1;
      }
      return counts;
    } catch (_) {
      return const {};
    }
  }

  /// Last message per enquiry, used for the conversation list preview.
  Future<Map<String, ChatMessage>> lastMessages(List<String> enquiryIds, {required String myProfileId}) async {
    if (enquiryIds.isEmpty) return const {};
    final res = await _client
        .from('messages')
        .select()
        .inFilter('enquiry_id', enquiryIds)
        .order('created_at', ascending: false);
    final result = <String, ChatMessage>{};
    for (final r in (res as List).cast<Map<String, dynamic>>()) {
      final id = r['enquiry_id'] as String?;
      if (id != null && !result.containsKey(id)) {
        result[id] = _mapRow(r, myProfileId: myProfileId);
      }
    }
    return result;
  }
}

final supabaseChatRepositoryProvider = Provider<SupabaseChatRepository>((ref) {
  return SupabaseChatRepository(ref.watch(supabaseClientProvider));
});

/// Live message list for one enquiry, for the signed-in user.
final enquiryMessagesProvider = StreamProvider.autoDispose.family<List<ChatMessage>, String>((ref, enquiryId) {
  final user = ref.watch(currentUserProvider);
  final profileId = user?.profileId;
  if (profileId == null) return Stream.value(const []);
  return ref.watch(supabaseChatRepositoryProvider).streamMessages(enquiryId: enquiryId, myProfileId: profileId);
});
