class CraftProduct {
  final String id;
  final String title;
  final String artisanName;
  final String region;
  final double price;
  final double? rating;
  final String category;
  final bool isGiTagged;
  final bool isCustomizable;
  final String? imageUrl;

  const CraftProduct({
    required this.id,
    required this.title,
    required this.artisanName,
    required this.region,
    required this.price,
    this.rating,
    required this.category,
    this.isGiTagged = false,
    this.isCustomizable = false,
    this.imageUrl,
  });
}
