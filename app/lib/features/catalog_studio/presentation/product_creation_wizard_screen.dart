import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_constants.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/utils/currency_formatter.dart';
import '../../../core/widgets/app_button.dart';
import '../../../core/widgets/app_card.dart';
import '../../../core/widgets/app_empty_state.dart';
import '../../../core/widgets/app_image_placeholder.dart';
import '../../../shared/models/product.dart';
import '../../auth/data/auth_repository.dart';
import '../../auth/data/supabase_auth_repository.dart';
import '../../products/data/supabase_products_repository.dart';

class ProductCreationWizardScreen extends ConsumerStatefulWidget {
  /// When non-null the wizard edits this product instead of creating a new one.
  final Product? initialProduct;

  const ProductCreationWizardScreen({super.key, this.initialProduct});

  @override
  ConsumerState<ProductCreationWizardScreen> createState() => _ProductCreationWizardScreenState();
}

class _TierControllers {
  final TextEditingController minQty;
  final TextEditingController price;

  _TierControllers({String minQtyText = '', String priceText = ''})
      : minQty = TextEditingController(text: minQtyText),
        price = TextEditingController(text: priceText);

  bool get isEmpty => minQty.text.trim().isEmpty && price.text.trim().isEmpty;

  void dispose() {
    minQty.dispose();
    price.dispose();
  }
}

class _ProductCreationWizardScreenState extends ConsumerState<ProductCreationWizardScreen> {
  static const int _stepBasics = 0;
  static const int _stepStory = 1;
  static const int _stepPricing = 2;
  static const int _stepImages = 3;
  static const int _stepLocation = 4;
  static const int _stepReview = 5;
  static const int _stepCount = 6;
  static const int _maxTiers = 3;

  int _currentStep = _stepBasics;
  bool _isSaving = false;

  final List<GlobalKey<FormState>> _formKeys = List.generate(_stepCount, (_) => GlobalKey<FormState>());

  final _titleController = TextEditingController();
  final _materialController = TextEditingController();
  final _descController = TextEditingController();
  final _priceController = TextEditingController();
  final _stockController = TextEditingController();
  final _imageUrlController = TextEditingController();
  final _cityController = TextEditingController();
  final _stateController = TextEditingController();

  String? _category;
  final List<_TierControllers> _tiers = [];
  final List<String> _imageUrls = [];

  List<String> get _categoryOptions => AppConstants.craftCategories.skip(1).toList();

  bool get _isEditing => widget.initialProduct != null;

  @override
  void initState() {
    super.initState();
    final product = widget.initialProduct;
    final user = ref.read(currentUserProvider);

    if (product != null) {
      _titleController.text = product.title;
      _materialController.text = product.material;
      _descController.text = product.description;
      _priceController.text = product.price == product.price.roundToDouble()
          ? product.price.toStringAsFixed(0)
          : product.price.toString();
      _stockController.text = product.stock.toString();
      _category = _categoryOptions.contains(product.category) ? product.category : null;
      _imageUrls.addAll(product.imageUrls);
      for (final tier in product.sortedTiers.take(_maxTiers)) {
        _tiers.add(_TierControllers(
          minQtyText: tier.minQuantity.toString(),
          priceText: tier.pricePerUnit == tier.pricePerUnit.roundToDouble()
              ? tier.pricePerUnit.toStringAsFixed(0)
              : tier.pricePerUnit.toString(),
        ));
      }
      _cityController.text = product.city ?? user?.city ?? '';
      _stateController.text = product.state ?? user?.state ?? '';
    } else {
      _cityController.text = user?.city ?? '';
      _stateController.text = user?.state ?? '';
    }
  }

  @override
  void dispose() {
    _titleController.dispose();
    _materialController.dispose();
    _descController.dispose();
    _priceController.dispose();
    _stockController.dispose();
    _imageUrlController.dispose();
    _cityController.dispose();
    _stateController.dispose();
    for (final t in _tiers) {
      t.dispose();
    }
    super.dispose();
  }

