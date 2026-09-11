import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_constants.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/widgets/app_button.dart';
import '../../../core/widgets/app_card.dart';
import '../../../shared/models/product.dart';
import '../../auth/data/auth_repository.dart';
import '../../auth/data/supabase_auth_repository.dart';
import '../../products/data/supabase_products_repository.dart';
import '../data/catalog_studio_repository.dart';
import '../domain/catalog_studio_state.dart';

class CatalogStudioScreen extends ConsumerStatefulWidget {
  const CatalogStudioScreen({super.key});

  @override
  ConsumerState<CatalogStudioScreen> createState() => _CatalogStudioScreenState();
}

class _CatalogStudioScreenState extends ConsumerState<CatalogStudioScreen> with SingleTickerProviderStateMixin {
  late TabController _translationTabController;
  final TextEditingController _titleController = TextEditingController();
  final TextEditingController _categoryController = TextEditingController();
  final TextEditingController _materialsController = TextEditingController();
  final TextEditingController _techniqueController = TextEditingController();
  final TextEditingController _dimensionsController = TextEditingController();
  final TextEditingController _weightController = TextEditingController();
  final TextEditingController _descController = TextEditingController();
  final TextEditingController _retailPriceController = TextEditingController();
  final TextEditingController _wholesalePriceController = TextEditingController();
  final TextEditingController _moqController = TextEditingController();
  final TextEditingController _stockController = TextEditingController();

  bool _isSaving = false;
  ProductStatus? _savingAs;

  @override
  void initState() {
    super.initState();
    _translationTabController = TabController(length: 4, vsync: this);
    // The studio provider is app-wide, so a previous run may already be ready.
    final existing = ref.read(catalogStudioProvider);
    if (existing.stage == CatalogStudioStage.ready && existing.generatedData != null) {
      _populateControllers(existing.generatedData!);
    }
  }

  @override
  void dispose() {
    _translationTabController.dispose();
    _titleController.dispose();
    _categoryController.dispose();
    _materialsController.dispose();
    _techniqueController.dispose();
    _dimensionsController.dispose();
    _weightController.dispose();
    _descController.dispose();
    _retailPriceController.dispose();
    _wholesalePriceController.dispose();
    _moqController.dispose();
    _stockController.dispose();
    super.dispose();
  }

  /// Copies the simulated AI output into the editable fields. Called once per
  /// generation (when the stage becomes ready) so later user edits are kept.
  void _populateControllers(AiGeneratedCraftData data) {
    _titleController.text = data.title;
    _categoryController.text = data.category;
    _materialsController.text = data.materials;
    _techniqueController.text = data.craftTechnique;
    _dimensionsController.text = data.dimensions;
    _weightController.text = data.weight;
    _descController.text = data.description;
    _retailPriceController.text = data.retailPrice.toStringAsFixed(0);
    _wholesalePriceController.text = data.wholesalePrice.toStringAsFixed(0);
    _moqController.text = data.suggestedMoq.toString();
    _stockController.text = '10';
  }

  void _clearControllers() {
    _titleController.clear();
    _categoryController.clear();
    _materialsController.clear();
    _techniqueController.clear();
    _dimensionsController.clear();
    _weightController.clear();
    _descController.clear();
    _retailPriceController.clear();
    _wholesalePriceController.clear();
    _moqController.clear();
    _stockController.clear();
  }

  void _resetStudio() {
    _clearControllers();
    ref.read(catalogStudioProvider.notifier).resetStudio();
  }

  void _showSnack(String message, {bool isError = false}) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        behavior: SnackBarBehavior.floating,
        backgroundColor: isError ? AppColors.error : null,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    ref.listen<CatalogStudioSessionState>(catalogStudioProvider, (previous, next) {
      final becameReady = next.stage == CatalogStudioStage.ready && previous?.stage != CatalogStudioStage.ready;
      if (becameReady && next.generatedData != null) {
        _populateControllers(next.generatedData!);
      }
    });

