import 'buyer_models.dart';

enum ProductStatus { published, draft, archived }

enum OrderStatus { pending, accepted, processing, shipped, delivered, cancelled }

enum RfqStatus { incoming, matched, quoted, accepted, rejected }

class SellerProduct {
  final String id;
  final String title;
  final String category;
  final double retailPrice;
  final double? originalPrice;
  final List<WholesaleTier> wholesaleTiers;
  final int stockQuantity;
  final ProductStatus status;
  final int viewsCount;
  final int salesCount;
  final double totalRevenue;
  final String material;
  final String dimensions;
  final String weight;
  final String description;
  final Map<String, String> translations; // e.g. {'hi': '...', 'te': '...', 'bn': '...'}
  final bool isGiTagged;
  final String passportId;
  final List<String> craftTechniques;
  final DateTime createdAt;

  const SellerProduct({
    required this.id,
    required this.title,
    required this.category,
    required this.retailPrice,
    this.originalPrice,
    this.wholesaleTiers = const [],
    required this.stockQuantity,
    this.status = ProductStatus.published,
    this.viewsCount = 124,
    this.salesCount = 8,
    this.totalRevenue = 19600,
    required this.material,
    required this.dimensions,
    required this.weight,
    required this.description,
    this.translations = const {},
    this.isGiTagged = true,
    required this.passportId,
    this.craftTechniques = const [],
    required this.createdAt,
  });

  SellerProduct copyWith({
    String? id,
    String? title,
    String? category,
    double? retailPrice,
    double? originalPrice,
    List<WholesaleTier>? wholesaleTiers,
    int? stockQuantity,
    ProductStatus? status,
    int? viewsCount,
    int? salesCount,
    double? totalRevenue,
    String? material,
    String? dimensions,
    String? weight,
    String? description,
    Map<String, String>? translations,
    bool? isGiTagged,
    String? passportId,
    List<String>? craftTechniques,
    DateTime? createdAt,
  }) {
    return SellerProduct(
      id: id ?? this.id,
      title: title ?? this.title,
      category: category ?? this.category,
      retailPrice: retailPrice ?? this.retailPrice,
      originalPrice: originalPrice ?? this.originalPrice,
      wholesaleTiers: wholesaleTiers ?? this.wholesaleTiers,
      stockQuantity: stockQuantity ?? this.stockQuantity,
      status: status ?? this.status,
      viewsCount: viewsCount ?? this.viewsCount,
      salesCount: salesCount ?? this.salesCount,
      totalRevenue: totalRevenue ?? this.totalRevenue,
      material: material ?? this.material,
      dimensions: dimensions ?? this.dimensions,
      weight: weight ?? this.weight,
      description: description ?? this.description,
      translations: translations ?? this.translations,
      isGiTagged: isGiTagged ?? this.isGiTagged,
      passportId: passportId ?? this.passportId,
      craftTechniques: craftTechniques ?? this.craftTechniques,
      createdAt: createdAt ?? this.createdAt,
    );
  }
}

class SellerOrderItem {
  final String productId;
  final String productTitle;
  final int quantity;
  final double unitPrice;
  final bool isWholesale;

  const SellerOrderItem({
    required this.productId,
    required this.productTitle,
    required this.quantity,
    required this.unitPrice,
    this.isWholesale = false,
  });

  double get totalPrice => unitPrice * quantity;
}

class SellerOrder {
  final String id;
  final String orderNumber;
  final String buyerName;
  final String buyerPhone;
  final String buyerAddress;
  final List<SellerOrderItem> items;
  final double totalAmount;
  final OrderStatus status;
  final DateTime orderDate;
  final String? trackingNumber;
  final String? courierPartner;
  final String paymentStatus;

  const SellerOrder({
    required this.id,
    required this.orderNumber,
    required this.buyerName,
    required this.buyerPhone,
    required this.buyerAddress,
    required this.items,
    required this.totalAmount,
    required this.status,
    required this.orderDate,
    this.trackingNumber,
    this.courierPartner,
    this.paymentStatus = 'Paid via UPI Escrow',
  });

  SellerOrder copyWith({
    String? id,
    String? orderNumber,
    String? buyerName,
    String? buyerPhone,
    String? buyerAddress,
    List<SellerOrderItem>? items,
    double? totalAmount,
    OrderStatus? status,
    DateTime? orderDate,
    String? trackingNumber,
    String? courierPartner,
    String? paymentStatus,
  }) {
    return SellerOrder(
      id: id ?? this.id,
      orderNumber: orderNumber ?? this.orderNumber,
      buyerName: buyerName ?? this.buyerName,
      buyerPhone: buyerPhone ?? this.buyerPhone,
      buyerAddress: buyerAddress ?? this.buyerAddress,
      items: items ?? this.items,
      totalAmount: totalAmount ?? this.totalAmount,
      status: status ?? this.status,
      orderDate: orderDate ?? this.orderDate,
      trackingNumber: trackingNumber ?? this.trackingNumber,
      courierPartner: courierPartner ?? this.courierPartner,
      paymentStatus: paymentStatus ?? this.paymentStatus,
    );
  }
}

