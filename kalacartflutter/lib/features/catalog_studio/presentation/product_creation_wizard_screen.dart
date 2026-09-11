import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/utils/currency_formatter.dart';
import '../../../core/widgets/app_card.dart';
import '../../../shared/models/buyer_models.dart';
import '../../../shared/models/seller_models.dart';
import '../../seller/data/seller_repository.dart';

class ProductCreationWizardScreen extends ConsumerStatefulWidget {
  const ProductCreationWizardScreen({super.key});

  @override
  ConsumerState<ProductCreationWizardScreen> createState() => _ProductCreationWizardScreenState();
}

class _ProductCreationWizardScreenState extends ConsumerState<ProductCreationWizardScreen> {
  int _currentStep = 0;

  final TextEditingController _titleController = TextEditingController();
  final TextEditingController _categoryController = TextEditingController(text: 'Pottery & Terracotta');
  final TextEditingController _clusterController = TextEditingController(text: 'Jaipur Blue Pottery Cluster, Rajasthan');
  final TextEditingController _materialsController = TextEditingController(text: 'Quartz stone powder, multani mitti, natural cobalt oxide glaze');
  final TextEditingController _dimensionsController = TextEditingController(text: '12" H x 6" W');
  final TextEditingController _weightController = TextEditingController(text: '1.2 kg');
  final TextEditingController _retailPriceController = TextEditingController(text: '2200');
  final TextEditingController _wholesalePriceController = TextEditingController(text: '1500');
  final TextEditingController _moqController = TextEditingController(text: '10');
  final TextEditingController _descController = TextEditingController(text: 'Authentic GI-Certified handmade craft made using centuries-old heritage methods.');
  final TextEditingController _hindiDescController = TextEditingController(text: 'प्राकृतिक रंगों और पारंपरिक हस्तकला से निर्मित जयपुर ब्लू पॉटरी।');
  final TextEditingController _teluguDescController = TextEditingController(text: 'సహజ రంగులతో రూపొందించబడిన చేతివృత్తుల కళాఖండం.');

  int _photoCount = 3;

  @override
  void dispose() {
    _titleController.dispose();
    _categoryController.dispose();
    _clusterController.dispose();
    _materialsController.dispose();
    _dimensionsController.dispose();
    _weightController.dispose();
    _retailPriceController.dispose();
    _wholesalePriceController.dispose();
    _moqController.dispose();
    _descController.dispose();
    _hindiDescController.dispose();
    _teluguDescController.dispose();
    super.dispose();
  }

