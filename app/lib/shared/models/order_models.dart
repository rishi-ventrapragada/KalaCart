/// Order lifecycle as stored in `orders.order_status`.
enum OrderStatus {
  pending,
  accepted,
  processing,
  shipped,
  delivered,
  cancelled;

  String get dbValue => name;

  static OrderStatus fromDb(String? value) {
    return OrderStatus.values.firstWhere(
      (s) => s.name == (value ?? '').toLowerCase(),
      orElse: () => OrderStatus.pending,
    );
  }

  String get label {
    switch (this) {
      case OrderStatus.pending:
        return 'Pending';
      case OrderStatus.accepted:
        return 'Accepted';
      case OrderStatus.processing:
        return 'In Kiln';
      case OrderStatus.shipped:
        return 'Shipped';
      case OrderStatus.delivered:
        return 'Delivered';
      case OrderStatus.cancelled:
        return 'Cancelled';
    }
  }
}

/// One row of `orders`. The table stores a single product per order, so a
/// multi-item checkout produces several rows sharing the same shipping address
/// and creation time.
class OrderRecord {
  final String id;
  final String buyerId; // auth user id
  final String sellerId; // sellers.id
  final String? productId;
  final int quantity;
  final double unitPrice;
  final double totalAmount;
  final OrderStatus status;
  final String paymentStatus;
  final String? shippingAddress;
  final DateTime createdAt;
  final DateTime? updatedAt;

  // Joined, read-only
  final String? productTitle;
  final String? productCategory;
  final String? productImageUrl;
  final String? sellerShopName;
  final String? buyerName;
  final String? buyerPhone;

  const OrderRecord({
    required this.id,
    required this.buyerId,
    required this.sellerId,
    this.productId,
    required this.quantity,
    required this.unitPrice,
    required this.totalAmount,
    required this.status,
    required this.paymentStatus,
    this.shippingAddress,
    required this.createdAt,
    this.updatedAt,
    this.productTitle,
    this.productCategory,
    this.productImageUrl,
    this.sellerShopName,
    this.buyerName,
    this.buyerPhone,
  });

  /// Short human-friendly order number derived from the UUID.
  String get orderNumber => 'KC-${id.replaceAll('-', '').substring(0, 8).toUpperCase()}';

  bool get isWholesale => quantity >= 5;

  OrderRecord copyWith({OrderStatus? status, String? paymentStatus, DateTime? updatedAt}) {
    return OrderRecord(
      id: id,
      buyerId: buyerId,
      sellerId: sellerId,
      productId: productId,
      quantity: quantity,
      unitPrice: unitPrice,
      totalAmount: totalAmount,
      status: status ?? this.status,
      paymentStatus: paymentStatus ?? this.paymentStatus,
      shippingAddress: shippingAddress,
      createdAt: createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      productTitle: productTitle,
      productCategory: productCategory,
      productImageUrl: productImageUrl,
      sellerShopName: sellerShopName,
      buyerName: buyerName,
      buyerPhone: buyerPhone,
    );
  }

  factory OrderRecord.fromRow(Map<String, dynamic> row) {
    final product = row['products'] as Map<String, dynamic>?;
    final seller = row['sellers'] as Map<String, dynamic>?;
    final imageUrls = product?['image_urls'];
    String? firstImage;
    if (imageUrls is List && imageUrls.isNotEmpty) firstImage = imageUrls.first?.toString();

    return OrderRecord(
      id: row['id'] as String,
      buyerId: row['buyer_id'] as String? ?? '',
      sellerId: row['seller_id'] as String? ?? '',
      productId: row['product_id'] as String?,
      quantity: (row['quantity'] as num?)?.toInt() ?? 1,
      unitPrice: (row['unit_price'] as num?)?.toDouble() ?? 0,
      totalAmount: (row['total_amount'] as num?)?.toDouble() ?? 0,
      status: OrderStatus.fromDb(row['order_status'] as String?),
      paymentStatus: row['payment_status'] as String? ?? 'pending',
      shippingAddress: row['shipping_address'] as String?,
      createdAt: DateTime.tryParse(row['created_at']?.toString() ?? '') ?? DateTime.now(),
      updatedAt: DateTime.tryParse(row['updated_at']?.toString() ?? ''),
      productTitle: product?['title'] as String?,
      productCategory: product?['category'] as String?,
      productImageUrl: firstImage,
      sellerShopName: seller?['shop_name'] as String?,
    );
  }
}
