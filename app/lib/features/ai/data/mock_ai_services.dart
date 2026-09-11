import 'dart:async';
import '../domain/ai_models.dart';
import '../domain/ai_service_interfaces.dart';

class MockVisionService implements VisionService {
  @override
  Future<ProductUnderstandingResult> analyzeCraftImages(List<String> imagePathsOrUrls) async {
    await Future.delayed(const Duration(milliseconds: 1200));
    return const ProductUnderstandingResult(
      detectedTitle: 'Handcrafted Blue Pottery Royal Jaipur Floral Vase',
      category: 'Pottery & Terracotta',
      primaryMaterial: 'Makrana Quartz & Natural Egyptian Frit Glaze',
      allMaterials: ['Quartz Powder', 'Raw Glass Powder', 'Fuller Earth / Multani Mitti', 'Natural Cobalt Oxide'],
      craftTechnique: 'Mould-formed, freehand cobalt brushwork, low-fire wood kiln',
      region: 'Jaipur, Rajasthan',
      isGiCandidate: true,
      giCategory: 'GI-IN-RAJ-2026-BP-0941 (Registered Handicraft)',
      dimensionsEstimate: '14" Height x 7" Diameter',
      weightEstimate: '1.45 kg',
      visualTags: ['Ceramic', 'Blue Pottery', 'Urn', 'Floral Motifs', 'Cobalt Blue', 'Lead-Free Glaze'],
      confidenceScore: 0.96,
    );
  }
}

class MockTranslationService implements TranslationService {
  @override
  Future<TranslationResult> translate({
    required String text,
    required String targetLanguage,
    String? sourceLanguage,
  }) async {
    await Future.delayed(const Duration(milliseconds: 600));

    // Handle mixed language / code-mixing simulation
    final isMixed = text.contains('Ee') || text.contains('kavali') || text.contains('chahiye') || text.contains('bhaiya');

    String translated = text;
    if (targetLanguage == 'hi') {
      if (text.contains('basket') || text.contains('pieces')) {
        translated = 'मुझे इस हस्तशिल्प टोकरी के 50 पीस चाहिए। क्या थोक छूट उपलब्ध है?';
      } else {
        translated = 'पारंपरिक जयपुर ब्लू पॉटरी हस्तशिल्प फूलदान शुद्ध क्वार्ट्ज से निर्मित।';
      }
    } else if (targetLanguage == 'te') {
      if (text.contains('basket') || text.contains('pieces')) {
        translated = 'నాకు ఈ చేతితో తయారు చేసిన బుట్ట 50 ముక్కలు కావాలి. హోల్‌సేల్ ధర ఎంత?';
      } else {
        translated = 'సాంప్రదాయ జైపూర్ బ్లూ పాట్ ఫ్లవర్ వాజ్ సహజ క్వార్ట్జ్ క్లే తో తయారు చేయబడింది.';
      }
    } else {
      if (isMixed) {
        translated = 'I need 50 pieces of this handcrafted basket. Please provide quotation.';
      } else {
        translated = 'Traditional handcrafted Jaipur Blue Pottery Urn made from quartz clay.';
      }
    }

    return TranslationResult(
      originalText: text,
      sourceLanguage: sourceLanguage ?? 'auto-detect',
      targetLanguage: targetLanguage,
      translatedText: translated,
      isMixedLanguage: isMixed,
    );
  }

  @override
  Future<Map<String, String>> translateToAllSupportedLanguages(String text) async {
    await Future.delayed(const Duration(milliseconds: 800));
    return {
      'en': 'Handcrafted authentic Indian artisan masterpiece with registered GI heritage tag.',
      'hi': 'पंजीकृत जीआई विरासत टैग के साथ हस्तनिर्मित प्रामाणिक भारतीय कारीगर उत्कृष्ट कृति।',
      'te': 'రిజిస్టర్డ్ GI వారసత్వ ట్యాగ్‌తో చేతితో రూపొందించిన ప్రామాణిక భారతీయ కళాఖండం.',
    };
  }
}

class MockSpeechToTextService implements SpeechToTextService {
  final _streamController = StreamController<String>.broadcast();
  Timer? _mockSpeechTimer;

