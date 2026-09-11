enum VoiceState {
  idle,
  listening,
  processing,
  speaking,
  error,
}

enum SupportedLanguage {
  english('en', 'English', 'English'),
  hindi('hi', 'हिन्दी', 'Hindi'),
  telugu('te', 'తెలుగు', 'Telugu'),
  hinglish('hi-en', 'Hinglish / Mix', 'Mixed Indian Languages');

  final String code;
  final String nativeLabel;
  final String englishLabel;

  const SupportedLanguage(this.code, this.nativeLabel, this.englishLabel);
}

class ProductUnderstandingResult {
  final String detectedTitle;
  final String category;
  final String primaryMaterial;
  final List<String> allMaterials;
  final String craftTechnique;
  final String region;
  final bool isGiCandidate;
  final String giCategory;
  final String dimensionsEstimate;
  final String weightEstimate;
  final List<String> visualTags;
  final double confidenceScore;

  const ProductUnderstandingResult({
    required this.detectedTitle,
    required this.category,
    required this.primaryMaterial,
    this.allMaterials = const [],
    required this.craftTechnique,
    required this.region,
    this.isGiCandidate = true,
    required this.giCategory,
    required this.dimensionsEstimate,
    required this.weightEstimate,
    this.visualTags = const [],
    this.confidenceScore = 0.94,
  });
}

class GeneratedCatalogueData {
  final String title;
  final String shortDescription;
  final String fullStoryDescription;
  final String careInstructions;
  final String seoKeywords;
  final Map<String, String> localizedTitles;
  final Map<String, String> localizedDescriptions;
  final List<String> craftHeritageHighlights;

  const GeneratedCatalogueData({
    required this.title,
    required this.shortDescription,
    required this.fullStoryDescription,
    required this.careInstructions,
    required this.seoKeywords,
    required this.localizedTitles,
    required this.localizedDescriptions,
    required this.craftHeritageHighlights,
  });
}

class PricingSuggestionResult {
  final double suggestedRetailPrice;
  final double suggestedWholesalePrice;
  final int suggestedMoq;
  final double estimatedLaborCost;
  final double estimatedRawMaterialCost;
  final double marketAveragePrice;
  final String pricingRationale;

  const PricingSuggestionResult({
    required this.suggestedRetailPrice,
    required this.suggestedWholesalePrice,
    required this.suggestedMoq,
    required this.estimatedLaborCost,
    required this.estimatedRawMaterialCost,
    required this.marketAveragePrice,
    required this.pricingRationale,
  });
}

class TranslationResult {
  final String originalText;
  final String sourceLanguage;
  final String targetLanguage;
  final String translatedText;
  final bool isMixedLanguage;

  const TranslationResult({
    required this.originalText,
    required this.sourceLanguage,
    required this.targetLanguage,
    required this.translatedText,
    this.isMixedLanguage = false,
  });
}

class VoiceIntentResult {
  final String rawTranscript;
  final String recognizedLanguage;
  final String intentType; // 'rfq_inquiry', 'search_craft', 'artisan_help', 'price_check'
  final Map<String, dynamic> extractedEntities;
  final String assistantResponseText;

  const VoiceIntentResult({
    required this.rawTranscript,
    required this.recognizedLanguage,
    required this.intentType,
    required this.extractedEntities,
    required this.assistantResponseText,
  });
}
