/// A quantity break stored in `wholesale_pricing`.
class WholesaleTier {
  final String? id;
  final int minQuantity;
  final double pricePerUnit;

  const WholesaleTier({this.id, required this.minQuantity, required this.pricePerUnit});

  factory WholesaleTier.fromRow(Map<String, dynamic> row) => WholesaleTier(
        id: row['id'] as String?,
        minQuantity: (row['min_quantity'] as num?)?.toInt() ?? 1,
        pricePerUnit: (row['price'] as num?)?.toDouble() ?? 0,
      );
}

enum ProductStatus {
  published,
  draft,
  archived;

  String get dbValue => name;

  static ProductStatus fromDb(String? value) => ProductStatus.values.firstWhere(
        (s) => s.name == (value ?? '').toLowerCase(),
        orElse: () => ProductStatus.draft,
      );
}

/// One row of `products` joined with its seller and wholesale tiers.
class Product {
  final String id;
  final String sellerId; // sellers.id
  final String title;
  final String description;
  final String category;
  final String material;
  final double price;
  final int stock;
  final List<String> imageUrls;
  final bool isActive;
  final ProductStatus status;
  final String? city;
  final String? state;
  final DateTime createdAt;
  final List<WholesaleTier> wholesaleTiers;

  // Joined seller info
  final String? sellerShopName;
  final String? sellerArtisanType;
  final String? sellerBio;
  final String? sellerLocation;

  const Product({
    required this.id,
    required this.sellerId,
    required this.title,
    required this.description,
    required this.category,
    required this.material,
    required this.price,
    required this.stock,
    this.imageUrls = const [],
    this.isActive = true,
    this.status = ProductStatus.published,
    this.city,
    this.state,
    required this.createdAt,
    this.wholesaleTiers = const [],
    this.sellerShopName,
    this.sellerArtisanType,
    this.sellerBio,
    this.sellerLocation,
  });

  String get artisanName => sellerShopName ?? 'Artisan Studio';

  String get region {
    final bits = [city, state].where((s) => s != null && s.trim().isNotEmpty).cast<String>().toList();
    if (bits.isNotEmpty) return bits.join(', ');
    return sellerLocation ?? 'India';
  }

  String? get primaryImageUrl => imageUrls.isEmpty ? null : imageUrls.first;
  bool get inStock => stock > 0;
  bool get isPublished => status == ProductStatus.published && isActive;

  /// Sorted ascending by minimum quantity.
  List<WholesaleTier> get sortedTiers {
    final tiers = [...wholesaleTiers]..sort((a, b) => a.minQuantity.compareTo(b.minQuantity));
    return tiers;
  }

  /// Unit price for [quantity], applying the best matching wholesale tier.
  double unitPriceFor(int quantity) {
    double unit = price;
    for (final tier in sortedTiers) {
      if (quantity >= tier.minQuantity) unit = tier.pricePerUnit;
    }
    return unit;
  }

  /// Provenance code shown on the craft passport, derived from the product id.
  String get passportCode => 'KC-${id.replaceAll('-', '').substring(0, 10).toUpperCase()}';

  factory Product.fromRow(Map<String, dynamic> row) {
    final seller = row['sellers'] as Map<String, dynamic>?;
    final tiersRaw = row['wholesale_pricing'];
    final tiers = tiersRaw is List
        ? tiersRaw.whereType<Map<String, dynamic>>().map(WholesaleTier.fromRow).toList()
        : const <WholesaleTier>[];
    final imagesRaw = row['image_urls'];
    final images = imagesRaw is List
        ? imagesRaw.map((e) => e.toString()).where((s) => s.trim().isNotEmpty).toList()
        : const <String>[];

    return Product(
      id: row['id'] as String,
      sellerId: row['seller_id'] as String? ?? '',
      title: row['title'] as String? ?? 'Untitled craft',
      description: row['description'] as String? ?? '',
      category: row['category'] as String? ?? 'Handicrafts',
      material: row['material'] as String? ?? '',
      price: (row['price'] as num?)?.toDouble() ?? 0,
      stock: (row['stock'] as num?)?.toInt() ?? 0,
      imageUrls: images,
      isActive: row['is_active'] as bool? ?? true,
      status: ProductStatus.fromDb(row['status'] as String?),
      city: row['city'] as String?,
      state: row['state'] as String?,
      createdAt: DateTime.tryParse(row['created_at']?.toString() ?? '') ?? DateTime.now(),
      wholesaleTiers: tiers,
      sellerShopName: seller?['shop_name'] as String?,
      sellerArtisanType: seller?['artisan_type'] as String?,
      sellerBio: seller?['bio'] as String?,
      // sellers.location is PostGIS geometry, not text -- an `as String?` cast
      // throws on a populated row. Place text lives on profiles.city/state.
      sellerLocation: null,
    );
  }

  Product copyWith({
    String? title,
    String? description,
    String? category,
    String? material,
    double? price,
    int? stock,
    List<String>? imageUrls,
    bool? isActive,
    ProductStatus? status,
    String? city,
    String? state,
    List<WholesaleTier>? wholesaleTiers,
  }) {
    return Product(
      id: id,
      sellerId: sellerId,
      title: title ?? this.title,
      description: description ?? this.description,
      category: category ?? this.category,
      material: material ?? this.material,
      price: price ?? this.price,
      stock: stock ?? this.stock,
      imageUrls: imageUrls ?? this.imageUrls,
      isActive: isActive ?? this.isActive,
      status: status ?? this.status,
      city: city ?? this.city,
      state: state ?? this.state,
      createdAt: createdAt,
      wholesaleTiers: wholesaleTiers ?? this.wholesaleTiers,
      sellerShopName: sellerShopName,
      sellerArtisanType: sellerArtisanType,
      sellerBio: sellerBio,
      sellerLocation: sellerLocation,
    );
  }
}

/// Input for creating or updating a product listing.
class ProductInput {
  final String title;
  final String description;
  final String category;
  final String material;
  final double price;
  final int stock;
  final List<String> imageUrls;
  final ProductStatus status;
  final String? city;
  final String? state;
  final List<WholesaleTier> wholesaleTiers;

  const ProductInput({
    required this.title,
    required this.description,
    required this.category,
    required this.material,
    required this.price,
    required this.stock,
    this.imageUrls = const [],
    this.status = ProductStatus.published,
    this.city,
    this.state,
    this.wholesaleTiers = const [],
  });

  Map<String, dynamic> toRow({required String sellerId}) => {
        'seller_id': sellerId,
        'title': title.trim(),
        'description': description.trim(),
        'category': category,
        'material': material.trim(),
        'price': price,
        'stock': stock,
        'image_urls': imageUrls,
        'is_active': status != ProductStatus.archived,
        'status': status.dbValue,
        if (city != null) 'city': city,
        if (state != null) 'state': state,
      };
}
