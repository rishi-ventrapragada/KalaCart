import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import 'package:intl/intl.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;

import '../../../core/constants/app_spacing.dart';
import '../../../core/network/api_client.dart';
import '../../../core/widgets/app_button.dart';
import '../../../core/widgets/app_card.dart';
import '../data/backend_ai_repository.dart';
import '../domain/backend_ai_models.dart';

/// One screen exercising the three live AI features end to end.
///
/// Each section calls the deployed FastAPI backend and renders the real
/// response, so what appears here is server output rather than mock data.
class AiStudioScreen extends ConsumerStatefulWidget {
  const AiStudioScreen({super.key});

  @override
  ConsumerState<AiStudioScreen> createState() => _AiStudioScreenState();
}

class _AiStudioScreenState extends ConsumerState<AiStudioScreen> {
  // ── Image enhancement ────────────────────────────────────────────────
  File? _pickedImage;
  EnhancedImageResult? _enhanced;
  bool _enhancing = false;

  // ── Pricing ──────────────────────────────────────────────────────────
  final _descriptionController = TextEditingController(
    text: 'Hand-thrown Jaipur blue pottery vase, 14 inches tall, cobalt floral motifs, natural dyes',
  );
  final _materialCostController = TextEditingController(text: '400');
  final _labourHoursController = TextEditingController(text: '6');
  String _category = 'Pottery';
  String _size = 'Medium';
  String _quality = 'Premium';
  int _complexity = 4;
  PricingBreakdown? _pricing;
  bool _pricingLoading = false;

  // ── Voice → catalog ──────────────────────────────────────────────────
  final stt.SpeechToText _speech = stt.SpeechToText();
  final _transcriptController = TextEditingController();
  bool _listening = false;
  String _voiceLanguage = 'hi';
  GeneratedCatalog? _catalog;
  bool _catalogLoading = false;

  final _currency = NumberFormat.currency(locale: 'en_IN', symbol: '₹', decimalDigits: 0);

  @override
  void dispose() {
    _descriptionController.dispose();
    _materialCostController.dispose();
    _labourHoursController.dispose();
    _transcriptController.dispose();
    super.dispose();
  }

