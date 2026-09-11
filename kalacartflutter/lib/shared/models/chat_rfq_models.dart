enum ChatMessageType {
  text,
  image,
  voice,
  product,
  rfq,
  quotation,
  order,
  system,
}

class ChatMessage {
  final String id;
  final String conversationId;
  final String senderId;
  final String senderName;
  final bool isMe;
  final ChatMessageType type;
  final String text;
  final DateTime timestamp;
  final Map<String, dynamic>? metadata; // Holds quote, product, order or rfq details

  const ChatMessage({
    required this.id,
    required this.conversationId,
    required this.senderId,
    required this.senderName,
    required this.isMe,
    required this.type,
    required this.text,
    required this.timestamp,
    this.metadata,
  });
}

class Conversation {
  final String id;
  final String otherPartyId;
  final String otherPartyName;
  final String otherPartyRole; // 'Master Artisan' or 'Wholesale Buyer'
  final String? craftCluster;
  final String lastMessage;
  final DateTime lastMessageTime;
  final int unreadCount;
  final String? relatedRfqId;
  final String? relatedOrderId;

  const Conversation({
    required this.id,
    required this.otherPartyId,
    required this.otherPartyName,
    required this.otherPartyRole,
    this.craftCluster,
    required this.lastMessage,
    required this.lastMessageTime,
    this.unreadCount = 0,
    this.relatedRfqId,
    this.relatedOrderId,
  });

  Conversation copyWith({
    String? id,
    String? otherPartyId,
    String? otherPartyName,
    String? otherPartyRole,
    String? craftCluster,
    String? lastMessage,
    DateTime? lastMessageTime,
    int? unreadCount,
    String? relatedRfqId,
    String? relatedOrderId,
  }) {
    return Conversation(
      id: id ?? this.id,
      otherPartyId: otherPartyId ?? this.otherPartyId,
      otherPartyName: otherPartyName ?? this.otherPartyName,
      otherPartyRole: otherPartyRole ?? this.otherPartyRole,
      craftCluster: craftCluster ?? this.craftCluster,
      lastMessage: lastMessage ?? this.lastMessage,
      lastMessageTime: lastMessageTime ?? this.lastMessageTime,
      unreadCount: unreadCount ?? this.unreadCount,
      relatedRfqId: relatedRfqId ?? this.relatedRfqId,
      relatedOrderId: relatedOrderId ?? this.relatedOrderId,
    );
  }
}

class BuyerRfqSubmission {
  final String id;
  final String title;
  final String category;
  final int quantity;
  final double targetPricePerUnit;
  final String deliveryRequiredBy;
  final String destinationPincode;
  final String customizationNotes;
  final bool hasVoiceNote;
  final List<String> attachments;
  final String status; // 'open', 'quotes_received', 'accepted', 'closed'
  final DateTime createdAt;

  const BuyerRfqSubmission({
    required this.id,
    required this.title,
    required this.category,
    required this.quantity,
    required this.targetPricePerUnit,
    required this.deliveryRequiredBy,
    required this.destinationPincode,
    required this.customizationNotes,
    this.hasVoiceNote = false,
    this.attachments = const [],
    this.status = 'open',
    required this.createdAt,
  });

  double get totalTargetBudget => targetPricePerUnit * quantity;

  BuyerRfqSubmission copyWith({
    String? id,
    String? title,
    String? category,
    int? quantity,
    double? targetPricePerUnit,
    String? deliveryRequiredBy,
    String? destinationPincode,
    String? customizationNotes,
    bool? hasVoiceNote,
    List<String>? attachments,
    String? status,
    DateTime? createdAt,
  }) {
    return BuyerRfqSubmission(
      id: id ?? this.id,
      title: title ?? this.title,
      category: category ?? this.category,
      quantity: quantity ?? this.quantity,
      targetPricePerUnit: targetPricePerUnit ?? this.targetPricePerUnit,
      deliveryRequiredBy: deliveryRequiredBy ?? this.deliveryRequiredBy,
      destinationPincode: destinationPincode ?? this.destinationPincode,
      customizationNotes: customizationNotes ?? this.customizationNotes,
      hasVoiceNote: hasVoiceNote ?? this.hasVoiceNote,
      attachments: attachments ?? this.attachments,
      status: status ?? this.status,
      createdAt: createdAt ?? this.createdAt,
    );
  }
}