  // ---------------------------------------------------------------------------
  // Validation & navigation
  // ---------------------------------------------------------------------------

  bool _validateStep(int step) {
    final form = _formKeys[step].currentState;
    if (form == null) return true;
    return form.validate();
  }

  void _goToStep(int step) {
    if (step == _currentStep) return;
    if (step > _currentStep) {
      for (var s = _currentStep; s < step; s++) {
        if (!_validateStep(s)) {
          setState(() => _currentStep = s);
          return;
        }
      }
    }
    setState(() => _currentStep = step);
  }

  void _onContinue() {
    if (!_validateStep(_currentStep)) return;
    if (_currentStep < _stepReview) {
      setState(() => _currentStep += 1);
    }
  }

  void _onBack() {
    if (_currentStep > 0) setState(() => _currentStep -= 1);
  }

  String? _requiredValidator(String? v, String label) {
    if (v == null || v.trim().isEmpty) return '$label is required';
    return null;
  }

  String? _priceValidator(String? v) {
    final parsed = double.tryParse((v ?? '').trim());
    if (parsed == null) return 'Enter a valid price';
    if (parsed <= 0) return 'Price must be greater than zero';
    return null;
  }

  String? _stockValidator(String? v) {
    final parsed = int.tryParse((v ?? '').trim());
    if (parsed == null) return 'Enter a whole number';
    if (parsed < 0) return 'Stock cannot be negative';
    return null;
  }

  String? _tierQtyValidator(_TierControllers tier, String? v) {
    if (tier.isEmpty) return null;
    final parsed = int.tryParse((v ?? '').trim());
    if (parsed == null || parsed < 1) return 'Min 1 unit';
    return null;
  }

  String? _tierPriceValidator(_TierControllers tier, String? v) {
    if (tier.isEmpty) return null;
    final parsed = double.tryParse((v ?? '').trim());
    if (parsed == null || parsed <= 0) return 'Enter a price';
    final retail = double.tryParse(_priceController.text.trim());
    if (retail != null && parsed >= retail) return 'Below retail';
    return null;
  }

  List<WholesaleTier> _collectTiers() {
    final tiers = <WholesaleTier>[];
    for (final t in _tiers) {
      if (t.isEmpty) continue;
      final qty = int.tryParse(t.minQty.text.trim());
      final price = double.tryParse(t.price.text.trim());
      if (qty == null || price == null) continue;
      tiers.add(WholesaleTier(minQuantity: qty, pricePerUnit: price));
    }
    tiers.sort((a, b) => a.minQuantity.compareTo(b.minQuantity));
    return tiers;
  }