  @override
  Stream<String> startListening({SupportedLanguage preferredLanguage = SupportedLanguage.hinglish}) {
    // Simulate real-time streaming speech transcription with mixed language
    final phrases = [
      'Ee basket ki...',
      'Ee basket ki 50 pieces...',
      'Ee basket ki 50 pieces kavali, wholesale quote ivvandi.',
    ];
    int step = 0;

    _mockSpeechTimer?.cancel();
    _mockSpeechTimer = Timer.periodic(const Duration(milliseconds: 700), (timer) {
      if (step < phrases.length) {
        _streamController.add(phrases[step]);
        step++;
      } else {
        timer.cancel();
      }
    });

    return _streamController.stream;
  }

  @override
  Future<String> stopListening() async {
    _mockSpeechTimer?.cancel();
    return 'Ee basket ki 50 pieces kavali, wholesale quote ivvandi.';
  }

  @override
  Future<void> cancelListening() async {
    _mockSpeechTimer?.cancel();
  }
}

class MockTextToSpeechService implements TextToSpeechService {
  @override
  Future<void> speak({required String text, SupportedLanguage language = SupportedLanguage.english}) async {
    // Simulating audio synthesis playback
    await Future.delayed(const Duration(milliseconds: 1500));
  }

  @override
  Future<void> stop() async {}
}

class MockPricingService implements PricingService {
  @override
  Future<PricingSuggestionResult> calculateFairPricing({
    required String craftCategory,
    required String material,
    required double estimatedHours,
    int? customMoq,
  }) async {
    await Future.delayed(const Duration(milliseconds: 700));

    const rawMaterialCost = 450.0;
    const artisanWagePerHour = 180.0;
    final laborCost = estimatedHours * artisanWagePerHour;
    final baseCost = rawMaterialCost + laborCost;

    final retail = (baseCost * 2.2).roundToDouble();
    final wholesale = (baseCost * 1.45).roundToDouble();

    return PricingSuggestionResult(
      suggestedRetailPrice: retail,
      suggestedWholesalePrice: wholesale,
      suggestedMoq: customMoq ?? 15,
      estimatedLaborCost: laborCost,
      estimatedRawMaterialCost: rawMaterialCost,
      marketAveragePrice: retail * 1.15,
      pricingRationale: 'Calculated using 100% fair-wage standard (₹180/hr artisan rate for $estimatedHours hrs) + ₹450 raw material costs with 45% minimum wholesale artisan margin.',
    );
  }
}

class MockRecommendationService implements RecommendationService {
  @override
  Future<List<String>> getRecommendedProductIds({
    required String userId,
    List<String>? recentInterests,
    String? preferredRegion,
  }) async {
    await Future.delayed(const Duration(milliseconds: 400));
    return ['prod-001', 'prod-002', 'prod-003', 'prod-004', 'prod-005'];
  }
}

class MockAIService implements AIService {
  final VisionService visionService;
  final TranslationService translationService;
  final PricingService pricingService;

  MockAIService({
    required this.visionService,
    required this.translationService,
    required this.pricingService,
  });

  @override
  Future<GeneratedCatalogueData> generateCatalogue({
    required ProductUnderstandingResult visionData,
    required PricingSuggestionResult pricingData,
  }) async {
    await Future.delayed(const Duration(milliseconds: 1000));
    return const GeneratedCatalogueData(
      title: 'GI Hand-Painted Blue Pottery 14" Royal Floral Urn Vase',
      shortDescription: 'Masterpiece handcrafted from quartz and natural Egyptian frit glass using 400-year Rajasthani heritage techniques.',
      fullStoryDescription: 'Shaped without clay on traditional potters\' wheels using pulverized quartz stone, Fuller\'s earth, and natural plant gum. The brilliant cobalt blue is hand-painted with fine squirrel-hair brushes by master artisans in Kot Jewar, Jaipur.',
      careInstructions: 'Clean gently with a soft dry cloth. Non-porous decorative ceramic. Avoid acidic detergents.',
      seoKeywords: 'Jaipur blue pottery, GI certified Indian handicraft, handmade ceramic urn, authentic Rajasthani craft, wholesale pottery export',
      localizedTitles: {
        'en': 'GI Hand-Painted Blue Pottery 14" Royal Floral Urn Vase',
        'hi': 'जीआई प्रमाणित हस्तनिर्मित जयपुर ब्लू पॉटरी 14 इंच रॉयल फ्लोरल फूलदान',
        'te': 'GI సర్టిఫైడ్ చేతితో చిత్రించిన జైపూర్ బ్లూ పాట్ 14" రాయల్ ఫ్లోరల్ వాజ్',
      },
      localizedDescriptions: {
        'en': 'Authentic GI tagged blue pottery urn vase directly from master artisans of Jaipur.',
        'hi': 'जयपुर के मास्टर कारीगरों द्वारा सीधे तैयार किया गया प्रामाणिक जीआई टैग वाला ब्लू पॉटरी फूलदान।',
        'te': 'జైపూర్ మాస్టర్ కళాకారుల నుండి నేరుగా వచ్చిన ప్రామాణిక GI బ్లూ పాట్ ఫ్లవర్ వాజ్.',
      },
      craftHeritageHighlights: [
        'Geographical Indication (GI) Verified',
        '100% Lead-Free Natural Mineral Glaze',
        '18 Hours of Single-Artisan Brush Detailing',
      ],
    );
  }

