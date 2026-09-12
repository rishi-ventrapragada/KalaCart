import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http_parser/http_parser.dart';

import '../../../core/network/api_client.dart';
import '../domain/backend_ai_models.dart';

/// Calls the three live FastAPI endpoints.
///
/// Contracts verified against the deployed backend on 2026-09-12; see
/// `backend_ai_models.dart` for the response shapes.
class BackendAiRepository {
  BackendAiRepository(this._dio);

  final Dio _dio;

  /// Builds the `image` part of a multipart request.
  ///
  /// The backend validates the extension against {jpg, jpeg, png, webp} and the
  /// MIME against a matching allowlist, returning 400 for anything else. A file
  /// from `image_picker` can arrive as a cache path whose extension is missing
  /// or unusual (`.jfif` on some devices), and `MultipartFile.fromFile` sends
  /// no content type at all — so both are set explicitly here rather than left
  /// to be inferred.
  Future<MultipartFile> _imagePart(String path) async {
    final lower = path.toLowerCase();
    final isPng = lower.endsWith('.png');
    final isWebp = lower.endsWith('.webp');
    final extension = isPng
        ? 'png'
        : isWebp
            ? 'webp'
            : 'jpg';
    final mimeSubtype = isPng
        ? 'png'
        : isWebp
            ? 'webp'
            : 'jpeg';
    return MultipartFile.fromFile(
      path,
      filename: 'upload.$extension',
      contentType: MediaType('image', mimeSubtype),
    );
  }

  /// `POST /api/v1/image/enhance` — OpenCV background removal, CLAHE, compose
  /// on white, crop and resize. No LLM, so this path is unaffected by the
  /// OpenRouter free-tier limits.
  ///
  /// [imagePath] is a local file path from the camera or gallery.
  Future<EnhancedImageResult> enhanceImage({
    required String imagePath,
    String outputFormat = '1:1',
    bool enhance = true,
  }) async {
    final form = FormData.fromMap({
      'image': await _imagePart(imagePath),
      'output_format': outputFormat,
      'enhance': enhance.toString(),
    });
    final response = await _dio.post<dynamic>('/api/v1/image/enhance', data: form);
    return EnhancedImageResult.fromResponse(unwrapResponse(response));
  }

  /// `POST /api/v1/pricing/analyze` — vision extraction plus a deterministic
  /// price from the backend's pricing engine.
  ///
  /// The image is optional. Supplying [category], [size], [quality] and
  /// [complexity] together makes the backend skip the AI call entirely, which
  /// is both instant and immune to upstream model rate limits — so pass them
  /// whenever they are known.
  Future<PricingBreakdown> analyzePricing({
    required String description,
    String? imagePath,
    String? title,
    String? category,
    String? materials,
    double? materialCost,
    double? labourHours,
    String marketPosition = 'Standard',
    String? size,
    String? quality,
    int? complexity,
  }) async {
    final map = <String, dynamic>{
      'description': description,
      'market_position': marketPosition,
      if (title != null && title.isNotEmpty) 'title': title,
      if (category != null && category.isNotEmpty) 'category': category,
      if (materials != null && materials.isNotEmpty) 'materials': materials,
      if (materialCost != null) 'material_cost': materialCost,
      if (labourHours != null) 'labour_hours': labourHours,
      if (size != null && size.isNotEmpty) 'size': size,
      if (quality != null && quality.isNotEmpty) 'quality': quality,
      if (complexity != null) 'complexity': complexity,
      if (imagePath != null) 'image': await _imagePart(imagePath),
    };
    final response = await _dio.post<dynamic>(
      '/api/v1/pricing/analyze',
      data: FormData.fromMap(map),
    );
    return PricingBreakdown.fromResponse(unwrapResponse(response));
  }

  /// `POST /api/v1/catalog/generate` — turns a transcript into a listing.
  ///
  /// This is the text endpoint. The audio one (`/catalog/voice`) is dormant by
  /// design: it needs a paid Sarvam key, so speech-to-text runs on-device and
  /// only the resulting text is sent here.
  ///
  /// The backend requires 5-1000 characters and one of te|hi|en|ta|kn, so the
  /// transcript is clamped rather than left to fail validation server-side.
  Future<GeneratedCatalog> generateCatalog({
    required String transcript,
    String language = 'hi',
  }) async {
    final clean = transcript.trim();
    final clamped = clean.length > 1000 ? clean.substring(0, 1000) : clean;
    const supported = {'te', 'hi', 'en', 'ta', 'kn'};
    final lang = supported.contains(language) ? language : 'en';

    final response = await _dio.post<dynamic>(
      '/api/v1/catalog/generate',
      data: {'transcript': clamped, 'language': lang},
    );
    return GeneratedCatalog.fromResponse(unwrapResponse(response));
  }
}

// Providers

/// Set to true to fall back to the bundled mock services for an offline demo.
/// Defaults to false: the real endpoints are the intended path.
final useMockAiProvider = StateProvider<bool>((ref) => false);

final backendAiRepositoryProvider = Provider<BackendAiRepository>((ref) {
  return BackendAiRepository(ref.watch(apiClientProvider));
});