  void _autofillWithSample() {
    setState(() {
      _titleController.text = 'Traditional Mughal Floral Blue Pottery Planter';
      _categoryController.text = 'Pottery & Terracotta';
      _clusterController.text = 'Jaipur Blue Pottery Cluster, Rajasthan (GI Reg #04)';
      _materialsController.text = 'Makrana Quartz, Fuller Earth, Glass Frit, Copper & Cobalt Glaze';
      _dimensionsController.text = '10" Diameter x 8" Height';
      _weightController.text = '1.8 kg';
      _retailPriceController.text = '1850';
      _wholesalePriceController.text = '1250';
      _moqController.text = '8';
      _descController.text = 'Hand-formed clay-free quartz planter with heat-resistant mineral glazes and Mughal petal motifs.';
      _hindiDescController.text = 'पारंपरिक मुग़ल फ्लोरल जयपुर ब्लू पॉटरी प्लांटर - प्राकृतिक खनिजों से निर्मित।';
      _teluguDescController.text = 'సాంప్రదాయ మొఘల్ బ్లూ పాటర్ ప్లాంటర్ - స్వచ్ఛమైన సహజ రంగులు.';
      _photoCount = 4;
    });

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('✨ Auto-filled wizard fields with Kala-AI Craft Data!')),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Add New Craft Product'),
        actions: [
          TextButton.icon(
            style: TextButton.styleFrom(foregroundColor: const Color(0xFF6A1B9A)),
            icon: const Icon(Icons.auto_awesome, size: 16),
            label: const Text('AI Auto-Fill', style: TextStyle(fontWeight: FontWeight.bold)),
            onPressed: _autofillWithSample,
          ),
        ],
      ),
      body: Stepper(
        type: StepperType.vertical,
        currentStep: _currentStep,
        onStepTapped: (step) => setState(() => _currentStep = step),
        onStepContinue: () {
          if (_currentStep < 9) {
            setState(() => _currentStep += 1);
          } else {
            _publishProduct();
          }
        },
        onStepCancel: () {
          if (_currentStep > 0) {
            setState(() => _currentStep -= 1);
          }
        },
        controlsBuilder: (context, details) {
          final isLastStep = _currentStep == 9;
          return Padding(
            padding: const EdgeInsets.only(top: 16),
            child: Row(
              children: [
                Expanded(
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: isLastStep ? AppColors.primary : AppColors.secondary,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      shape: AppRadius.shapeMd,
                    ),
                    onPressed: details.onStepContinue,
                    child: Text(
                      isLastStep ? 'Publish Craft Product' : 'Next Step (${_currentStep + 1}/10)',
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                  ),
                ),
                if (_currentStep > 0) ...[
                  AppSpacing.gapH12,
                  OutlinedButton(
                    onPressed: details.onStepCancel,
                    child: const Text('Back'),
                  ),
                ],
              ],
            ),
          );
        },
        steps: [
          // Step 1: Photos
          Step(
            title: const Text('1. Craft Photos'),
            subtitle: Text('$_photoCount photos selected'),
            isActive: _currentStep >= 0,
            state: _currentStep > 0 ? StepState.complete : StepState.indexed,
            content: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Upload multi-angle photos showing details, base, and artisan stamps.'),
                AppSpacing.gapV12,
                Row(
                  children: [
                    Container(
                      height: 80,
                      width: 80,
                      decoration: BoxDecoration(
                        color: const Color(0xFF6A1B9A).withValues(alpha: 0.1),
                        borderRadius: AppRadius.borderMd,
                        border: Border.all(color: const Color(0xFF6A1B9A)),
                      ),
                      child: const Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.add_a_photo_outlined, color: Color(0xFF6A1B9A)),
                            Text('Add', style: TextStyle(fontSize: 10, color: Color(0xFF6A1B9A), fontWeight: FontWeight.bold)),
                          ],
                        ),
                      ),
                    ),
                    AppSpacing.gapH12,
                    ...List.generate(
                      _photoCount,
                      (i) => Container(
                        margin: const EdgeInsets.only(right: 8),
                        height: 80,
                        width: 80,
                        decoration: BoxDecoration(
                          color: isDark ? AppColors.surfaceDark : Colors.grey.shade200,
                          borderRadius: AppRadius.borderMd,
                        ),
                        child: Center(
                          child: Text('Photo ${i + 1}', style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),

          // Step 2: Basic Info
          Step(
            title: const Text('2. Basic Information'),
            subtitle: Text(_titleController.text.isNotEmpty ? _titleController.text : 'Title & Craft Category'),
            isActive: _currentStep >= 1,
            state: _currentStep > 1 ? StepState.complete : StepState.indexed,
            content: Column(
              children: [
                TextField(
                  controller: _titleController,
                  decoration: const InputDecoration(labelText: 'Handicraft Title *', hintText: 'e.g. Cobalt Floral Blue Pottery Vase'),
                ),
                AppSpacing.gapV12,
                TextField(
                  controller: _categoryController,
                  decoration: const InputDecoration(labelText: 'Craft Category *'),
                ),
                AppSpacing.gapV12,
                TextField(
                  controller: _clusterController,
                  decoration: const InputDecoration(labelText: 'GI Craft Cluster & State *'),
                ),
              ],
            ),
          ),

          // Step 3: Material
          Step(
            title: const Text('3. Raw Materials & Purity'),
            subtitle: const Text('Natural fibers, minerals, clays'),
            isActive: _currentStep >= 2,
            state: _currentStep > 2 ? StepState.complete : StepState.indexed,
            content: TextField(
              controller: _materialsController,
              maxLines: 2,
              decoration: const InputDecoration(labelText: 'Raw Material Provenance', hintText: 'e.g. 100% Guntur organic handloom cotton'),
            ),
          ),

          // Step 4: Dimensions
          Step(
            title: const Text('4. Dimensions & Weight'),
            isActive: _currentStep >= 3,
            state: _currentStep > 3 ? StepState.complete : StepState.indexed,
            content: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _dimensionsController,
                    decoration: const InputDecoration(labelText: 'Dimensions (L x W x H)'),
                  ),
                ),
                AppSpacing.gapH12,
                Expanded(
                  child: TextField(
                    controller: _weightController,
                    decoration: const InputDecoration(labelText: 'Weight'),
                  ),
                ),
              ],
            ),
          ),

          // Step 5: Retail Pricing
          Step(
            title: const Text('5. Retail Pricing'),
            subtitle: Text('₹${_retailPriceController.text}'),
            isActive: _currentStep >= 4,
            state: _currentStep > 4 ? StepState.complete : StepState.indexed,
            content: TextField(
              controller: _retailPriceController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'Direct Retail Price (₹)', prefixIcon: Icon(Icons.currency_rupee)),
            ),
          ),

          // Step 6: Wholesale Pricing
          Step(
            title: const Text('6. Wholesale B2B Tier'),
            subtitle: Text('₹${_wholesalePriceController.text} for ${_moqController.text}+ units'),
            isActive: _currentStep >= 5,
            state: _currentStep > 5 ? StepState.complete : StepState.indexed,
            content: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _wholesalePriceController,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(labelText: 'Wholesale Price (₹)'),
                  ),
                ),
                AppSpacing.gapH12,
                Expanded(
                  child: TextField(
                    controller: _moqController,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(labelText: 'Min Order Qty (MOQ)'),
                  ),
                ),
              ],
            ),
          ),

          // Step 7: Description
          Step(
            title: const Text('7. Heritage Description'),
            isActive: _currentStep >= 6,
            state: _currentStep > 6 ? StepState.complete : StepState.indexed,
            content: TextField(
              controller: _descController,
              maxLines: 3,
              decoration: const InputDecoration(labelText: 'Artisan Narrative & Techniques'),
            ),
          ),

          // Step 8: Translation
          Step(
            title: const Text('8. Regional Indian Translations'),
            isActive: _currentStep >= 7,
            state: _currentStep > 7 ? StepState.complete : StepState.indexed,
            content: Column(
              children: [
                TextField(
                  controller: _hindiDescController,
                  maxLines: 2,
                  decoration: const InputDecoration(labelText: 'हिंदी अनुवाद (Hindi)'),
                ),
                AppSpacing.gapV12,
                TextField(
                  controller: _teluguDescController,
                  maxLines: 2,
                  decoration: const InputDecoration(labelText: 'తెలుగు అనువాదం (Telugu)'),
                ),
              ],
            ),
          ),

          // Step 9: Digital Craft Passport Preview
          Step(
            title: const Text('9. Digital Craft Passport'),
            isActive: _currentStep >= 8,
            state: _currentStep > 8 ? StepState.complete : StepState.indexed,
            content: Container(
              padding: AppSpacing.paddingAllBase,
              decoration: BoxDecoration(
                color: AppColors.primaryContainer.withValues(alpha: 0.3),
                borderRadius: AppRadius.borderMd,
              ),
              child: const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.verified, color: AppColors.primary, size: 20),
                      SizedBox(width: 6),
                      Text('GI Certified Digital Provenance Tag', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                    ],
                  ),
                  SizedBox(height: 6),
                  Text('Passport ID: GI-IN-2026-WZ-8841\nCluster: Kot Jewar, Jaipur, Rajasthan\nArtisan Stamp: Master Guild Verified', style: TextStyle(fontSize: 11, height: 1.4)),
                ],
              ),
            ),
          ),

          // Step 10: Final Preview & Publish
          Step(
            title: const Text('10. Final Preview & Confirmation'),
            isActive: _currentStep >= 9,
            state: StepState.indexed,
            content: AppCard(
              padding: AppSpacing.paddingAllBase,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    _titleController.text.isNotEmpty ? _titleController.text : 'Craft Title',
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                  AppSpacing.gapV4,
                  Text('Category: ${_categoryController.text}'),
                  AppSpacing.gapV8,
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text('Retail: ${CurrencyFormatter.formatINR(double.tryParse(_retailPriceController.text) ?? 2200)}', style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary)),
                      Text('Wholesale: ${CurrencyFormatter.formatINR(double.tryParse(_wholesalePriceController.text) ?? 1500)} (MOQ: ${_moqController.text})', style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.secondary)),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _publishProduct() {
    final newProduct = SellerProduct(
      id: 'sp-${DateTime.now().millisecondsSinceEpoch}',
      title: _titleController.text.isNotEmpty ? _titleController.text : 'Handcrafted Heritage Artisan Piece',
      category: _categoryController.text,
      retailPrice: double.tryParse(_retailPriceController.text) ?? 2200,
      wholesaleTiers: [
        WholesaleTier(
          minQuantity: int.tryParse(_moqController.text) ?? 10,
          pricePerUnit: double.tryParse(_wholesalePriceController.text) ?? 1500,
        ),
      ],
      stockQuantity: 12,
      status: ProductStatus.published,
      material: _materialsController.text,
      dimensions: _dimensionsController.text,
      weight: _weightController.text,
      description: _descController.text,
      translations: {
        'hi': _hindiDescController.text,
        'te': _teluguDescController.text,
      },
      isGiTagged: true,
      passportId: 'GI-IN-2026-WZ-${DateTime.now().millisecond}',
      createdAt: DateTime.now(),
    );

    ref.read(sellerProductsProvider.notifier).addProduct(newProduct);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('🎉 Craft product successfully created and published!'),
        behavior: SnackBarBehavior.floating,
      ),
    );
    context.pop();
  }
}
