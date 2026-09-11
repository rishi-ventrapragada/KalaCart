class ArtisanProfile {
  final String id;
  final String name;
  final String craftSpecialty;
  final String clusterRegion;
  final String state;
  final int yearsOfExperience;
  final double rating;
  final int reviewCount;
  final bool isGiCertified;
  final bool isNationalAwardee;
  final String storySnippet;
  final int productCount;
  final String? avatarUrl;

  const ArtisanProfile({
    required this.id,
    required this.name,
    required this.craftSpecialty,
    required this.clusterRegion,
    required this.state,
    required this.yearsOfExperience,
    this.rating = 4.9,
    this.reviewCount = 120,
    this.isGiCertified = true,
    this.isNationalAwardee = false,
    required this.storySnippet,
    this.productCount = 24,
    this.avatarUrl,
  });
}

class ArtisanStore {
  final String id;
  final String storeName;
  final String artisanName;
  final String region;
  final String bannerTitle;
  final int totalProducts;
  final double rating;
  final bool acceptsCustomRfq;
  final String craftCategory;

  const ArtisanStore({
    required this.id,
    required this.storeName,
    required this.artisanName,
    required this.region,
    required this.bannerTitle,
    required this.totalProducts,
    required this.rating,
    this.acceptsCustomRfq = true,
    required this.craftCategory,
  });
}
