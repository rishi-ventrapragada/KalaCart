import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../shared/models/chat_rfq_models.dart';

// Buyer RFQs Notifier
class BuyerRfqNotifier extends StateNotifier<List<BuyerRfqSubmission>> {
  BuyerRfqNotifier()
      : super([
          BuyerRfqSubmission(
            id: 'brfq-01',
            title: '50 Pcs Hand-Painted Madhubani Silk Scarves',
            category: 'Handloom & Textiles',
            quantity: 50,
            targetPricePerUnit: 1300,
            deliveryRequiredBy: 'Within 20 Days',
            destinationPincode: '110057 (New Delhi)',
            customizationNotes: 'Require custom natural botanical border with wedding initials printed discreetly on corner.',
            hasVoiceNote: true,
            status: 'quotes_received',
            createdAt: DateTime.now().subtract(const Duration(days: 2)),
          ),
          BuyerRfqSubmission(
            id: 'brfq-02',
            title: '100 Units Cobalt Blue Pottery Coffee Mugs',
            category: 'Pottery & Terracotta',
            quantity: 100,
            targetPricePerUnit: 450,
            deliveryRequiredBy: 'Within 30 Days',
            destinationPincode: '560038 (Bengaluru)',
            customizationNotes: 'Lead-free food grade glaze with corporate logo stamped at base.',
            status: 'open',
            createdAt: DateTime.now().subtract(const Duration(days: 5)),
          ),
        ]);

  void submitBuyerRfq(BuyerRfqSubmission rfq) {
    state = [rfq, ...state];
  }
}

final buyerRfqProvider = StateNotifierProvider<BuyerRfqNotifier, List<BuyerRfqSubmission>>((ref) {
  return BuyerRfqNotifier();
});

// Chat Conversations Notifier
class ChatConversationNotifier extends StateNotifier<List<Conversation>> {
  ChatConversationNotifier()
      : super([
          Conversation(
            id: 'conv-01',
            otherPartyId: 'art-002',
            otherPartyName: 'Dr. Kripal Kumbh Studio',
            otherPartyRole: 'Master Artisan Guild',
            craftCluster: 'Jaipur Blue Pottery Cluster, Rajasthan',
            lastMessage: 'Quotation of ₹1,350/unit accepted! We have begun kiln preparations.',
            lastMessageTime: DateTime.now().subtract(const Duration(minutes: 12)),
            unreadCount: 1,
            relatedRfqId: 'rfq-203',
            relatedOrderId: 'ord-103',
          ),
          Conversation(
            id: 'conv-02',
            otherPartyId: 'art-004',
            otherPartyName: 'Pedana Kalamkari Collective',
            otherPartyRole: 'Master Handloom Society',
            craftCluster: 'Pedana Krishna River Cluster',
            lastMessage: 'Natural indigo dye batch has been fermented for your silk batch.',
            lastMessageTime: DateTime.now().subtract(const Duration(hours: 4)),
            unreadCount: 0,
          ),
        ]);

  void addConversation(Conversation conv) {
    state = [conv, ...state.where((c) => c.id != conv.id)];
  }

  void updateLastMessage(String convId, String message) {
    state = state.map((c) {
      if (c.id == convId) {
        return c.copyWith(lastMessage: message, lastMessageTime: DateTime.now());
      }
      return c;
    }).toList();
  }
}

final chatConversationsProvider = StateNotifierProvider<ChatConversationNotifier, List<Conversation>>((ref) {
  return ChatConversationNotifier();
});

// Chat Messages State for active conversation
class ChatMessagesNotifier extends StateNotifier<Map<String, List<ChatMessage>>> {
  ChatMessagesNotifier()
      : super({
          'conv-01': [
            ChatMessage(
              id: 'msg-01',
              conversationId: 'conv-01',
              senderId: 'buyer-01',
              senderName: 'Wholesale Buyer',
              isMe: true,
              type: ChatMessageType.rfq,
              text: 'Custom RFQ: 100 Pcs Royal Blue Pottery Plates',
              timestamp: DateTime.now().subtract(const Duration(days: 3)),
              metadata: const {
                'rfqNumber': 'RFQ-IN-2026-074',
                'quantity': 100,
                'targetBudget': 150000,
              },
            ),
            ChatMessage(
              id: 'msg-02',
              conversationId: 'conv-01',
              senderId: 'art-002',
              senderName: 'Dr. Kripal Kumbh Studio',
              isMe: false,
              type: ChatMessageType.quotation,
              text: 'Master Guild Formal Quotation Submitted',
              timestamp: DateTime.now().subtract(const Duration(days: 2)),
              metadata: const {
                'pricePerUnit': 1350.0,
                'moq': 50,
                'deliveryDays': 28,
                'terms': 'GI Tagged Makrana Quartz with low-fire kiln glazes.',
              },
            ),
            ChatMessage(
              id: 'msg-03',
              conversationId: 'conv-01',
              senderId: 'buyer-01',
              senderName: 'Wholesale Buyer',
              isMe: true,
              type: ChatMessageType.system,
              text: '✅ Quotation Accepted! Order #KC-2026-89215 created via KalaCart Escrow.',
              timestamp: DateTime.now().subtract(const Duration(days: 1)),
            ),
            ChatMessage(
              id: 'msg-04',
              conversationId: 'conv-01',
              senderId: 'art-002',
              senderName: 'Dr. Kripal Kumbh Studio',
              isMe: false,
              type: ChatMessageType.text,
              text: 'Namaste! We have prepared the Makrana quartz mixture and will fire the first 25 pieces on Monday. Digital Craft Passport is mapped.',
              timestamp: DateTime.now().subtract(const Duration(minutes: 12)),
            ),
          ],
        });

  void sendMessage(String conversationId, ChatMessage message) {
    final currentList = state[conversationId] ?? [];
    state = {
      ...state,
      conversationId: [...currentList, message],
    };
  }

  void acceptQuotationAndCreateOrder({
    required WidgetRef ref,
    required String conversationId,
    required String rfqId,
    required double pricePerUnit,
    required int quantity,
    required String craftTitle,
  }) {
    final orderNumber = 'KC-2026-${DateTime.now().millisecondsSinceEpoch.toString().substring(7)}';

    // 1. Add system confirmation message in chat
    sendMessage(
      conversationId,
      ChatMessage(
        id: 'msg-${DateTime.now().millisecondsSinceEpoch}',
        conversationId: conversationId,
        senderId: 'system',
        senderName: 'KalaCart Commerce Engine',
        isMe: true,
        type: ChatMessageType.order,
        text: '🎉 Quotation Accepted! Order #$orderNumber has been confirmed and escrow payment held.',
        timestamp: DateTime.now(),
        metadata: {
          'orderNumber': orderNumber,
          'totalAmount': pricePerUnit * quantity,
          'quantity': quantity,
          'craftTitle': craftTitle,
        },
      ),
    );
  }
}

final chatMessagesProvider = StateNotifierProvider<ChatMessagesNotifier, Map<String, List<ChatMessage>>>((ref) {
  return ChatMessagesNotifier();
});