    final state = ref.watch(catalogStudioProvider);
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(6),
              decoration: const BoxDecoration(
                color: Color(0xFF6A1B9A),
                borderRadius: AppRadius.borderSm,
              ),
              child: const Icon(Icons.auto_awesome, color: Colors.white, size: 18),
            ),
            AppSpacing.gapH10,
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Kala-AI Catalog Studio',
                  style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                ),
                Text(
                  'Simulation · AI vision & multilingual cataloguer',
                  style: theme.textTheme.bodySmall?.copyWith(fontSize: 10, color: isDark ? AppColors.textTertiaryDark : AppColors.textSecondaryLight),
                ),
              ],
            ),
          ],
        ),
        actions: [
          if (state.stage == CatalogStudioStage.ready)
            IconButton(
              icon: const Icon(Icons.refresh_rounded),
              tooltip: 'Reset Studio',
              onPressed: _isSaving ? null : _resetStudio,
            ),
        ],
      ),
      body: _buildCurrentStageView(state, theme, isDark),
    );
  }

  Widget _buildCurrentStageView(CatalogStudioSessionState state, ThemeData theme, bool isDark) {
    switch (state.stage) {
      case CatalogStudioStage.capture:
      case CatalogStudioStage.reviewingImages:
        return _buildCaptureAndReviewView(state, theme, isDark);

      case CatalogStudioStage.analyzing:
      case CatalogStudioStage.identifying:
      case CatalogStudioStage.generating:
      case CatalogStudioStage.translating:
      case CatalogStudioStage.pricing:
        return _buildProcessingPipelineView(state, theme, isDark);

      case CatalogStudioStage.ready:
        return _buildGeneratedCatalogueReview(state, theme, isDark);

      case CatalogStudioStage.error:
        return Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.red),
              AppSpacing.gapV12,
              Text(state.errorMessage ?? 'An error occurred during AI processing'),
              AppSpacing.gapV16,
              ElevatedButton(
                onPressed: _resetStudio,
                child: const Text('Try Again'),
              ),
            ],
          ),
        );
    }
  }

  // Stage 1 & 2: Camera Capture, Preset Selection & Image Review
  Widget _buildCaptureAndReviewView(CatalogStudioSessionState state, ThemeData theme, bool isDark) {
    return ListView(
      padding: AppSpacing.paddingAllBase,
      children: [
        // AI Dev Notice Banner
        Container(
          padding: AppSpacing.paddingAllSm,
          decoration: BoxDecoration(
            color: const Color(0xFF6A1B9A).withValues(alpha: 0.1),
            borderRadius: AppRadius.borderMd,
            border: Border.all(color: const Color(0xFF6A1B9A).withValues(alpha: 0.3)),
          ),
          child: const Row(
            children: [
              Icon(Icons.developer_mode, size: 18, color: Color(0xFF6A1B9A)),
              SizedBox(width: 8),
              Expanded(
                child: Text(
                  'Kala-AI Simulation Mode: Test instant craft cataloging using preset Indian handicraft photos or upload custom ones.',
                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.w500),
                ),
              ),
            ],
          ),
        ),
        AppSpacing.gapV16,

        // Select Craft Preset
        Text('Select Mock Craft Preset for AI Demo', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
        AppSpacing.gapV8,
        Row(
          children: [
            _buildPresetChip(0, '🏺 Jaipur Blue Pottery', state.selectedSamplePresetIndex),
            AppSpacing.gapH8,
            _buildPresetChip(1, '🌿 Pedana Kalamkari', state.selectedSamplePresetIndex),
            AppSpacing.gapH8,
            _buildPresetChip(2, '🔥 Bastar Dhokra', state.selectedSamplePresetIndex),
          ],
        ),
        AppSpacing.gapV16,

        // Camera Viewfinder Canvas
        Container(
          height: 260,
          width: double.infinity,
          decoration: BoxDecoration(
            color: Colors.black,
            borderRadius: AppRadius.borderLg,
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.2),
                blurRadius: 10,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: Stack(
            children: [
              Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.15),
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.camera_alt_outlined, size: 48, color: Colors.white),
                    ),
                    AppSpacing.gapV8,
                    const Text(
                      'Position handicraft inside the frame',
                      style: TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.bold),
                    ),
                    AppSpacing.gapV4,
                    const Text(
                      'AI detects natural glazes, weave count, and GI marks',
                      style: TextStyle(color: Colors.white70, fontSize: 11),
                    ),
                  ],
                ),
              ),

              // Viewfinder Grid Overlay
              Positioned.fill(
                child: Container(
                  margin: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    border: Border.all(color: Colors.white.withValues(alpha: 0.35), width: 1.5),
                    borderRadius: AppRadius.borderMd,
                  ),
                ),
              ),

              // Camera Controls Overlay
              Positioned(
                bottom: 12,
                left: 16,
                right: 16,
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    IconButton(
                      icon: const Icon(Icons.flash_auto, color: Colors.white),
                      onPressed: () {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Flash set to Auto-Detect Studio Light'), duration: Duration(seconds: 1)),
                        );
                      },
                    ),
                    GestureDetector(
                      onTap: () {
                        final newId = 'img-${DateTime.now().millisecondsSinceEpoch}';
                        ref.read(catalogStudioProvider.notifier).addImage(
                              CapturedImageItem(
                                id: newId,
                                label: 'Angle Photo #${state.images.length + 1}',
                                assetMockPath: 'assets/mock/camera_snap.jpg',
                                isPrimary: state.images.isEmpty,
                                isEnhanced: true,
                              ),
                            );
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Photo added to review list!'), duration: Duration(seconds: 1)),
                        );
                      },
                      child: Container(
                        padding: const EdgeInsets.all(4),
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          border: Border.all(color: Colors.white, width: 3),
                        ),
                        child: Container(
                          width: 52,
                          height: 52,
                          decoration: const BoxDecoration(
                            color: Color(0xFF6A1B9A),
                            shape: BoxShape.circle,
                          ),
                          child: const Icon(Icons.camera_rounded, color: Colors.white, size: 28),
                        ),
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.flip_camera_ios, color: Colors.white),
                      onPressed: () {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Switched to Macro Sensor for Handloom Texture'), duration: Duration(seconds: 1)),
                        );
                      },
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        AppSpacing.gapV20,

        // Selected Images Review Header
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              'Selected Photos (${state.images.length})',
              style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold),
            ),
            TextButton.icon(
              icon: const Icon(Icons.add_photo_alternate_outlined, size: 16),
              label: const Text('Add More'),
              onPressed: () {
                final newId = 'img-${DateTime.now().millisecondsSinceEpoch}';
                ref.read(catalogStudioProvider.notifier).addImage(
                      CapturedImageItem(
                        id: newId,
                        label: 'Detail Shot #${state.images.length + 1}',
                        assetMockPath: 'assets/mock/detail.jpg',
                        isPrimary: false,
                        isEnhanced: true,
                      ),
                    );
              },
            ),
          ],
        ),
        AppSpacing.gapV8,

        if (state.images.isEmpty)
          Container(
            padding: AppSpacing.paddingAllLg,
            decoration: BoxDecoration(
              color: isDark ? AppColors.surfaceDark : AppColors.surfaceLight,
              borderRadius: AppRadius.borderMd,
            ),
            child: const Center(
              child: Text('No photos added yet. Tap shutter to capture craft angles.'),
            ),
          )
        else
          SizedBox(
            height: 140,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: state.images.length,
              separatorBuilder: (_, __) => AppSpacing.gapH12,
              itemBuilder: (context, index) {
                final img = state.images[index];
                return Stack(
                  children: [
                    Container(
                      width: 130,
                      decoration: BoxDecoration(
                        color: isDark ? AppColors.surfaceDark : Colors.white,
                        borderRadius: AppRadius.borderMd,
                        border: Border.all(
                          color: img.isPrimary ? const Color(0xFF6A1B9A) : (isDark ? AppColors.borderDark : AppColors.borderLight),
                          width: img.isPrimary ? 2.0 : 1.0,
                        ),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.center,
                        children: [
                          Expanded(
                            child: Container(
                              decoration: BoxDecoration(
                                color: const Color(0xFF6A1B9A).withValues(alpha: 0.1),
                                borderRadius: const BorderRadius.vertical(top: Radius.circular(8)),
                              ),
                              child: Center(
                                child: Icon(
                                  Icons.image_outlined,
                                  size: 36,
                                  color: const Color(0xFF6A1B9A).withValues(alpha: 0.7),
                                ),
                              ),
                            ),
                          ),
                          Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
                            child: Column(
                              children: [
                                Text(
                                  img.label,
                                  style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                                GestureDetector(
                                  onTap: () {
                                    ref.read(catalogStudioProvider.notifier).toggleEnhancedBackground(img.id);
                                  },
                                  child: Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Icon(
                                        img.isEnhanced ? Icons.auto_fix_high : Icons.auto_fix_normal,
                                        size: 11,
                                        color: img.isEnhanced ? const Color(0xFF6A1B9A) : Colors.grey,
                                      ),
                                      const SizedBox(width: 3),
                                      Text(
                                        img.isEnhanced ? 'AI Studio BG' : 'Original BG',
                                        style: TextStyle(
                                          fontSize: 9,
                                          fontWeight: FontWeight.bold,
                                          color: img.isEnhanced ? const Color(0xFF6A1B9A) : Colors.grey,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),

                    // Remove button
                    Positioned(
                      top: 4,
                      right: 4,
                      child: GestureDetector(
                        onTap: () {
                          ref.read(catalogStudioProvider.notifier).removeImage(img.id);
                        },
                        child: Container(
                          padding: const EdgeInsets.all(3),
                          decoration: const BoxDecoration(
                            color: Colors.black54,
                            shape: BoxShape.circle,
                          ),
                          child: const Icon(Icons.close, size: 12, color: Colors.white),
                        ),
                      ),
                    ),

                    if (img.isPrimary)
                      Positioned(
                        top: 4,
                        left: 4,
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                          decoration: const BoxDecoration(
                            color: Color(0xFF6A1B9A),
                            borderRadius: AppRadius.borderXs,
                          ),
                          child: const Text('COVER', style: TextStyle(color: Colors.white, fontSize: 8, fontWeight: FontWeight.bold)),
                        ),
                      ),
                  ],
                );
              },
            ),
          ),
        AppSpacing.gapV24,

        // Run AI Button
        SizedBox(
          width: double.infinity,
          height: 48,
          child: ElevatedButton.icon(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF6A1B9A),
              foregroundColor: Colors.white,
              shape: AppRadius.shapeMd,
              elevation: 3,
            ),
            icon: const Icon(Icons.auto_awesome_rounded),
            label: const Text(
              'Process & Understand Craft with AI',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
            ),
            onPressed: state.images.isEmpty
                ? null
                : () {
                    ref.read(catalogStudioProvider.notifier).startAiProcessing();
                  },
          ),
        ),
        AppSpacing.gapV32,
      ],
    );
  }

  Widget _buildPresetChip(int index, String label, int selectedIndex) {
    final isSelected = index == selectedIndex;
    return Expanded(
      child: GestureDetector(
        onTap: () {
          ref.read(catalogStudioProvider.notifier).selectPresetSample(index);
        },
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 6),
          decoration: BoxDecoration(
            color: isSelected ? const Color(0xFF6A1B9A) : Colors.transparent,
            borderRadius: AppRadius.borderMd,
            border: Border.all(
              color: isSelected ? const Color(0xFF6A1B9A) : Colors.grey.shade400,
              width: 1.2,
            ),
          ),
          child: Text(
            label,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.bold,
              color: isSelected ? Colors.white : null,
            ),
          ),
        ),
      ),
    );
  }

  // Stage 3: Animated AI Processing Pipeline
  Widget _buildProcessingPipelineView(CatalogStudioSessionState state, ThemeData theme, bool isDark) {
    return Center(
      child: Padding(
        padding: AppSpacing.paddingAllXl,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Pulsing AI Mandala Scanner
            Container(
              width: 120,
              height: 120,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(
                  colors: [
                    const Color(0xFF6A1B9A).withValues(alpha: 0.3),
                    const Color(0xFFAB47BC).withValues(alpha: 0.1),
                    Colors.transparent,
                  ],
                ),
              ),
              child: Center(
                child: Container(
                  width: 80,
                  height: 80,
                  decoration: const BoxDecoration(
                    color: Color(0xFF6A1B9A),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.auto_awesome, color: Colors.white, size: 40),
                ),
              ),
            ),
            AppSpacing.gapV24,
            Text(
              'Kala-AI Understanding Engine',
              style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
            ),
            AppSpacing.gapV8,
            Text(
              state.stageMessage,
              textAlign: TextAlign.center,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: const Color(0xFF6A1B9A),
                fontWeight: FontWeight.w600,
              ),
            ),
            AppSpacing.gapV24,

            // Progress Bar
            ClipRRect(
              borderRadius: AppRadius.borderPill,
              child: LinearProgressIndicator(
                value: state.progress,
                minHeight: 8,
                backgroundColor: isDark ? Colors.grey.shade800 : Colors.grey.shade200,
                valueColor: const AlwaysStoppedAnimation<Color>(Color(0xFF6A1B9A)),
              ),
            ),
            AppSpacing.gapV16,

            // Pipeline Stages Checkmarks
            _buildStageRow('Visual & Surface Geometry Analysis', state.progress >= 0.20),
            _buildStageRow('GI Registry & Craft Cluster Identification', state.progress >= 0.45),
            _buildStageRow('Heritage Narrative & Material Composition', state.progress >= 0.68),
            _buildStageRow('Indian Languages Translation (HI, TE, BN)', state.progress >= 0.85),
            _buildStageRow('Hyperlocal Wholesale Tier & Fair Pricing', state.progress >= 0.95),
          ],
        ),
      ),
    );
  }

  Widget _buildStageRow(String title, bool isDone) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Icon(
            isDone ? Icons.check_circle_rounded : Icons.radio_button_unchecked,
            size: 16,
            color: isDone ? AppColors.success : Colors.grey,
          ),
          AppSpacing.gapH8,
          Text(
            title,
            style: TextStyle(
              fontSize: 12,
              color: isDone ? null : Colors.grey,
              fontWeight: isDone ? FontWeight.w600 : FontWeight.normal,
            ),
          ),
        ],
      ),
    );
  }

  // Stage 4: Generated Catalogue Review & Editing
  Widget _buildGeneratedCatalogueReview(CatalogStudioSessionState state, ThemeData theme, bool isDark) {
    final data = state.generatedData;
    if (data == null) return const SizedBox.shrink();
    final sellerId = ref.watch(currentUserProvider)?.sellerId;

    return ListView(
      padding: AppSpacing.paddingAllBase,
      children: [
        // Simulation notice
        Container(
          padding: AppSpacing.paddingAllSm,
          decoration: BoxDecoration(
            color: AppColors.aiStudio.withValues(alpha: 0.1),
            borderRadius: AppRadius.borderMd,
            border: Border.all(color: AppColors.aiStudio.withValues(alpha: 0.3)),
          ),
          child: const Row(
            children: [
              Icon(Icons.developer_mode, size: 18, color: AppColors.aiStudio),
              SizedBox(width: 8),
              Expanded(
                child: Text(
                  'Simulation: the fields below were generated from a preset sample, not from your photos. Review and edit them before publishing.',
                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.w500),
                ),
              ),
            ],
          ),
        ),
        AppSpacing.gapV12,

        // GI Cluster Authenticity Banner (simulated)
        Container(
          padding: AppSpacing.paddingAllBase,
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              colors: [Color(0xFF2E7D32), Color(0xFF43A047)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: AppRadius.borderMd,
          ),
          child: Row(
            children: [
              const Icon(Icons.verified_rounded, color: Colors.white, size: 28),
              AppSpacing.gapH12,
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'SIMULATED GI MATCH (${(data.authenticityConfidence * 100).toInt()}%)',
                      style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 0.5),
                    ),
                    Text(
                      data.giClusterDetected,
                      style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        AppSpacing.gapV16,

        // Generated Fields Editor
        Text('Generated Craft Information', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
        AppSpacing.gapV12,

        TextField(
          controller: _titleController,
          decoration: const InputDecoration(
            labelText: 'Craft Title',
            prefixIcon: Icon(Icons.title_rounded),
          ),
        ),
        AppSpacing.gapV12,

        Row(
          children: [
            Expanded(
              child: TextField(
                controller: _categoryController,
                decoration: const InputDecoration(
                  labelText: 'Craft Category',
                  prefixIcon: Icon(Icons.category_outlined),
                ),
              ),
            ),
            AppSpacing.gapH12,
            Expanded(
              child: TextField(
                controller: _techniqueController,
                decoration: const InputDecoration(
                  labelText: 'Craft Technique',
                  prefixIcon: Icon(Icons.handyman_outlined),
                ),
              ),
            ),
          ],
        ),
        AppSpacing.gapV12,

        TextField(
          controller: _materialsController,
          decoration: const InputDecoration(
            labelText: 'Materials & Dyes',
            prefixIcon: Icon(Icons.grass_outlined),
          ),
        ),
        AppSpacing.gapV12,

        Row(
          children: [
            Expanded(
              child: TextField(
                controller: _dimensionsController,
                decoration: const InputDecoration(
                  labelText: 'Dimensions',
                  prefixIcon: Icon(Icons.straighten_outlined),
                ),
              ),
            ),
            AppSpacing.gapH12,
            Expanded(
              child: TextField(
                controller: _weightController,
                decoration: const InputDecoration(
                  labelText: 'Weight',
                  prefixIcon: Icon(Icons.scale_outlined),
                ),
              ),
            ),
          ],
        ),
        AppSpacing.gapV12,

        TextField(
          controller: _descController,
          maxLines: 3,
          decoration: const InputDecoration(
            labelText: 'Artisan Narrative & Description',
            alignLabelWithHint: true,
          ),
        ),
        AppSpacing.gapV20,

        // Pricing Suggestions
        Text('Fair Artisan Pricing & Wholesale Recommendations', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
        AppSpacing.gapV8,
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: _retailPriceController,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: const InputDecoration(
                  labelText: 'Retail Price (₹)',
                  prefixIcon: Icon(Icons.currency_rupee),
                ),
              ),
            ),
            AppSpacing.gapH12,
            Expanded(
              child: TextField(
                controller: _wholesalePriceController,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: const InputDecoration(
                  labelText: 'Wholesale Tier (₹)',
                  prefixIcon: Icon(Icons.store_outlined),
                ),
              ),
            ),
          ],
        ),
        AppSpacing.gapV12,
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: _moqController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: 'MOQ Units',
                  prefixIcon: Icon(Icons.layers_outlined),
                ),
              ),
            ),
            AppSpacing.gapH12,
            Expanded(
              child: TextField(
                controller: _stockController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: 'Stock (units)',
                  prefixIcon: Icon(Icons.inventory_2_outlined),
                ),
              ),
            ),
          ],
        ),
        AppSpacing.gapV20,

        // Multi-Language Translations Section
        Text('Multi-Language Craft Descriptions', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
        AppSpacing.gapV8,
        Container(
          decoration: BoxDecoration(
            color: isDark ? AppColors.surfaceDark : Colors.white,
            borderRadius: AppRadius.borderMd,
            border: Border.all(color: isDark ? AppColors.borderDark : AppColors.borderLight),
          ),
          child: Column(
            children: [
              TabBar(
                controller: _translationTabController,
                labelColor: AppColors.primary,
                unselectedLabelColor: Colors.grey,
                indicatorColor: AppColors.primary,
                tabs: const [
                  Tab(text: 'English'),
                  Tab(text: 'हिंदी (Hindi)'),
                  Tab(text: 'తెలుగు (Telugu)'),
                  Tab(text: 'বাংলা (Bengali)'),
                ],
              ),
              Padding(
                padding: AppSpacing.paddingAllBase,
                child: SizedBox(
                  height: 80,
                  child: TabBarView(
                    controller: _translationTabController,
                    children: [
                      Text(data.englishTranslation, style: const TextStyle(fontSize: 12)),
                      Text(data.hindiTranslation, style: const TextStyle(fontSize: 12)),
                      Text(data.teluguTranslation, style: const TextStyle(fontSize: 12)),
                      Text(data.bengaliTranslation, style: const TextStyle(fontSize: 12)),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
        AppSpacing.gapV20,

        // Marketing & Social Content Generator
        Text('AI Marketing & Social Copy', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
        AppSpacing.gapV8,
        AppCard(
          padding: AppSpacing.paddingAllBase,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('Instagram / WhatsApp Broadcast Post', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                  IconButton(
                    icon: const Icon(Icons.copy, size: 16),
                    tooltip: 'Copy caption',
                    onPressed: () async {
                      await Clipboard.setData(ClipboardData(text: data.marketingCopySocial));
                      _showSnack('Marketing caption copied.');
                    },
                  ),
                ],
              ),
              Text(
                data.marketingCopySocial,
                style: const TextStyle(fontSize: 12, height: 1.35),
              ),
            ],
          ),
        ),
        AppSpacing.gapV24,

        // Publish Actions
        if (sellerId == null)
          Container(
            padding: AppSpacing.paddingAllBase,
            decoration: BoxDecoration(
              color: AppColors.warningContainer,
              borderRadius: AppRadius.borderMd,
              border: Border.all(color: AppColors.warning.withValues(alpha: 0.4)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Complete your artisan storefront first',
                  style: TextStyle(fontWeight: FontWeight.bold, color: AppColors.warning),
                ),
                AppSpacing.gapV6,
                const Text(
                  'Listings are published under your storefront. Set it up once, then come back to publish this draft.',
                  style: TextStyle(fontSize: 12, color: AppColors.textPrimaryLight),
                ),
                AppSpacing.gapV12,
                AppButton(
                  label: 'Set up storefront',
                  icon: Icons.arrow_forward_rounded,
                  height: 40,
                  isFullWidth: false,
                  onPressed: () => context.push('/artisan-onboarding'),
                ),
              ],
            ),
          )
        else
          Row(
            children: [
              Expanded(
                child: AppButton(
                  label: 'Save as Draft',
                  variant: AppButtonVariant.outline,
                  isLoading: _isSaving && _savingAs == ProductStatus.draft,
                  onPressed: _isSaving ? null : () => _saveProduct(ProductStatus.draft),
                ),
              ),
              AppSpacing.gapH12,
              Expanded(
                child: AppButton(
                  label: 'Publish to Store',
                  icon: Icons.check_circle_outline,
                  isLoading: _isSaving && _savingAs == ProductStatus.published,
                  onPressed: _isSaving ? null : () => _saveProduct(ProductStatus.published),
                ),
              ),
            ],
          ),
        AppSpacing.gapV32,
      ],
    );
  }

  /// Maps the free-text category produced by the simulation onto one of the
  /// app's craft categories so the listing shows up under buyer filters.
  String _resolveCategory(String raw) {
    final options = AppConstants.craftCategories.skip(1).toList();
    final trimmed = raw.trim();
    if (options.contains(trimmed)) return trimmed;
    final lower = trimmed.toLowerCase();
    for (final option in options) {
      final optionLower = option.toLowerCase();
      if (optionLower.contains(lower) || lower.contains(optionLower.split(' ').first)) {
        return option;
      }
    }
    return trimmed.isEmpty ? options.first : trimmed;
  }

  Future<void> _saveProduct(ProductStatus status) async {
    final user = ref.read(currentUserProvider);
    final sellerId = user?.sellerId;
    if (sellerId == null) {
      _showSnack('Complete your artisan storefront first', isError: true);
      return;
    }

    final title = _titleController.text.trim();
    final description = _descController.text.trim();
    final material = _materialsController.text.trim();
    final retail = double.tryParse(_retailPriceController.text.trim());
    final wholesale = double.tryParse(_wholesalePriceController.text.trim());
    final moq = int.tryParse(_moqController.text.trim());
    final stock = int.tryParse(_stockController.text.trim()) ?? 10;

    if (title.isEmpty) {
      _showSnack('Add a product title before saving', isError: true);
      return;
    }
    if (retail == null || retail <= 0) {
      _showSnack('Enter a valid retail price', isError: true);
      return;
    }
    if (stock < 0) {
      _showSnack('Stock cannot be negative', isError: true);
      return;
    }

    final tiers = <WholesaleTier>[
      if (wholesale != null && wholesale > 0 && moq != null && moq > 0)
        WholesaleTier(minQuantity: moq, pricePerUnit: wholesale),
    ];

    final input = ProductInput(
      title: title,
      description: description,
      category: _resolveCategory(_categoryController.text),
      material: material,
      price: retail,
      stock: stock,
      status: status,
      city: user?.city,
      state: user?.state,
      wholesaleTiers: tiers,
    );

    setState(() {
      _isSaving = true;
      _savingAs = status;
    });
    try {
      await ref.read(supabaseProductsRepositoryProvider).createProduct(sellerId: sellerId, input: input);
      ref.read(catalogStudioProvider.notifier).resetStudio();
      _clearControllers();
      ref.invalidate(sellerProductsProvider);
      if (!mounted) return;
      _showSnack(
        status == ProductStatus.published
            ? 'Handicraft published to your KalaCart store.'
            : 'Product saved as a draft in your catalog.',
      );
      context.pop();
    } catch (e) {
      _showSnack(authErrorMessage(e), isError: true);
    } finally {
      if (mounted) {
        setState(() {
          _isSaving = false;
          _savingAs = null;
        });
      }
    }
  }
}