class SellerQuoteSubmission {
  final double pricePerUnit;
  final int moq;
  final int deliveryDays;
  final String message;
  final bool hasVoiceNote;
  final List<String> attachedPortfolioIds;
  final DateTime submittedAt;

  const SellerQuoteSubmission({
    required this.pricePerUnit,
    required this.moq,
    required this.deliveryDays,
    required this.message,
    this.hasVoiceNote = false,
    this.attachedPortfolioIds = const [],
    required this.submittedAt,
  });
}

class SellerRfq {
  final String id;
  final String rfqNumber;
  final String buyerName;
  final String buyerCompany;
  final String buyerLocation;
  final String craftRequired;
  final int quantityRequired;
  final double targetBudget;
  final String deliveryDeadline;
  final RfqStatus status;
  final String specifications;
  final DateTime postedAt;
  final SellerQuoteSubmission? quote;

  const SellerRfq({
    required this.id,
    required this.rfqNumber,
    required this.buyerName,
    required this.buyerCompany,
    required this.buyerLocation,
    required this.craftRequired,
    required this.quantityRequired,
    required this.targetBudget,
    required this.deliveryDeadline,
    required this.status,
    required this.specifications,
    required this.postedAt,
    this.quote,
  });

  SellerRfq copyWith({
    String? id,
    String? rfqNumber,
    String? buyerName,
    String? buyerCompany,
    String? buyerLocation,
    String? craftRequired,
    int? quantityRequired,
    double? targetBudget,
    String? deliveryDeadline,
    RfqStatus? status,
    String? specifications,
    DateTime? postedAt,
    SellerQuoteSubmission? quote,
  }) {
    return SellerRfq(
      id: id ?? this.id,
      rfqNumber: rfqNumber ?? this.rfqNumber,
      buyerName: buyerName ?? this.buyerName,
      buyerCompany: buyerCompany ?? this.buyerCompany,
      buyerLocation: buyerLocation ?? this.buyerLocation,
      craftRequired: craftRequired ?? this.craftRequired,
      quantityRequired: quantityRequired ?? this.quantityRequired,
      targetBudget: targetBudget ?? this.targetBudget,
      deliveryDeadline: deliveryDeadline ?? this.deliveryDeadline,
      status: status ?? this.status,
      specifications: specifications ?? this.specifications,
      postedAt: postedAt ?? this.postedAt,
      quote: quote ?? this.quote,
    );
  }
}

class ArtisanStorefrontConfig {
  final String storeName;
  final String artisanName;
  final String tagline;
  final String bio;
  final String clusterRegion;
  final String state;
  final bool isGiCertified;
  final bool isNationalAwardee;
  final bool isStoreOpen;
  final bool isLiveNow;
  final List<String> collections;
  final List<String> featuredProductIds;
  final String shareUrl;
  final int totalStoreVisits;

  const ArtisanStorefrontConfig({
    required this.storeName,
    required this.artisanName,
    required this.tagline,
    required this.bio,
    required this.clusterRegion,
    required this.state,
    this.isGiCertified = true,
    this.isNationalAwardee = true,
    this.isStoreOpen = true,
    this.isLiveNow = false,
    this.collections = const ['Heritage Masterpieces', 'Festive Collection 2026', 'GI Tagged Exports'],
    this.featuredProductIds = const ['prod-001', 'prod-002'],
    this.shareUrl = 'https://kalacart.in/store/kripal-kumbh-jaipur',
    this.totalStoreVisits = 3420,
  });

  ArtisanStorefrontConfig copyWith({
    String? storeName,
    String? artisanName,
    String? tagline,
    String? bio,
    String? clusterRegion,
    String? state,
    bool? isGiCertified,
    bool? isNationalAwardee,
    bool? isStoreOpen,
    bool? isLiveNow,
    List<String>? collections,
    List<String>? featuredProductIds,
    String? shareUrl,
    int? totalStoreVisits,
  }) {
    return ArtisanStorefrontConfig(
      storeName: storeName ?? this.storeName,
      artisanName: artisanName ?? this.artisanName,
      tagline: tagline ?? this.tagline,
      bio: bio ?? this.bio,
      clusterRegion: clusterRegion ?? this.clusterRegion,
      state: state ?? this.state,
      isGiCertified: isGiCertified ?? this.isGiCertified,
      isNationalAwardee: isNationalAwardee ?? this.isNationalAwardee,
      isStoreOpen: isStoreOpen ?? this.isStoreOpen,
      isLiveNow: isLiveNow ?? this.isLiveNow,
      collections: collections ?? this.collections,
      featuredProductIds: featuredProductIds ?? this.featuredProductIds,
      shareUrl: shareUrl ?? this.shareUrl,
      totalStoreVisits: totalStoreVisits ?? this.totalStoreVisits,
    );
  }
}