  @override
  Future<String> generateMarketingContent({
    required String productTitle,
    required String craftTechnique,
    required String artisanHeritage,
  }) async {
    await Future.delayed(const Duration(milliseconds: 600));
    return '🏺 Discover the soul of Indian craftsmanship. "$productTitle", shaped using centuries-old $craftTechnique. Direct from $artisanHeritage. Every purchase preserves generational heritage and provides fair artisan wages. #KalaCart #VocalForLocal #IndianHandicrafts';
  }

  @override
  Future<VoiceIntentResult> processVoiceCommand({
    required String rawVoiceText,
    required bool isArtisanMode,
  }) async {
    await Future.delayed(const Duration(milliseconds: 800));

    final lower = rawVoiceText.toLowerCase();

    // Mixed language intent parser
    if (lower.contains('kavali') || lower.contains('pieces') || lower.contains('order') || lower.contains('chahiye') || lower.contains('rfq')) {
      return VoiceIntentResult(
        rawTranscript: rawVoiceText,
        recognizedLanguage: 'Telugu + English (Mixed)',
        intentType: 'rfq_inquiry',
        extractedEntities: {
          'item': 'basket',
          'quantity': 50,
          'targetPrice': 'Negotiable Wholesale',
        },
        assistantResponseText: 'I understand you want to request a wholesale quote for 50 pieces of this basket. Would you like me to open the RFQ proposal screen?',
      );
    } else if (lower.contains('price') || lower.contains('kitna') || lower.contains('dhara') || lower.contains('cost')) {
      return VoiceIntentResult(
        rawTranscript: rawVoiceText,
        recognizedLanguage: 'Hindi + English',
        intentType: 'price_check',
        extractedEntities: {'category': 'Blue Pottery', 'pricingType': 'Fair Artisan Rate'},
        assistantResponseText: 'The fair trade retail price is ₹2,850 and wholesale tier starts at ₹1,950 per piece for MOQ of 10.',
      );
    } else {
      return VoiceIntentResult(
        rawTranscript: rawVoiceText,
        recognizedLanguage: 'Multi-lingual Indian English',
        intentType: 'artisan_help',
        extractedEntities: {'topic': 'General Handicraft Query'},
        assistantResponseText: 'I am your KalaCart AI assistant. How can I help with your craft order, catalogue translation, or RFQ bids?',
      );
    }
  }

  @override
  Future<String> queryAssistant({
    required String message,
    required bool isArtisanMode,
    List<Map<String, String>> conversationHistory = const [],
  }) async {
    await Future.delayed(const Duration(milliseconds: 900));

    if (isArtisanMode) {
      if (message.contains('price') || message.contains('cost') || message.contains('daam')) {
        return 'Based on raw quartz costs (₹450) and 18 hours of detailed painting, I suggest listing this vase at ₹2,850 retail and ₹1,950 wholesale (MOQ 15). This guarantees you a 45% net profit.';
      }
      return 'I can assist you in generating multi-language descriptions (Hindi, Telugu, English), verifying GI tag eligibility, and setting competitive B2B wholesale prices.';
    } else {
      if (message.contains('kavali') || message.contains('buy') || message.contains('order')) {
        return 'You can place an instant live order or submit a customized B2B RFQ with your target price directly to the master artisan!';
      }
      return 'This piece is 100% authentic GI certified from Jaipur Blue Pottery Guild with digital provenance verification.';
    }
  }
}
