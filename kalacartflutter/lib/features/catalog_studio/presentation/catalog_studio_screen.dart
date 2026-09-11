import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/widgets/app_card.dart';
import '../../../shared/models/buyer_models.dart';
import '../../../shared/models/seller_models.dart';
import '../../seller/data/seller_repository.dart';
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

  @override
  void initState() {
    super.initState();
    _translationTabController = TabController(length: 4, vsync: this);
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
    super.dispose();
  }

  void _populateControllers(AiGeneratedCraftData data) {
    if (_titleController.text.isEmpty) {
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
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(catalogStudioProvider);
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    if (state.generatedData != null) {
      _populateControllers(state.generatedData!);
    }

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
                  'Mock AI Vision & Multi-lingual Cataloger',
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
              onPressed: () {
                _titleController.clear();
                ref.read(catalogStudioProvider.notifier).resetStudio();
              },
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
                onPressed: () => ref.read(catalogStudioProvider.notifier).resetStudio(),
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

    return ListView(
      padding: AppSpacing.paddingAllBase,
      children: [
        // GI Cluster Authenticity Banner
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
                      'GI TAG MATCH DETECTED (${(data.authenticityConfidence * 100).toInt()}%)',
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
                keyboardType: TextInputType.number,
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
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: 'Wholesale Tier (₹)',
                  prefixIcon: Icon(Icons.store_outlined),
                ),
              ),
            ),
            AppSpacing.gapH12,
            Expanded(
              child: TextField(
                controller: _moqController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: 'MOQ Units',
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
                    onPressed: () {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Marketing caption copied!')),
                      );
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
        Row(
          children: [
            Expanded(
              child: OutlinedButton(
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: AppRadius.shapeMd,
                ),
                onPressed: () => _saveAsDraft(context, data),
                child: const Text('Save as Draft'),
              ),
            ),
            AppSpacing.gapH12,
            Expanded(
              child: ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: AppRadius.shapeMd,
                ),
                icon: const Icon(Icons.check_circle_outline, size: 18),
                label: const Text('Publish to Store', style: TextStyle(fontWeight: FontWeight.bold)),
                onPressed: () => _publishProduct(context, data),
              ),
            ),
          ],
        ),
        AppSpacing.gapV32,
      ],
    );
  }

  void _saveAsDraft(BuildContext context, AiGeneratedCraftData data) {
    final newProduct = SellerProduct(
      id: 'sp-${DateTime.now().millisecondsSinceEpoch}',
      title: _titleController.text.isNotEmpty ? _titleController.text : data.title,
      category: _categoryController.text.isNotEmpty ? _categoryController.text : data.category,
      retailPrice: double.tryParse(_retailPriceController.text) ?? data.retailPrice,
      wholesaleTiers: [
        WholesaleTier(
          minQuantity: int.tryParse(_moqController.text) ?? data.suggestedMoq,
          pricePerUnit: double.tryParse(_wholesalePriceController.text) ?? data.wholesalePrice,
        ),
      ],
      stockQuantity: 10,
      status: ProductStatus.draft,
      material: _materialsController.text.isNotEmpty ? _materialsController.text : data.materials,
      dimensions: _dimensionsController.text.isNotEmpty ? _dimensionsController.text : data.dimensions,
      weight: _weightController.text.isNotEmpty ? _weightController.text : data.weight,
      description: _descController.text.isNotEmpty ? _descController.text : data.description,
      isGiTagged: true,
      passportId: 'GI-IN-2026-DRAFT-${DateTime.now().millisecond}',
      createdAt: DateTime.now(),
    );

    ref.read(sellerProductsProvider.notifier).addProduct(newProduct);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Product saved as Draft in Artisan Catalog Studio!')),
    );
    context.pop();
  }

  void _publishProduct(BuildContext context, AiGeneratedCraftData data) {
    final newProduct = SellerProduct(
      id: 'sp-${DateTime.now().millisecondsSinceEpoch}',
      title: _titleController.text.isNotEmpty ? _titleController.text : data.title,
      category: _categoryController.text.isNotEmpty ? _categoryController.text : data.category,
      retailPrice: double.tryParse(_retailPriceController.text) ?? data.retailPrice,
      wholesaleTiers: [
        WholesaleTier(
          minQuantity: int.tryParse(_moqController.text) ?? data.suggestedMoq,
          pricePerUnit: double.tryParse(_wholesalePriceController.text) ?? data.wholesalePrice,
        ),
      ],
      stockQuantity: 15,
      status: ProductStatus.published,
      material: _materialsController.text.isNotEmpty ? _materialsController.text : data.materials,
      dimensions: _dimensionsController.text.isNotEmpty ? _dimensionsController.text : data.dimensions,
      weight: _weightController.text.isNotEmpty ? _weightController.text : data.weight,
      description: _descController.text.isNotEmpty ? _descController.text : data.description,
      isGiTagged: true,
      passportId: 'GI-IN-2026-PUB-${DateTime.now().millisecond}',
      createdAt: DateTime.now(),
    );

    ref.read(sellerProductsProvider.notifier).addProduct(newProduct);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('🎉 Handicraft successfully published to KalaCart Live Marketplace!'),
        behavior: SnackBarBehavior.floating,
      ),
    );
    context.pop();
  }
}
