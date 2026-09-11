/// Status values stored in `enquiries.status`.
enum EnquiryStatus {
  pending,
  quoted,
  accepted,
  rejected,
  closed;

  String get dbValue => name;

  static EnquiryStatus fromDb(String? value) => EnquiryStatus.values.firstWhere(
        (s) => s.name == (value ?? '').toLowerCase(),
        orElse: () => EnquiryStatus.pending,
      );

  String get label {
    switch (this) {
      case EnquiryStatus.pending:
        return 'Open for bids';
      case EnquiryStatus.quoted:
        return 'Quote received';
      case EnquiryStatus.accepted:
        return 'Accepted';
      case EnquiryStatus.rejected:
        return 'Declined';
      case EnquiryStatus.closed:
        return 'Closed';
    }
  }
}

/// Structured details a buyer attaches to an RFQ. The `enquiries` table only has
/// a free-text `message`, so these are serialised into it as labelled lines and
/// parsed back out.
class RfqDetails {
  final String title;
  final double? targetPricePerUnit;
  final String? deliveryBy;
  final String? destinationPincode;
  final String notes;

  const RfqDetails({
    required this.title,
    this.targetPricePerUnit,
    this.deliveryBy,
    this.destinationPincode,
    this.notes = '',
  });

  static const _kTitle = 'RFQ:';
  static const _kTarget = 'Target price/unit:';
  static const _kDelivery = 'Deliver by:';
  static const _kPincode = 'Destination PIN:';
  static const _kNotes = 'Notes:';

  String serialize() {
    final lines = <String>['$_kTitle ${title.trim()}'];
    if (targetPricePerUnit != null) lines.add('$_kTarget ${targetPricePerUnit!.toStringAsFixed(0)}');
    if ((deliveryBy ?? '').trim().isNotEmpty) lines.add('$_kDelivery ${deliveryBy!.trim()}');
    if ((destinationPincode ?? '').trim().isNotEmpty) lines.add('$_kPincode ${destinationPincode!.trim()}');
    if (notes.trim().isNotEmpty) lines.add('$_kNotes ${notes.trim()}');
    return lines.join('\n');
  }

  static RfqDetails parse(String message, {String fallbackTitle = 'Custom craft enquiry'}) {
    String title = fallbackTitle;
    double? target;
    String? deliveryBy;
    String? pincode;
    final notes = <String>[];
    bool inNotes = false;

    for (final raw in message.split('\n')) {
      final line = raw.trimRight();
      if (inNotes) {
        notes.add(line);
        continue;
      }
      if (line.startsWith(_kTitle)) {
        title = line.substring(_kTitle.length).trim();
      } else if (line.startsWith(_kTarget)) {
        target = double.tryParse(line.substring(_kTarget.length).trim());
      } else if (line.startsWith(_kDelivery)) {
        deliveryBy = line.substring(_kDelivery.length).trim();
      } else if (line.startsWith(_kPincode)) {
        pincode = line.substring(_kPincode.length).trim();
      } else if (line.startsWith(_kNotes)) {
        inNotes = true;
        final rest = line.substring(_kNotes.length).trim();
        if (rest.isNotEmpty) notes.add(rest);
      } else if (line.trim().isNotEmpty) {
        // Plain-text enquiry written outside the app.
        notes.add(line);
      }
    }
    return RfqDetails(
      title: title,
      targetPricePerUnit: target,
      deliveryBy: deliveryBy,
      destinationPincode: pincode,
      notes: notes.join('\n').trim(),
    );
  }
}

/// One row of `enquiries` joined with its product (and the product's seller).
class Enquiry {
  final String id;
  final String? productId;
  final String? buyerId; // auth user id
  final String message;
  final int quantity;
  final EnquiryStatus status;
  final String? guestName;
  final String? guestContact;
  final DateTime createdAt;

  // Joined
  final String? productTitle;
  final String? productCategory;
  final double? productPrice;
  final String? productImageUrl;
  final String? sellerId; // sellers.id via products
  final String? sellerShopName;
  final String? sellerProfileId; // profiles.id of the seller, for messaging

  const Enquiry({
    required this.id,
    this.productId,
    this.buyerId,
    required this.message,
    required this.quantity,
    required this.status,
    this.guestName,
    this.guestContact,
    required this.createdAt,
    this.productTitle,
    this.productCategory,
    this.productPrice,
    this.productImageUrl,
    this.sellerId,
    this.sellerShopName,
    this.sellerProfileId,
  });

  RfqDetails get details => RfqDetails.parse(message, fallbackTitle: productTitle ?? 'Custom craft enquiry');

