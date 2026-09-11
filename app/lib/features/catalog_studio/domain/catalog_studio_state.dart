enum CatalogStudioStage {
  capture,
  reviewingImages,
  analyzing,
  identifying,
  generating,
  translating,
  pricing,
  ready,
  error,
}

class CapturedImageItem {
  final String id;
  final String label;
  final String assetMockPath;
  final bool isPrimary;
  final int rotationDegrees;
  final bool isEnhanced;

  const CapturedImageItem({
    required this.id,
    required this.label,
    required this.assetMockPath,
    this.isPrimary = false,
    this.rotationDegrees = 0,
    this.isEnhanced = false,
  });

  CapturedImageItem copyWith({
    String? id,
    String? label,
    String? assetMockPath,
    bool? isPrimary,
    int? rotationDegrees,
    bool? isEnhanced,
  }) {
    return CapturedImageItem(
      id: id ?? this.id,
      label: label ?? this.label,
      assetMockPath: assetMockPath ?? this.assetMockPath,
      isPrimary: isPrimary ?? this.isPrimary,
      rotationDegrees: rotationDegrees ?? this.rotationDegrees,
      isEnhanced: isEnhanced ?? this.isEnhanced,
    );
  }
}

class AiGeneratedCraftData {
  final String title;
  final String description;
  final String category;
  final String materials;
  final String craftTechnique;
  final String dimensions;
  final String weight;
  final List<String> tags;
  final String careInstructions;
  final String seoDescription;
  final double retailPrice;
  final double wholesalePrice;
  final int suggestedMoq;
  final String englishTranslation;
  final String hindiTranslation;
  final String teluguTranslation;
  final String bengaliTranslation;
  final String marketingCopyShort;
  final String marketingCopySocial;
  final String giClusterDetected;
  final double authenticityConfidence;

  const AiGeneratedCraftData({
    required this.title,
    required this.description,
    required this.category,
    required this.materials,
    required this.craftTechnique,
    required this.dimensions,
    required this.weight,
    required this.tags,
    required this.careInstructions,
    required this.seoDescription,
    required this.retailPrice,
    required this.wholesalePrice,
    required this.suggestedMoq,
    required this.englishTranslation,
    required this.hindiTranslation,
    required this.teluguTranslation,
    required this.bengaliTranslation,
    required this.marketingCopyShort,
    required this.marketingCopySocial,
    required this.giClusterDetected,
    this.authenticityConfidence = 0.98,
  });

  AiGeneratedCraftData copyWith({
    String? title,
    String? description,
    String? category,
    String? materials,
    String? craftTechnique,
    String? dimensions,
    String? weight,
    List<String>? tags,
    String? careInstructions,
    String? seoDescription,
    double? retailPrice,
    double? wholesalePrice,
    int? suggestedMoq,
    String? englishTranslation,
    String? hindiTranslation,
    String? teluguTranslation,
    String? bengaliTranslation,
    String? marketingCopyShort,
    String? marketingCopySocial,
    String? giClusterDetected,
    double? authenticityConfidence,
  }) {
    return AiGeneratedCraftData(
      title: title ?? this.title,
      description: description ?? this.description,
      category: category ?? this.category,
      materials: materials ?? this.materials,
      craftTechnique: craftTechnique ?? this.craftTechnique,
      dimensions: dimensions ?? this.dimensions,
      weight: weight ?? this.weight,
      tags: tags ?? this.tags,
      careInstructions: careInstructions ?? this.careInstructions,
      seoDescription: seoDescription ?? this.seoDescription,
      retailPrice: retailPrice ?? this.retailPrice,
      wholesalePrice: wholesalePrice ?? this.wholesalePrice,
      suggestedMoq: suggestedMoq ?? this.suggestedMoq,
      englishTranslation: englishTranslation ?? this.englishTranslation,
      hindiTranslation: hindiTranslation ?? this.hindiTranslation,
      teluguTranslation: teluguTranslation ?? this.teluguTranslation,
      bengaliTranslation: bengaliTranslation ?? this.bengaliTranslation,
      marketingCopyShort: marketingCopyShort ?? this.marketingCopyShort,
      marketingCopySocial: marketingCopySocial ?? this.marketingCopySocial,
      giClusterDetected: giClusterDetected ?? this.giClusterDetected,
      authenticityConfidence: authenticityConfidence ?? this.authenticityConfidence,
    );
  }
}

class CatalogStudioSessionState {
  final CatalogStudioStage stage;
  final List<CapturedImageItem> images;
  final AiGeneratedCraftData? generatedData;
  final double progress;
  final String stageMessage;
  final String? errorMessage;
  final int selectedSamplePresetIndex;

  const CatalogStudioSessionState({
    this.stage = CatalogStudioStage.capture,
    this.images = const [],
    this.generatedData,
    this.progress = 0.0,
    this.stageMessage = 'Ready to capture craft',
    this.errorMessage,
    this.selectedSamplePresetIndex = 0,
  });

  CatalogStudioSessionState copyWith({
    CatalogStudioStage? stage,
    List<CapturedImageItem>? images,
    AiGeneratedCraftData? generatedData,
    double? progress,
    String? stageMessage,
    String? errorMessage,
    int? selectedSamplePresetIndex,
  }) {
    return CatalogStudioSessionState(
      stage: stage ?? this.stage,
      images: images ?? this.images,
      generatedData: generatedData ?? this.generatedData,
      progress: progress ?? this.progress,
      stageMessage: stageMessage ?? this.stageMessage,
      errorMessage: errorMessage ?? this.errorMessage,
      selectedSamplePresetIndex: selectedSamplePresetIndex ?? this.selectedSamplePresetIndex,
    );
  }
}