  void _addImageUrl() {
    final url = _imageUrlController.text.trim();
    if (url.isEmpty) return;
    final uri = Uri.tryParse(url);
    if (uri == null || !(uri.isScheme('http') || uri.isScheme('https')) || uri.host.isEmpty) {
      _showSnack('Enter a valid http(s) image URL', isError: true);
      return;
    }
    if (_imageUrls.contains(url)) {
      _showSnack('That image is already in the list', isError: true);
      return;
    }
    setState(() {
      _imageUrls.add(url);
      _imageUrlController.clear();
    });
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

  // ---------------------------------------------------------------------------
  // Save
  // ---------------------------------------------------------------------------

  Future<void> _save(ProductStatus status) async {
    // Validate all steps before writing (drafts still need the basics).
    final stepsToValidate = status == ProductStatus.draft
        ? [_stepBasics, _stepPricing]
        : [_stepBasics, _stepStory, _stepPricing, _stepImages, _stepLocation];
    for (final step in stepsToValidate) {
      if (!_validateStep(step)) {
        setState(() => _currentStep = step);
        _showSnack('Please fix the highlighted fields first', isError: true);
        return;
      }
    }

    final user = ref.read(currentUserProvider);
    final sellerId = user?.sellerId;
    if (sellerId == null) {
      _showSnack('Complete your artisan storefront first', isError: true);
      return;
    }

    final input = ProductInput(
      title: _titleController.text.trim(),
      description: _descController.text.trim(),
      category: _category ?? _categoryOptions.first,
      material: _materialController.text.trim(),
      price: double.parse(_priceController.text.trim()),
      stock: int.parse(_stockController.text.trim()),
      imageUrls: List.unmodifiable(_imageUrls),
      status: status,
      city: _cityController.text.trim().isEmpty ? null : _cityController.text.trim(),
      state: _stateController.text.trim().isEmpty ? null : _stateController.text.trim(),
      wholesaleTiers: _collectTiers(),
    );

    setState(() => _isSaving = true);
    try {
      final repo = ref.read(supabaseProductsRepositoryProvider);
      final existing = widget.initialProduct;
      if (existing != null) {
        await repo.updateProduct(productId: existing.id, sellerId: sellerId, input: input);
      } else {
        await repo.createProduct(sellerId: sellerId, input: input);
      }
      ref.invalidate(sellerProductsProvider);
      if (!mounted) return;
      final verb = existing != null ? 'updated' : 'created';
      _showSnack(
        status == ProductStatus.published
            ? 'Product $verb and published to your store.'
            : 'Product $verb and saved as a draft.',
      );
      context.pop();
    } catch (e) {
      _showSnack(authErrorMessage(e), isError: true);
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }

  // ---------------------------------------------------------------------------
  // Build
  // ---------------------------------------------------------------------------

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final user = ref.watch(currentUserProvider);

    if (user != null && user.sellerId == null) {
      return Scaffold(
        appBar: AppBar(title: Text(_isEditing ? 'Edit Craft Product' : 'Add Craft Product')),
        body: AppEmptyState(
          icon: Icons.storefront_outlined,
          title: 'Complete your artisan storefront first',
          message: 'Products are listed under your storefront. Set it up once and you can start adding crafts.',
          actionLabel: 'Set up storefront',
          onAction: () => context.push('/artisan-onboarding'),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: Text(_isEditing ? 'Edit Craft Product' : 'Add Craft Product'),
        actions: [
          TextButton.icon(
            icon: const Icon(Icons.save_outlined, size: 16),
            label: const Text('Save as draft'),
            onPressed: _isSaving ? null : () => _save(ProductStatus.draft),
          ),
        ],
      ),
      body: Stepper(
        type: StepperType.vertical,
        currentStep: _currentStep,
        onStepTapped: _isSaving ? null : _goToStep,
        onStepContinue: _isSaving ? null : _onContinue,
        onStepCancel: _isSaving ? null : _onBack,
        controlsBuilder: (context, details) {
          final isLast = _currentStep == _stepReview;
          return Padding(
            padding: const EdgeInsets.only(top: 16),
            child: Row(
              children: [
                Expanded(
                  child: isLast
                      ? AppButton(
                          label: _isEditing ? 'Save & Publish' : 'Publish Craft Product',
                          icon: Icons.check_circle_outline,
                          isLoading: _isSaving,
                          onPressed: () => _save(ProductStatus.published),
                        )
                      : ElevatedButton(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.secondary,
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            shape: AppRadius.shapeMd,
                          ),
                          onPressed: details.onStepContinue,
                          child: Text(
                            'Next (${_currentStep + 1}/$_stepCount)',
                            style: const TextStyle(fontWeight: FontWeight.bold),
                          ),
                        ),
                ),
                if (_currentStep > 0) ...[
                  AppSpacing.gapH12,
                  OutlinedButton(onPressed: details.onStepCancel, child: const Text('Back')),
                ],
              ],
            ),
          );
        },
        steps: [
          _buildStep(
            index: _stepBasics,
            title: 'Basics',
            subtitle: _titleController.text.trim().isEmpty ? 'Title, category & material' : _titleController.text.trim(),
            child: Column(
              children: [
                TextFormField(
                  controller: _titleController,
                  textInputAction: TextInputAction.next,
                  decoration: const InputDecoration(
                    labelText: 'Product title *',
                    hintText: 'e.g. Hand-painted terracotta planter',
                  ),
                  validator: (v) => _requiredValidator(v, 'Title'),
                  onChanged: (_) => setState(() {}),
                ),
                AppSpacing.gapV12,
                DropdownButtonFormField<String>(
                  initialValue: _category,
                  decoration: const InputDecoration(labelText: 'Craft category *'),
                  items: _categoryOptions.map((c) => DropdownMenuItem(value: c, child: Text(c))).toList(),
                  onChanged: (v) => setState(() => _category = v),
                  validator: (v) => v == null ? 'Pick a category' : null,
                ),
                AppSpacing.gapV12,
                TextFormField(
                  controller: _materialController,
                  textInputAction: TextInputAction.next,
                  decoration: const InputDecoration(
                    labelText: 'Primary material *',
                    hintText: 'e.g. River clay, natural mineral glaze',
                  ),
                  validator: (v) => _requiredValidator(v, 'Material'),
                ),
              ],
            ),
          ),
          _buildStep(
            index: _stepStory,
            title: 'Story',
            subtitle: 'Describe the craft and its technique',
            child: TextFormField(
              controller: _descController,
              maxLines: 5,
              decoration: const InputDecoration(
                labelText: 'Description *',
                hintText: 'How is it made? What makes it special? Care instructions?',
                alignLabelWithHint: true,
              ),
              validator: (v) {
                if (v == null || v.trim().isEmpty) return 'Description is required';
                if (v.trim().length < 20) return 'Add a little more detail (at least 20 characters)';
                return null;
              },
            ),
          ),
          _buildStep(
            index: _stepPricing,
            title: 'Pricing & Stock',
            subtitle: _priceController.text.trim().isEmpty
                ? 'Retail price, stock & wholesale tiers'
                : '${CurrencyFormatter.formatINR(double.tryParse(_priceController.text.trim()) ?? 0)} · ${_stockController.text.trim().isEmpty ? '0' : _stockController.text.trim()} in stock',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: TextFormField(
                        controller: _priceController,
                        keyboardType: const TextInputType.numberWithOptions(decimal: true),
                        decoration: const InputDecoration(
                          labelText: 'Retail price (₹) *',
                          prefixIcon: Icon(Icons.currency_rupee),
                        ),
                        validator: _priceValidator,
                        onChanged: (_) => setState(() {}),
                      ),
                    ),
                    AppSpacing.gapH12,
                    Expanded(
                      child: TextFormField(
                        controller: _stockController,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(
                          labelText: 'Stock (units) *',
                          prefixIcon: Icon(Icons.inventory_2_outlined),
                        ),
                        validator: _stockValidator,
                        onChanged: (_) => setState(() {}),
                      ),
                    ),
                  ],
                ),
                AppSpacing.gapV16,
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'Wholesale tiers (optional, up to $_maxTiers)',
                      style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold),
                    ),
                    if (_tiers.length < _maxTiers)
                      TextButton.icon(
                        icon: const Icon(Icons.add, size: 16),
                        label: const Text('Add tier'),
                        onPressed: () => setState(() => _tiers.add(_TierControllers())),
                      ),
                  ],
                ),
                if (_tiers.isEmpty)
                  Text(
                    'Offer a lower per-unit price for bulk buyers, e.g. 10+ units at ₹450.',
                    style: theme.textTheme.bodySmall,
                  ),
                ..._tiers.asMap().entries.map((entry) {
                  final i = entry.key;
                  final tier = entry.value;
                  return Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(
                          child: TextFormField(
                            controller: tier.minQty,
                            keyboardType: TextInputType.number,
                            decoration: InputDecoration(labelText: 'Tier ${i + 1} min qty'),
                            validator: (v) => _tierQtyValidator(tier, v),
                          ),
                        ),
                        AppSpacing.gapH8,
                        Expanded(
                          child: TextFormField(
                            controller: tier.price,
                            keyboardType: const TextInputType.numberWithOptions(decimal: true),
                            decoration: const InputDecoration(labelText: 'Price per unit (₹)'),
                            validator: (v) => _tierPriceValidator(tier, v),
                          ),
                        ),
                        IconButton(
                          tooltip: 'Remove tier',
                          icon: const Icon(Icons.remove_circle_outline, color: AppColors.error),
                          onPressed: () => setState(() => _tiers.removeAt(i).dispose()),
                        ),
                      ],
                    ),
                  );
                }),
              ],
            ),
          ),
          _buildStep(
            index: _stepImages,
            title: 'Images',
            subtitle: _imageUrls.isEmpty ? 'Add image links (optional)' : '${_imageUrls.length} image${_imageUrls.length == 1 ? '' : 's'}',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Paste public image URLs. The first image is used as the cover.',
                  style: theme.textTheme.bodySmall,
                ),
                AppSpacing.gapV8,
                Row(
                  children: [
                    Expanded(
                      child: TextFormField(
                        controller: _imageUrlController,
                        keyboardType: TextInputType.url,
                        decoration: const InputDecoration(
                          labelText: 'Image URL',
                          hintText: 'https://...',
                          prefixIcon: Icon(Icons.link),
                        ),
                        onFieldSubmitted: (_) => _addImageUrl(),
                      ),
                    ),
                    AppSpacing.gapH8,
                    IconButton.filled(
                      tooltip: 'Add image',
                      icon: const Icon(Icons.add),
                      onPressed: _addImageUrl,
                    ),
                  ],
                ),
                if (_imageUrls.isNotEmpty) ...[
                  AppSpacing.gapV12,
                  SizedBox(
                    height: 96,
                    child: ListView.separated(
                      scrollDirection: Axis.horizontal,
                      itemCount: _imageUrls.length,
                      separatorBuilder: (_, __) => AppSpacing.gapH8,
                      itemBuilder: (context, i) {
                        final url = _imageUrls[i];
                        return Stack(
                          children: [
                            ClipRRect(
                              borderRadius: AppRadius.borderMd,
                              child: Image.network(
                                url,
                                width: 96,
                                height: 96,
                                fit: BoxFit.cover,
                                errorBuilder: (_, __, ___) => const AppImagePlaceholder(width: 96, height: 96),
                              ),
                            ),
                            if (i == 0)
                              Positioned(
                                left: 4,
                                top: 4,
                                child: Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                                  decoration: const BoxDecoration(
                                    color: AppColors.primary,
                                    borderRadius: AppRadius.borderXs,
                                  ),
                                  child: const Text(
                                    'COVER',
                                    style: TextStyle(color: Colors.white, fontSize: 8, fontWeight: FontWeight.bold),
                                  ),
                                ),
                              ),
                            Positioned(
                              right: 2,
                              top: 2,
                              child: GestureDetector(
                                onTap: () => setState(() => _imageUrls.removeAt(i)),
                                child: Container(
                                  padding: const EdgeInsets.all(3),
                                  decoration: const BoxDecoration(color: Colors.black54, shape: BoxShape.circle),
                                  child: const Icon(Icons.close, size: 12, color: Colors.white),
                                ),
                              ),
                            ),
                          ],
                        );
                      },
                    ),
                  ),
                ],
              ],
            ),
          ),
          _buildStep(
            index: _stepLocation,
            title: 'Location',
            subtitle: [
              _cityController.text.trim(),
              _stateController.text.trim(),
            ].where((s) => s.isNotEmpty).join(', ').isEmpty
                ? 'Where is this craft made?'
                : [_cityController.text.trim(), _stateController.text.trim()].where((s) => s.isNotEmpty).join(', '),
            child: Row(
              children: [
                Expanded(
                  child: TextFormField(
                    controller: _cityController,
                    decoration: const InputDecoration(labelText: 'City / Village', prefixIcon: Icon(Icons.location_city)),
                    onChanged: (_) => setState(() {}),
                  ),
                ),
                AppSpacing.gapH12,
                Expanded(
                  child: TextFormField(
                    controller: _stateController,
                    decoration: const InputDecoration(labelText: 'State', prefixIcon: Icon(Icons.map_outlined)),
                    onChanged: (_) => setState(() {}),
                  ),
                ),
              ],
            ),
          ),
          _buildStep(
            index: _stepReview,
            title: 'Review & Publish',
            subtitle: 'Check everything before it goes live',
            child: _buildReviewCard(theme),
          ),
        ],
      ),
    );
  }

  Step _buildStep({
    required int index,
    required String title,
    required String subtitle,
    required Widget child,
  }) {
    return Step(
      title: Text('${index + 1}. $title'),
      subtitle: Text(subtitle, maxLines: 1, overflow: TextOverflow.ellipsis),
      isActive: _currentStep >= index,
      state: _currentStep > index ? StepState.complete : StepState.indexed,
      content: Form(
        key: _formKeys[index],
        autovalidateMode: AutovalidateMode.disabled,
        child: child,
      ),
    );
  }

  Widget _buildReviewCard(ThemeData theme) {
    final price = double.tryParse(_priceController.text.trim());
    final stock = int.tryParse(_stockController.text.trim());
    final tiers = _collectTiers();
    final location = [_cityController.text.trim(), _stateController.text.trim()].where((s) => s.isNotEmpty).join(', ');

    return AppCard(
      padding: AppSpacing.paddingAllBase,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              ClipRRect(
                borderRadius: AppRadius.borderMd,
                child: _imageUrls.isNotEmpty
                    ? Image.network(
                        _imageUrls.first,
                        width: 64,
                        height: 64,
                        fit: BoxFit.cover,
                        errorBuilder: (_, __, ___) => const AppImagePlaceholder(width: 64, height: 64),
                      )
                    : const AppImagePlaceholder(width: 64, height: 64),
              ),
              AppSpacing.gapH12,
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _titleController.text.trim().isEmpty ? 'Untitled craft' : _titleController.text.trim(),
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    AppSpacing.gapV4,
                    Text(
                      [
                        _category ?? 'No category',
                        if (_materialController.text.trim().isNotEmpty) _materialController.text.trim(),
                      ].join(' · '),
                      style: theme.textTheme.bodySmall,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
            ],
          ),
          AppSpacing.gapV12,
          if (_descController.text.trim().isNotEmpty) ...[
            Text(
              _descController.text.trim(),
              style: theme.textTheme.bodySmall,
              maxLines: 4,
              overflow: TextOverflow.ellipsis,
            ),
            AppSpacing.gapV12,
          ],
          const Divider(height: 1),
          AppSpacing.gapV8,
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Retail: ${price == null ? '—' : CurrencyFormatter.formatINR(price)}',
                style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary),
              ),
              Text(
                'Stock: ${stock ?? '—'}',
                style: const TextStyle(fontWeight: FontWeight.w600),
              ),
            ],
          ),
          if (tiers.isNotEmpty) ...[
            AppSpacing.gapV8,
            ...tiers.map(
              (t) => Text(
                'Wholesale: ${t.minQuantity}+ units at ${CurrencyFormatter.formatINR(t.pricePerUnit)}',
                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.secondary),
              ),
            ),
          ],
          AppSpacing.gapV8,
          Text(
            '${_imageUrls.length} image${_imageUrls.length == 1 ? '' : 's'}${location.isEmpty ? '' : ' · $location'}',
            style: theme.textTheme.bodySmall,
          ),
        ],
      ),
    );
  }
}