  void _showError(Object error) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(apiErrorMessage(error))),
    );
  }

  // ── Feature 1: image enhancement ─────────────────────────────────────

  Future<void> _pickImage(ImageSource source) async {
    try {
      // The backend rejects anything over 10 MB with a 413, and a modern phone
      // camera clears that easily, so downscale and re-encode before upload.
      // 2000 px also stays inside its 100-6000 px dimension check.
      final picked = await ImagePicker().pickImage(
        source: source,
        maxWidth: 2000,
        maxHeight: 2000,
        imageQuality: 85,
      );
      if (picked == null) return;
      setState(() {
        _pickedImage = File(picked.path);
        _enhanced = null;
      });
    } catch (e) {
      _showError(e);
    }
  }

  Future<void> _enhanceImage() async {
    final file = _pickedImage;
    if (file == null) return;
    setState(() => _enhancing = true);
    try {
      final result = await ref
          .read(backendAiRepositoryProvider)
          .enhanceImage(imagePath: file.path);
      if (mounted) setState(() => _enhanced = result);
    } catch (e) {
      _showError(e);
    } finally {
      if (mounted) setState(() => _enhancing = false);
    }
  }

  // ── Feature 2: pricing ───────────────────────────────────────────────

  Future<void> _analyzePricing() async {
    setState(() => _pricingLoading = true);
    try {
      final result = await ref.read(backendAiRepositoryProvider).analyzePricing(
            description: _descriptionController.text.trim(),
            category: _category,
            size: _size,
            quality: _quality,
            complexity: _complexity,
            materialCost: double.tryParse(_materialCostController.text.trim()),
            labourHours: double.tryParse(_labourHoursController.text.trim()),
          );
      if (mounted) setState(() => _pricing = result);
    } catch (e) {
      _showError(e);
    } finally {
      if (mounted) setState(() => _pricingLoading = false);
    }
  }

  // ── Feature 3: voice → catalog ───────────────────────────────────────

  Future<void> _toggleListening() async {
    if (_listening) {
      await _speech.stop();
      if (mounted) setState(() => _listening = false);
      return;
    }
    try {
      final available = await _speech.initialize(
        onStatus: (status) {
          if (status == 'done' || status == 'notListening') {
            if (mounted) setState(() => _listening = false);
          }
        },
        onError: (error) {
          if (mounted) setState(() => _listening = false);
        },
      );
      if (!available) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Speech recognition is not available on this device.'),
          ),
        );
        return;
      }
      setState(() => _listening = true);
      await _speech.listen(
        listenOptions: stt.SpeechListenOptions(
          localeId: _localeFor(_voiceLanguage),
        ),
        onResult: (result) {
          setState(() => _transcriptController.text = result.recognizedWords);
        },
      );
    } catch (e) {
      if (mounted) setState(() => _listening = false);
      _showError(e);
    }
  }

  /// Maps the backend's language codes onto device locale ids.
  String _localeFor(String code) => switch (code) {
        'hi' => 'hi_IN',
        'te' => 'te_IN',
        'ta' => 'ta_IN',
        'kn' => 'kn_IN',
        _ => 'en_IN',
      };

  Future<void> _generateCatalog() async {
    final transcript = _transcriptController.text.trim();
    if (transcript.length < 5) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please speak or type at least 5 characters.')),
      );
      return;
    }
    setState(() => _catalogLoading = true);
    try {
      final result = await ref.read(backendAiRepositoryProvider).generateCatalog(
            transcript: transcript,
            language: _voiceLanguage,
          );
      if (mounted) setState(() => _catalog = result);
    } catch (e) {
      _showError(e);
    } finally {
      if (mounted) setState(() => _catalogLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final waking = ref.watch(backendWakingProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('AI Studio')),
      body: Column(
        children: [
          if (waking)
            Container(
              width: double.infinity,
              color: theme.colorScheme.secondaryContainer,
              padding: AppSpacing.paddingAllMd,
              child: Row(
                children: [
                  const SizedBox(
                    height: 16,
                    width: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                  AppSpacing.gapH12,
                  Expanded(
                    child: Text(
                      'Waking the server — the first request can take up to a minute.',
                      style: theme.textTheme.bodySmall,
                    ),
                  ),
                ],
              ),
            ),
          Expanded(
            child: ListView(
              padding: AppSpacing.paddingAllBase,
              children: [
                _buildImageSection(theme),
                AppSpacing.gapV16,
                _buildPricingSection(theme),
                AppSpacing.gapV16,
                _buildVoiceSection(theme),
                AppSpacing.gapV24,
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _sectionTitle(ThemeData theme, int number, String title, String subtitle) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            CircleAvatar(
              radius: 14,
              backgroundColor: theme.colorScheme.primary,
              child: Text(
                '$number',
                style: theme.textTheme.labelMedium?.copyWith(
                  color: theme.colorScheme.onPrimary,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            AppSpacing.gapH12,
            Expanded(
              child: Text(title, style: theme.textTheme.titleMedium),
            ),
          ],
        ),
        AppSpacing.gapV4,
        Text(subtitle, style: theme.textTheme.bodySmall),
      ],
    );
  }

  // ── Section 1 ────────────────────────────────────────────────────────

  Widget _buildImageSection(ThemeData theme) {
    final enhanced = _enhanced;
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _sectionTitle(theme, 1, 'Photo enhancement',
              'Background removal, lighting and framing — runs on the server with OpenCV.'),
          AppSpacing.gapV12,
          Row(
            children: [
              Expanded(
                child: AppButton(
                  label: 'Camera',
                  icon: Icons.photo_camera,
                  variant: AppButtonVariant.outline,
                  onPressed: () => _pickImage(ImageSource.camera),
                ),
              ),
              AppSpacing.gapH12,
              Expanded(
                child: AppButton(
                  label: 'Gallery',
                  icon: Icons.photo_library,
                  variant: AppButtonVariant.outline,
                  onPressed: () => _pickImage(ImageSource.gallery),
                ),
              ),
            ],
          ),
          if (_pickedImage != null) ...[
            AppSpacing.gapV12,
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Column(
                    children: [
                      Text('Original', style: theme.textTheme.labelMedium),
                      AppSpacing.gapV4,
                      ClipRRect(
                        borderRadius: BorderRadius.circular(8),
                        child: Image.file(_pickedImage!, height: 140, fit: BoxFit.cover),
                      ),
                    ],
                  ),
                ),
                AppSpacing.gapH12,
                Expanded(
                  child: Column(
                    children: [
                      Text('Enhanced', style: theme.textTheme.labelMedium),
                      AppSpacing.gapV4,
                      if (enhanced?.enhancedUrl != null)
                        ClipRRect(
                          borderRadius: BorderRadius.circular(8),
                          child: Image.network(
                            enhanced!.enhancedUrl!,
                            height: 140,
                            fit: BoxFit.cover,
                            errorBuilder: (_, __, ___) => const SizedBox(
                              height: 140,
                              child: Center(child: Icon(Icons.broken_image)),
                            ),
                          ),
                        )
                      else
                        Container(
                          height: 140,
                          decoration: BoxDecoration(
                            color: theme.colorScheme.surfaceContainerHighest,
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: const Center(child: Icon(Icons.auto_awesome)),
                        ),
                    ],
                  ),
                ),
              ],
            ),
            AppSpacing.gapV12,
            AppButton(
              label: 'Enhance photo',
              icon: Icons.auto_fix_high,
              isLoading: _enhancing,
              onPressed: _enhancing ? null : _enhanceImage,
            ),
          ],
          if (enhanced != null) ...[
            AppSpacing.gapV12,
            _factRow(theme, 'Output', '${enhanced.width} × ${enhanced.height} (${enhanced.ratio})'),
            _factRow(theme, 'Background removed', enhanced.backgroundRemoved ? 'Yes' : 'No'),
            _factRow(theme, 'Saved to storage', enhanced.storageUploaded ? 'Yes' : 'Returned inline'),
          ],
        ],
      ),
    );
  }

  // ── Section 2 ────────────────────────────────────────────────────────

  Widget _buildPricingSection(ThemeData theme) {
    final pricing = _pricing;
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _sectionTitle(theme, 2, 'Fair price',
              'Computed from materials, labour, market band and the festival calendar.'),
          AppSpacing.gapV12,
          TextField(
            controller: _descriptionController,
            maxLines: 2,
            decoration: const InputDecoration(
              labelText: 'Describe the piece',
              border: OutlineInputBorder(),
            ),
          ),
          AppSpacing.gapV12,
          Row(
            children: [
              Expanded(
                child: DropdownButtonFormField<String>(
                  initialValue: _category,
                  decoration: const InputDecoration(labelText: 'Category', border: OutlineInputBorder()),
                  items: const ['Pottery', 'Textiles', 'Jewellery', 'Woodwork', 'Painting', 'Other']
                      .map((c) => DropdownMenuItem(value: c, child: Text(c)))
                      .toList(),
                  onChanged: (v) => setState(() => _category = v ?? 'Pottery'),
                ),
              ),
              AppSpacing.gapH12,
              Expanded(
                child: DropdownButtonFormField<String>(
                  initialValue: _size,
                  decoration: const InputDecoration(labelText: 'Size', border: OutlineInputBorder()),
                  items: const ['Small', 'Medium', 'Large']
                      .map((c) => DropdownMenuItem(value: c, child: Text(c)))
                      .toList(),
                  onChanged: (v) => setState(() => _size = v ?? 'Medium'),
                ),
              ),
            ],
          ),
          AppSpacing.gapV12,
          Row(
            children: [
              Expanded(
                child: DropdownButtonFormField<String>(
                  initialValue: _quality,
                  decoration: const InputDecoration(labelText: 'Quality', border: OutlineInputBorder()),
                  items: const ['Basic', 'Standard', 'Premium']
                      .map((c) => DropdownMenuItem(value: c, child: Text(c)))
                      .toList(),
                  onChanged: (v) => setState(() => _quality = v ?? 'Premium'),
                ),
              ),
              AppSpacing.gapH12,
              Expanded(
                child: DropdownButtonFormField<int>(
                  initialValue: _complexity,
                  decoration: const InputDecoration(labelText: 'Complexity', border: OutlineInputBorder()),
                  items: const [1, 2, 3, 4, 5]
                      .map((c) => DropdownMenuItem(value: c, child: Text('$c / 5')))
                      .toList(),
                  onChanged: (v) => setState(() => _complexity = v ?? 4),
                ),
              ),
            ],
          ),
          AppSpacing.gapV12,
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _materialCostController,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'Material cost (₹)',
                    border: OutlineInputBorder(),
                  ),
                ),
              ),
              AppSpacing.gapH12,
              Expanded(
                child: TextField(
                  controller: _labourHoursController,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'Labour hours',
                    border: OutlineInputBorder(),
                  ),
                ),
              ),
            ],
          ),
          AppSpacing.gapV12,
          AppButton(
            label: 'Suggest a fair price',
            icon: Icons.calculate,
            isLoading: _pricingLoading,
            onPressed: _pricingLoading ? null : _analyzePricing,
          ),
          if (pricing != null) ...[
            AppSpacing.gapV16,
            Center(
              child: Column(
                children: [
                  Text('Suggested price', style: theme.textTheme.labelMedium),
                  Text(
                    _currency.format(pricing.suggestedPrice),
                    style: theme.textTheme.headlineMedium?.copyWith(
                      color: theme.colorScheme.primary,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  Text(
                    '${_currency.format(pricing.minimumPrice)} – ${_currency.format(pricing.maximumPrice)}'
                    '   ·   ${pricing.confidence}% confidence',
                    style: theme.textTheme.bodySmall,
                  ),
                ],
              ),
            ),
            AppSpacing.gapV12,
            _factRow(theme, 'Materials', _currency.format(pricing.materials)),
            _factRow(theme, 'Labour', _currency.format(pricing.labour)),
            _factRow(theme, 'Overhead', _currency.format(pricing.overhead)),
            _factRow(theme, 'Profit', _currency.format(pricing.profit)),
            if (pricing.factors.isNotEmpty) ...[
              AppSpacing.gapV12,
              Text('Why this price', style: theme.textTheme.titleSmall),
              AppSpacing.gapV4,
              ...pricing.factors.map(
                (f) => Padding(
                  padding: const EdgeInsets.only(bottom: 4),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('•  '),
                      Expanded(child: Text(f, style: theme.textTheme.bodySmall)),
                    ],
                  ),
                ),
              ),
            ],
          ],
        ],
      ),
    );
  }

  // ── Section 3 ────────────────────────────────────────────────────────

  Widget _buildVoiceSection(ThemeData theme) {
    final catalog = _catalog;
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _sectionTitle(theme, 3, 'Voice to listing',
              'Speech is transcribed on this phone; only the text is sent for the listing.'),
          AppSpacing.gapV12,
          Row(
            children: [
              Expanded(
                child: DropdownButtonFormField<String>(
                  initialValue: _voiceLanguage,
                  decoration: const InputDecoration(labelText: 'Language', border: OutlineInputBorder()),
                  items: const [
                    DropdownMenuItem(value: 'hi', child: Text('Hindi')),
                    DropdownMenuItem(value: 'en', child: Text('English')),
                    DropdownMenuItem(value: 'te', child: Text('Telugu')),
                    DropdownMenuItem(value: 'ta', child: Text('Tamil')),
                    DropdownMenuItem(value: 'kn', child: Text('Kannada')),
                  ],
                  onChanged: (v) => setState(() => _voiceLanguage = v ?? 'hi'),
                ),
              ),
              AppSpacing.gapH12,
              IconButton.filled(
                tooltip: _listening ? 'Stop' : 'Speak',
                iconSize: 28,
                icon: Icon(_listening ? Icons.stop : Icons.mic),
                onPressed: _toggleListening,
              ),
            ],
          ),
          AppSpacing.gapV12,
          TextField(
            controller: _transcriptController,
            maxLines: 3,
            decoration: InputDecoration(
              labelText: 'Transcript',
              helperText: _listening ? 'Listening…' : 'Speak, or type a description',
              border: const OutlineInputBorder(),
            ),
          ),
          AppSpacing.gapV12,
          AppButton(
            label: 'Generate listing',
            icon: Icons.auto_awesome,
            isLoading: _catalogLoading,
            onPressed: _catalogLoading ? null : _generateCatalog,
          ),
          if (catalog != null) ...[
            AppSpacing.gapV16,
            Text(catalog.title, style: theme.textTheme.titleMedium),
            AppSpacing.gapV8,
            Text(catalog.descriptionEn, style: theme.textTheme.bodySmall),
            AppSpacing.gapV8,
            Text(catalog.descriptionHi, style: theme.textTheme.bodySmall),
            AppSpacing.gapV12,
            _factRow(theme, 'Category', catalog.category),
            if (catalog.materials.isNotEmpty)
              _factRow(theme, 'Materials', catalog.materials.join(', ')),
            if (catalog.care.isNotEmpty) _factRow(theme, 'Care', catalog.care),
            if (catalog.seoTags.isNotEmpty) ...[
              AppSpacing.gapV8,
              Wrap(
                spacing: 6,
                runSpacing: 6,
                children: catalog.seoTags
                    .map((t) => Chip(
                          label: Text(t, style: theme.textTheme.labelSmall),
                          visualDensity: VisualDensity.compact,
                        ))
                    .toList(),
              ),
            ],
          ],
        ],
      ),
    );
  }

  Widget _factRow(ThemeData theme, String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 130,
            child: Text(label, style: theme.textTheme.bodySmall),
          ),
          Expanded(
            child: Text(
              value,
              style: theme.textTheme.bodySmall?.copyWith(fontWeight: FontWeight.w600),
            ),
          ),
        ],
      ),
    );
  }
}
