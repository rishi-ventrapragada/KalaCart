/// DTOs for the three live FastAPI endpoints.
///
/// Field names and shapes were read off real responses from
/// https://kalacart-api.onrender.com on 2026-09-12, not from the OpenAPI
/// document (production has `/openapi.json` and `/docs` disabled).
///
/// Parsing is defensive in the same style as `shared/models/product.dart`:
/// nothing here throws on a malformed row.
library;

/// Result of `POST /api/v1/image/enhance`.
///
/// The backend returns the same fields both at the top level and inside a
/// `data` envelope; we read the envelope and fall back to the root.
class EnhancedImageResult {
  final String? originalUrl;
  final String? enhancedUrl;
  final String? thumbnailUrl;
  final int width;
  final int height;
  final String ratio;
  final bool backgroundRemoved;
  final bool storageUploaded;

  const EnhancedImageResult({
    this.originalUrl,
    this.enhancedUrl,
    this.thumbnailUrl,
    this.width = 0,
    this.height = 0,
    this.ratio = '1:1',
    this.backgroundRemoved = false,
    this.storageUploaded = false,
  });

  factory EnhancedImageResult.fromResponse(Map<String, dynamic> body) {
    final row = (body['data'] is Map<String, dynamic>)
        ? body['data'] as Map<String, dynamic>
        : body;
    return EnhancedImageResult(
      originalUrl: row['original_url'] as String?,
      enhancedUrl: row['enhanced_url'] as String?,
      thumbnailUrl: row['thumbnail_url'] as String?,
      width: (row['width'] as num?)?.toInt() ?? 0,
      height: (row['height'] as num?)?.toInt() ?? 0,
      ratio: row['ratio'] as String? ?? '1:1',
      backgroundRemoved: row['background_removed'] == true,
      storageUploaded: row['storage_uploaded'] == true,
    );
  }

  /// True when the enhanced image came back inline because Supabase Storage
  /// rejected the upload. Such a URL is a `data:` URI, not a network address.
  bool get isInlineData => enhancedUrl?.startsWith('data:') ?? false;
}

/// One line of the price explanation, e.g. "Materials ₹400 (your cost)".
typedef PricingFactor = String;

/// Result of `POST /api/v1/pricing/analyze`.
///
/// The price is computed deterministically by the backend's pricing engine —
/// the AI only extracts attributes — so every number here has a stated reason.
class PricingBreakdown {
  final double suggestedPrice;
  final double minimumPrice;
  final double maximumPrice;
  final String currency;
  final int confidence;

  /// Cost split: materials / labour / overhead / profit, all in INR.
  final double materials;
  final double labour;
  final double overhead;
  final double profit;

  /// Comparable market band.
  final String marketSource;
  final int comparables;
  final double marketLow;
  final double marketMedian;
  final double marketHigh;

  final double seasonalFactor;
  final String seasonalReason;

  /// Human-readable explanation lines, ready to render as a list.
  final List<PricingFactor> factors;
  final String reasoning;

  /// Inputs the engine had to estimate (e.g. `material_cost`), so the UI can
  /// invite the artisan to supply them for a better price.
  final List<String> estimatedInputs;

  final String category;
  final double labourHours;

  const PricingBreakdown({
    required this.suggestedPrice,
    required this.minimumPrice,
    required this.maximumPrice,
    this.currency = 'INR',
    this.confidence = 0,
    this.materials = 0,
    this.labour = 0,
    this.overhead = 0,
    this.profit = 0,
    this.marketSource = '',
    this.comparables = 0,
    this.marketLow = 0,
    this.marketMedian = 0,
    this.marketHigh = 0,
    this.seasonalFactor = 1,
    this.seasonalReason = '',
    this.factors = const [],
    this.reasoning = '',
    this.estimatedInputs = const [],
    this.category = '',
    this.labourHours = 0,
  });

  factory PricingBreakdown.fromResponse(Map<String, dynamic> body) {
    final data = (body['data'] as Map<String, dynamic>?) ?? const {};
    final breakdown = (data['breakdown'] as Map<String, dynamic>?) ?? const {};
    final market = (data['market'] as Map<String, dynamic>?) ?? const {};
    final seasonal = (data['seasonal'] as Map<String, dynamic>?) ?? const {};
    final attributes = (data['attributes'] as Map<String, dynamic>?) ?? const {};

    double num_(Object? v) => (v as num?)?.toDouble() ?? 0;

    return PricingBreakdown(
      suggestedPrice: num_(data['suggested_price']),
      minimumPrice: num_(data['minimum_price']),
      maximumPrice: num_(data['maximum_price']),
      currency: data['currency'] as String? ?? 'INR',
      confidence: (data['confidence'] as num?)?.toInt() ?? 0,
      materials: num_(breakdown['materials']),
      labour: num_(breakdown['labour']),
      overhead: num_(breakdown['overhead']),
      profit: num_(breakdown['profit']),
      marketSource: market['source'] as String? ?? '',
      comparables: (market['comparables'] as num?)?.toInt() ?? 0,
      marketLow: num_(market['low']),
      marketMedian: num_(market['median']),
      marketHigh: num_(market['high']),
      seasonalFactor: (seasonal['factor'] as num?)?.toDouble() ?? 1,
      seasonalReason: seasonal['reason'] as String? ?? '',
      factors: (data['factors'] is List)
          ? (data['factors'] as List).whereType<String>().toList()
          : const [],
      reasoning: data['reasoning'] as String? ?? '',
      estimatedInputs: (data['estimated_inputs'] is List)
          ? (data['estimated_inputs'] as List).whereType<String>().toList()
          : const [],
      category: attributes['category'] as String? ?? '',
      labourHours: num_(data['labour_hours']),
    );
  }

  /// True when the backend priced this without any AI call, because the seller
  /// supplied category + size + quality + complexity.
  bool get isDeterministic => estimatedInputs.isEmpty;
}

/// Result of `POST /api/v1/catalog/generate`.
class GeneratedCatalog {
  final String title;
  final String descriptionEn;
  final String descriptionHi;
  final String category;
  final List<String> materials;
  final List<String> seoTags;
  final String care;

  /// Present only on the voice endpoint; kept so the same DTO serves both.
  final String? transcript;
  final String? detectedLanguage;

  const GeneratedCatalog({
    required this.title,
    required this.descriptionEn,
    required this.descriptionHi,
    required this.category,
    this.materials = const [],
    this.seoTags = const [],
    this.care = '',
    this.transcript,
    this.detectedLanguage,
  });

  factory GeneratedCatalog.fromResponse(Map<String, dynamic> body) {
    final data = (body['data'] as Map<String, dynamic>?) ?? const {};
    List<String> list(Object? v) =>
        v is List ? v.whereType<String>().toList() : const [];
    return GeneratedCatalog(
      title: data['title'] as String? ?? '',
      descriptionEn: data['description_en'] as String? ?? '',
      descriptionHi: data['description_hi'] as String? ?? '',
      category: data['category'] as String? ?? '',
      materials: list(data['materials']),
      seoTags: list(data['seo_tags']),
      care: data['care'] as String? ?? '',
      transcript: data['transcript'] as String?,
      detectedLanguage: data['detected_language'] as String?,
    );
  }
}