  String get rfqNumber => 'RFQ-${id.replaceAll('-', '').substring(0, 6).toUpperCase()}';

  double get targetBudget => (details.targetPricePerUnit ?? productPrice ?? 0) * quantity;

  factory Enquiry.fromRow(Map<String, dynamic> row) {
    final product = row['products'] as Map<String, dynamic>?;
    final seller = product?['sellers'] as Map<String, dynamic>?;
    final imagesRaw = product?['image_urls'];
    String? firstImage;
    if (imagesRaw is List && imagesRaw.isNotEmpty) firstImage = imagesRaw.first?.toString();

    return Enquiry(
      id: row['id'] as String,
      productId: row['product_id'] as String?,
      buyerId: row['buyer_id'] as String?,
      message: row['message'] as String? ?? '',
      quantity: (row['quantity'] as num?)?.toInt() ?? 1,
      status: EnquiryStatus.fromDb(row['status'] as String?),
      guestName: row['guest_name'] as String?,
      guestContact: row['guest_contact'] as String?,
      createdAt: DateTime.tryParse(row['created_at']?.toString() ?? '') ?? DateTime.now(),
      productTitle: product?['title'] as String?,
      productCategory: product?['category'] as String?,
      productPrice: (product?['price'] as num?)?.toDouble(),
      productImageUrl: firstImage,
      sellerId: product?['seller_id'] as String?,
      sellerShopName: seller?['shop_name'] as String?,
      sellerProfileId: seller?['profile_id'] as String?,
    );
  }

  Enquiry copyWith({EnquiryStatus? status}) => Enquiry(
        id: id,
        productId: productId,
        buyerId: buyerId,
        message: message,
        quantity: quantity,
        status: status ?? this.status,
        guestName: guestName,
        guestContact: guestContact,
        createdAt: createdAt,
        productTitle: productTitle,
        productCategory: productCategory,
        productPrice: productPrice,
        productImageUrl: productImageUrl,
        sellerId: sellerId,
        sellerShopName: sellerShopName,
        sellerProfileId: sellerProfileId,
      );
}

/// A quotation embedded in a chat message. Serialised into `messages.message`
/// with a `QUOTE:` prefix so it can be rendered as a card.
class QuoteDetails {
  final double pricePerUnit;
  final int moq;
  final int deliveryDays;
  final String note;

  const QuoteDetails({
    required this.pricePerUnit,
    required this.moq,
    required this.deliveryDays,
    this.note = '',
  });

  static const prefix = 'QUOTE:';

  String serialize() =>
      '$prefix price=${pricePerUnit.toStringAsFixed(2)};moq=$moq;days=$deliveryDays\n${note.trim()}';

  static QuoteDetails? tryParse(String message) {
    if (!message.startsWith(prefix)) return null;
    final firstLineEnd = message.indexOf('\n');
    final head = (firstLineEnd == -1 ? message : message.substring(0, firstLineEnd)).substring(prefix.length).trim();
    final note = firstLineEnd == -1 ? '' : message.substring(firstLineEnd + 1).trim();
    double? price;
    int? moq;
    int? days;
    for (final part in head.split(';')) {
      final kv = part.split('=');
      if (kv.length != 2) continue;
      switch (kv[0].trim()) {
        case 'price':
          price = double.tryParse(kv[1].trim());
        case 'moq':
          moq = int.tryParse(kv[1].trim());
        case 'days':
          days = int.tryParse(kv[1].trim());
      }
    }
    if (price == null) return null;
    return QuoteDetails(pricePerUnit: price, moq: moq ?? 1, deliveryDays: days ?? 0, note: note);
  }
}

/// An order confirmation embedded in a chat message (`ORDER:` prefix).
class OrderMessageDetails {
  final String orderId;
  final double totalAmount;
  final int quantity;

  const OrderMessageDetails({required this.orderId, required this.totalAmount, required this.quantity});

  static const prefix = 'ORDER:';

  String serialize() => '$prefix id=$orderId;total=${totalAmount.toStringAsFixed(2)};qty=$quantity';

  static OrderMessageDetails? tryParse(String message) {
    if (!message.startsWith(prefix)) return null;
    String? id;
    double? total;
    int? qty;
    for (final part in message.substring(prefix.length).trim().split(';')) {
      final kv = part.split('=');
      if (kv.length != 2) continue;
      switch (kv[0].trim()) {
        case 'id':
          id = kv[1].trim();
        case 'total':
          total = double.tryParse(kv[1].trim());
        case 'qty':
          qty = int.tryParse(kv[1].trim());
      }
    }
    if (id == null) return null;
    return OrderMessageDetails(orderId: id, totalAmount: total ?? 0, quantity: qty ?? 1);
  }
}
