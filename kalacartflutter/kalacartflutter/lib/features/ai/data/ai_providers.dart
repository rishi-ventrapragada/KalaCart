import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../domain/ai_service_interfaces.dart';
import 'mock_ai_services.dart';

final visionServiceProvider = Provider<VisionService>((ref) {
  return MockVisionService();
});

final translationServiceProvider = Provider<TranslationService>((ref) {
  return MockTranslationService();
});

final speechToTextServiceProvider = Provider<SpeechToTextService>((ref) {
  return MockSpeechToTextService();
});

final textToSpeechServiceProvider = Provider<TextToSpeechService>((ref) {
  return MockTextToSpeechService();
});

final pricingServiceProvider = Provider<PricingService>((ref) {
  return MockPricingService();
});

final recommendationServiceProvider = Provider<RecommendationService>((ref) {
  return MockRecommendationService();
});

final aiServiceProvider = Provider<AIService>((ref) {
  return MockAIService(
    visionService: ref.watch(visionServiceProvider),
    translationService: ref.watch(translationServiceProvider),
    pricingService: ref.watch(pricingServiceProvider),
  );
});
