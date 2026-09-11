import 'ai_models.dart';

/// Vision Service abstraction for analyzing craft images, identifying materials, & GI verification.
abstract class VisionService {
  Future<ProductUnderstandingResult> analyzeCraftImages(List<String> imagePathsOrUrls);
}

/// Translation Service abstraction for English, Hindi, Telugu, and mixed-Indian dialect translation.
abstract class TranslationService {
  Future<TranslationResult> translate({
    required String text,
    required String targetLanguage,
    String? sourceLanguage,
  });

  Future<Map<String, String>> translateToAllSupportedLanguages(String text);
}

/// Speech To Text Service abstraction supporting mixed Indian multilingual audio (English/Hindi/Telugu).
abstract class SpeechToTextService {
  Stream<String> startListening({SupportedLanguage preferredLanguage = SupportedLanguage.hinglish});
  Future<String> stopListening();
  Future<void> cancelListening();
}

/// Text To Speech Service abstraction for multi-language voice responses.
abstract class TextToSpeechService {
  Future<void> speak({
    required String text,
    SupportedLanguage language = SupportedLanguage.english,
  });
  Future<void> stop();
}

/// Pricing Intelligence Service abstraction calculating fair artisan value & wholesale MOQ margins.
abstract class PricingService {
  Future<PricingSuggestionResult> calculateFairPricing({
    required String craftCategory,
    required String material,
    required double estimatedHours,
    int? customMoq,
  });
}

/// Recommendation Service abstraction for discovering crafts, artisan stories, and RFQ matches.
abstract class RecommendationService {
  Future<List<String>> getRecommendedProductIds({
    required String userId,
    List<String>? recentInterests,
    String? preferredRegion,
  });
}

/// Unified High-Level AI Service orchestrator for assistant chat, catalogue generation, & voice commands.
abstract class AIService {
  Future<GeneratedCatalogueData> generateCatalogue({
    required ProductUnderstandingResult visionData,
    required PricingSuggestionResult pricingData,
  });

  Future<String> generateMarketingContent({
    required String productTitle,
    required String craftTechnique,
    required String artisanHeritage,
  });

  Future<VoiceIntentResult> processVoiceCommand({
    required String rawVoiceText,
    required bool isArtisanMode,
  });

  Future<String> queryAssistant({
    required String message,
    required bool isArtisanMode,
    List<Map<String, String>> conversationHistory = const [],
  });
}
