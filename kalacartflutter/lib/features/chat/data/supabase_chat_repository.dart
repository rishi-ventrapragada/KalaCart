import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../../../shared/models/chat_rfq_models.dart';
import '../../auth/data/supabase_auth_repository.dart';

class SupabaseChatRepository {
  final SupabaseClient _client;

  SupabaseChatRepository(this._client);

  /// Fetch messages for a specific conversation / enquiry
  Future<List<ChatMessage>> getMessages({required String enquiryId}) async {
    try {
      final res = await _client
          .from('messages')
          .select()
          .eq('enquiry_id', enquiryId)
          .order('created_at', ascending: true);

      return (res as List).map((row) {
        final currentUserId = _client.auth.currentUser?.id;
        final senderId = row['sender_id'] as String;

        return ChatMessage(
          id: row['id'] as String,
          conversationId: enquiryId,
          senderId: senderId,
          senderName: senderId == currentUserId ? 'You' : 'Artisan',
          text: row['message'] as String? ?? '',
          timestamp: row['created_at'] != null ? DateTime.parse(row['created_at']) : DateTime.now(),
          type: ChatMessageType.text,
          isMe: senderId == currentUserId,
        );
      }).toList();
    } catch (_) {
      return [];
    }
  }

  /// Subscribe to real-time chat messages
  Stream<List<ChatMessage>> streamMessages({required String enquiryId}) {
    return _client
        .from('messages')
        .stream(primaryKey: ['id'])
        .eq('enquiry_id', enquiryId)
        .order('created_at', ascending: true)
        .map((rows) {
          final currentUserId = _client.auth.currentUser?.id;
          return rows.map((row) {
            final senderId = row['sender_id'] as String;
            return ChatMessage(
              id: row['id'] as String,
              conversationId: enquiryId,
              senderId: senderId,
              senderName: senderId == currentUserId ? 'You' : 'Artisan',
              text: row['message'] as String? ?? '',
              timestamp: row['created_at'] != null ? DateTime.parse(row['created_at']) : DateTime.now(),
              type: ChatMessageType.text,
              isMe: senderId == currentUserId,
            );
          }).toList();
        });
  }

  /// Send a chat message
  Future<void> sendMessage({
    required String receiverId,
    required String enquiryId,
    required String text,
    String? mediaUrl,
  }) async {
    final user = _client.auth.currentUser;
    if (user == null) return;

    await _client.from('messages').insert({
      'sender_id': user.id,
      'receiver_id': receiverId,
      'enquiry_id': enquiryId,
      'message': text,
      'media_url': mediaUrl,
      'is_read': false,
    });
  }
}

final supabaseChatRepositoryProvider = Provider<SupabaseChatRepository>((ref) {
  return SupabaseChatRepository(ref.watch(supabaseClientProvider));
});
