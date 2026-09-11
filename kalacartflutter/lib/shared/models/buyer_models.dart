import 'craft_product.dart';

class CraftPassportData {
  final String passportId;
  final String giRegistrationNumber;
  final String artisanSignature;
  final String geoCoordinates;
  final String craftClusterName;
  final String materialsPurityScore;
  final String rawMaterialProvenance;
  final String handcraftHours;
  final String sustainabilityRating;

  const CraftPassportData({
    required this.passportId,
    required this.giRegistrationNumber,
    required this.artisanSignature,
    required this.geoCoordinates,
    required this.craftClusterName,
    this.materialsPurityScore = '100% Natural & Organic',
    required this.rawMaterialProvenance,
    required this.handcraftHours,
    this.sustainabilityRating = 'A+ (Zero Carbon Handloom)',
  });
}

class WholesaleTier {
  final int minQuantity;
  final int? maxQuantity;
  final double pricePerUnit;

  const WholesaleTier({
    required this.minQuantity,
    this.maxQuantity,
    required this.pricePerUnit,
  });
}

class CraftReview {
  final String id;
  final String userName;
  final String userLocation;
  final double rating;
  final String date;
  final String comment;
  final bool isVerifiedBuyer;

  const CraftReview({
    required this.id,
    required this.userName,
    required this.userLocation,
    required this.rating,
    required this.date,
    required this.comment,
    this.isVerifiedBuyer = true,
  });
}

class BuyerCraftProduct {
  final String id;
  final String title;
  final String artisanId;
  final String artisanName;
  final String villageLocation;
  final String state;
  final double retailPrice;
  final double? originalPrice;
  final List<WholesaleTier> wholesaleTiers;
  final double rating;
  final int reviewCount;
  final String category;
  final String material;
  final String dimensions;
  final String weight;
  final String description;
  final List<String> craftTechniques;
  final bool isGiTagged;
  final bool isCustomizable;
  final bool inStock;
  final int stockCount;
  final CraftPassportData passport;
  final List<CraftReview> reviews;

  const BuyerCraftProduct({
    required this.id,
    required this.title,
    required this.artisanId,
    required this.artisanName,
    required this.villageLocation,
    required this.state,
    required this.retailPrice,
    this.originalPrice,
    this.wholesaleTiers = const [],
    this.rating = 4.9,
    this.reviewCount = 84,
    required this.category,
    required this.material,
    required this.dimensions,
    required this.weight,
    required this.description,
    this.craftTechniques = const [],
    this.isGiTagged = true,
    this.isCustomizable = true,
    this.inStock = true,
    this.stockCount = 12,
    required this.passport,
    this.reviews = const [],
  });

  CraftProduct toCraftProduct() {
    return CraftProduct(
      id: id,
      title: title,
      artisanName: artisanName,
      region: '$villageLocation, $state',
      price: retailPrice,
      rating: rating,
      category: category,
      isGiTagged: isGiTagged,
      isCustomizable: isCustomizable,
    );
  }
}

class LiveCraftSession {
  final String id;
  final String artisanName;
  final String sessionTitle;
  final String craftType;
  final String region;
  final int viewerCount;
  final bool isLiveNow;
  final String scheduledTime;

  const LiveCraftSession({
    required this.id,
    required this.artisanName,
    required this.sessionTitle,
    required this.craftType,
    required this.region,
    this.viewerCount = 340,
    this.isLiveNow = true,
    this.scheduledTime = 'Live Now',
  });
}

class DiscoveryItem {
  final String id;
  final String type; // 'product', 'story', 'live', 'collection', 'nearby'
  final String title;
  final String subtitle;
  final String artisanName;
  final String location;
  final String? craftCategory;
  final double? price;
  final int likesCount;
  final int savesCount;
  final bool isLiked;
  final bool isSaved;
  final bool isFollowing;
  final String? productId;
  final String? artisanId;
  final String? liveSessionId;

  const DiscoveryItem({
    required this.id,
    required this.type,
    required this.title,
    required this.subtitle,
    required this.artisanName,
    required this.location,
    this.craftCategory,
    this.price,
    this.likesCount = 128,
    this.savesCount = 45,
    this.isLiked = false,
    this.isSaved = false,
    this.isFollowing = false,
    this.productId,
    this.artisanId,
    this.liveSessionId,
  });

  DiscoveryItem copyWith({
    bool? isLiked,
    bool? isSaved,
    bool? isFollowing,
    int? likesCount,
    int? savesCount,
  }) {
    return DiscoveryItem(
      id: id,
      type: type,
      title: title,
      subtitle: subtitle,
      artisanName: artisanName,
      location: location,
      craftCategory: craftCategory,
      price: price,
      likesCount: likesCount ?? this.likesCount,
      savesCount: savesCount ?? this.savesCount,
      isLiked: isLiked ?? this.isLiked,
      isSaved: isSaved ?? this.isSaved,
      isFollowing: isFollowing ?? this.isFollowing,
      productId: productId,
      artisanId: artisanId,
      liveSessionId: liveSessionId,
    );
  }
}
