import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/utils/currency_formatter.dart';
import '../../../core/widgets/app_button.dart';
import '../../../core/widgets/app_error_state.dart';
import '../../../core/widgets/app_image_placeholder.dart';
import '../../../core/widgets/app_loading_state.dart';
import '../../../shared/models/enquiry_models.dart';
import '../../../shared/models/product.dart';
import '../../ai/presentation/widgets/voice_assistant_modal.dart';
import '../../auth/data/auth_repository.dart';
import '../../auth/data/supabase_auth_repository.dart';
import '../../products/data/supabase_products_repository.dart';
import '../data/supabase_rfq_repository.dart';

class BuyerCreateRfqScreen extends ConsumerStatefulWidget {
  /// Optional product the enquiry is about (from the product details page).
  final String? productId;

  const BuyerCreateRfqScreen({super.key, this.productId});

  @override
  ConsumerState<BuyerCreateRfqScreen> createState() => _BuyerCreateRfqScreenState();
}

class _BuyerCreateRfqScreenState extends ConsumerState<BuyerCreateRfqScreen> {
  final _formKey = GlobalKey<FormState>();
  final TextEditingController _titleController = TextEditingController();
  final TextEditingController _qtyController = TextEditingController();
  final TextEditingController _priceController = TextEditingController();
  final TextEditingController _deliveryController = TextEditingController();
  final TextEditingController _pincodeController = TextEditingController();
  final TextEditingController _notesController = TextEditingController();

  /// Product chosen from the catalogue when no [BuyerCreateRfqScreen.productId] was given.
  String? _selectedProductId;
  bool _submitting = false;

  static final _pincodePattern = RegExp(r'^\d{6}$');

  @override
  void dispose() {
    _titleController.dispose();
    _qtyController.dispose();
    _priceController.dispose();
    _deliveryController.dispose();
    _pincodeController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  int? get _quantity => int.tryParse(_qtyController.text.trim());
  double? get _targetPrice => double.tryParse(_priceController.text.trim());

  String _autoTitle(Product? product) {
    final qty = _quantity;
    if (product == null) return '';
    return qty == null || qty < 1 ? product.title : '$qty × ${product.title}';
  }

  void _showSnack(String message, {bool isError = false}) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: isError ? AppColors.error : null,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  Future<void> _pickDeliveryDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: now.add(const Duration(days: 30)),
      firstDate: now,
      lastDate: now.add(const Duration(days: 365 * 2)),
      helpText: 'Deliver by',
    );
    if (picked == null || !mounted) return;
    setState(() => _deliveryController.text = DateFormat('d MMM yyyy').format(picked));
  }

  Future<void> _dictateNotes() async {
    final result = await VoiceAssistantModal.show(context, isArtisanMode: false);
    if (result == null || !mounted) return;
    final transcript = result.rawTranscript.trim();
    if (transcript.isEmpty) return;
    setState(() {
      final existing = _notesController.text.trim();
      _notesController.text = existing.isEmpty ? transcript : '$existing\n$transcript';
    });
  }

  Future<void> _submit(Product? product) async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    if (product == null) {
      _showSnack('Choose the product you want a quote for.', isError: true);
      return;
    }
    final user = ref.read(currentUserProvider);
    if (user == null) {
      _showSnack('Sign in to send an enquiry.', isError: true);
      return;
    }
    final quantity = _quantity;
    if (quantity == null || quantity < 1) return;

    final title = _titleController.text.trim().isEmpty ? _autoTitle(product) : _titleController.text.trim();
    final details = RfqDetails(
      title: title,
      targetPricePerUnit: _targetPrice,
      deliveryBy: _deliveryController.text.trim().isEmpty ? null : _deliveryController.text.trim(),
      destinationPincode: _pincodeController.text.trim().isEmpty ? null : _pincodeController.text.trim(),
      notes: _notesController.text.trim(),
    );

    setState(() => _submitting = true);
    try {
      await ref.read(supabaseRfqRepositoryProvider).submitEnquiry(
            buyerAuthId: user.id,
            productId: product.id,
            quantity: quantity,
            details: details,
          );
      ref.invalidate(buyerEnquiriesProvider);
      if (!mounted) return;
      _showSnack('Enquiry sent to ${product.artisanName}');
      context.pop();
    } catch (e) {
      if (!mounted) return;
      setState(() => _submitting = false);
      _showSnack(authErrorMessage(e), isError: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final lockedId = widget.productId;
    final AsyncValue<Product?> productAsync;
    final AsyncValue<List<Product>>? catalogueAsync;

    if (lockedId != null) {
      productAsync = ref.watch(productProvider(lockedId));
      catalogueAsync = null;
    } else {
      final catalogue = ref.watch(publishedProductsProvider);
      catalogueAsync = catalogue;
      productAsync = catalogue.whenData((products) {
        if (_selectedProductId == null) return null;
        for (final p in products) {
          if (p.id == _selectedProductId) return p;
        }
        return null;
      });
    }

    final product = productAsync.valueOrNull;
    final qty = _quantity ?? 0;
    final target = _targetPrice;
    final unitBasis = target ?? product?.unitPriceFor(qty < 1 ? 1 : qty);
    final totalBudget = unitBasis == null || qty < 1 ? null : unitBasis * qty;

    return Scaffold(
      appBar: AppBar(title: const Text('New Enquiry')),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: AppSpacing.paddingAllBase,
          children: [
            const Text(
              'Ask an artisan for a bulk or custom quote',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
            AppSpacing.gapV4,
            const Text(
              'Your enquiry goes straight to the artisan who listed the product. They reply with pricing and a delivery timeline in chat.',
              style: TextStyle(fontSize: 12, color: Colors.grey, height: 1.35),
            ),
            AppSpacing.gapV16,

            // Product
            if (lockedId != null)
              productAsync.when(
                loading: () => const AppLoadingState(message: 'Loading product...'),
                error: (e, _) => AppErrorState(
                  title: 'Could not load product',
                  message: authErrorMessage(e),
                  onRetry: () => ref.invalidate(productProvider(lockedId)),
                ),
                data: (p) => p == null
                    ? const AppErrorState(
                        title: 'Product not found',
                        message: 'This craft is no longer listed.',
                      )
                    : _ProductSummary(product: p),
              )
            else
              catalogueAsync!.when(
                loading: () => const AppLoadingState(message: 'Loading crafts...'),
                error: (e, _) => AppErrorState(
                  title: 'Could not load crafts',
                  message: authErrorMessage(e),
                  onRetry: () => ref.invalidate(publishedProductsProvider),
                ),
                data: (products) => Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    DropdownButtonFormField<String>(
                      initialValue: products.any((p) => p.id == _selectedProductId) ? _selectedProductId : null,
                      isExpanded: true,
                      decoration: const InputDecoration(
                        labelText: 'Product *',
                        prefixIcon: Icon(Icons.shopping_bag_outlined),
                      ),
                      hint: const Text('Choose a listed craft'),
                      items: [
                        for (final p in products)
                          DropdownMenuItem<String>(
                            value: p.id,
                            child: Text(
                              '${p.title} · ${p.artisanName}',
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                      ],
                      validator: (v) => v == null ? 'Choose a product' : null,
                      onChanged: _submitting ? null : (v) => setState(() => _selectedProductId = v),
                    ),
                    if (product != null) ...[
                      AppSpacing.gapV12,
                      _ProductSummary(product: product),
                    ],
                  ],
                ),
              ),
            AppSpacing.gapV16,

            TextFormField(
              controller: _titleController,
              decoration: InputDecoration(
                labelText: 'Enquiry title (optional)',
                hintText: product == null ? 'Auto-filled from quantity and product' : _autoTitle(product),
                prefixIcon: const Icon(Icons.title),
              ),
            ),
            AppSpacing.gapV12,

            Row(
              children: [
                Expanded(
                  child: TextFormField(
                    controller: _qtyController,
                    keyboardType: TextInputType.number,
                    onChanged: (_) => setState(() {}),
                    decoration: const InputDecoration(
                      labelText: 'Quantity (units) *',
                      prefixIcon: Icon(Icons.numbers),
                    ),
                    validator: (v) {
                      final n = int.tryParse((v ?? '').trim());
                      if (n == null || n < 1) return 'Enter a whole number of 1 or more';
                      return null;
                    },
                  ),
                ),
                AppSpacing.gapH12,
                Expanded(
                  child: TextFormField(
                    controller: _priceController,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    onChanged: (_) => setState(() {}),
                    decoration: const InputDecoration(
                      labelText: 'Target price / unit (₹)',
                      prefixIcon: Icon(Icons.currency_rupee),
                    ),
                    validator: (v) {
                      final text = (v ?? '').trim();
                      if (text.isEmpty) return null;
                      final n = double.tryParse(text);
                      if (n == null || n <= 0) return 'Enter a price above 0';
                      return null;
                    },
                  ),
                ),
              ],
            ),
            AppSpacing.gapV12,

            Row(
              children: [
                Expanded(
                  child: TextFormField(
                    controller: _deliveryController,
                    readOnly: true,
                    onTap: _submitting ? null : _pickDeliveryDate,
                    decoration: InputDecoration(
                      labelText: 'Deliver by',
                      prefixIcon: const Icon(Icons.event_outlined),
                      suffixIcon: _deliveryController.text.isEmpty
                          ? null
                          : IconButton(
                              icon: const Icon(Icons.clear, size: 18),
                              onPressed: () => setState(() => _deliveryController.clear()),
                            ),
                    ),
                  ),
                ),
                AppSpacing.gapH12,
                Expanded(
                  child: TextFormField(
                    controller: _pincodeController,
                    keyboardType: TextInputType.number,
                    maxLength: 6,
                    decoration: const InputDecoration(
                      labelText: 'Destination PIN',
                      prefixIcon: Icon(Icons.location_on_outlined),
                      counterText: '',
                    ),
                    validator: (v) {
                      final text = (v ?? '').trim();
                      if (text.isEmpty) return null;
                      if (!_pincodePattern.hasMatch(text)) return 'Enter a 6-digit PIN code';
                      return null;
                    },
                  ),
                ),
              ],
            ),
            AppSpacing.gapV12,

            TextFormField(
              controller: _notesController,
              maxLines: 4,
              decoration: const InputDecoration(
                labelText: 'Customisation & material requirements *',
                hintText: 'Describe colours, dimensions, motifs, packaging, branding...',
                alignLabelWithHint: true,
              ),
              validator: (v) => (v ?? '').trim().isEmpty ? 'Tell the artisan what you need' : null,
            ),
            AppSpacing.gapV8,
            Align(
              alignment: Alignment.centerLeft,
              child: TextButton.icon(
                icon: const Icon(Icons.mic_none_rounded, size: 18),
                label: const Text('Voice notes (simulated)'),
                onPressed: _submitting ? null : _dictateNotes,
              ),
            ),
            AppSpacing.gapV16,

            // Target budget
            Container(
              padding: AppSpacing.paddingAllBase,
              decoration: BoxDecoration(
                color: AppColors.secondaryContainer.withValues(alpha: 0.4),
                borderRadius: AppRadius.borderMd,
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Target budget', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                        Text(
                          target != null
                              ? 'Quantity × your target price'
                              : (product != null ? 'Quantity × listed price' : 'Enter a quantity and product'),
                          style: const TextStyle(fontSize: 11, color: Colors.grey),
                        ),
                      ],
                    ),
                  ),
                  Text(
                    totalBudget == null ? '—' : CurrencyFormatter.formatINR(totalBudget),
                    style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary, fontSize: 16),
                  ),
                ],
              ),
            ),
            AppSpacing.gapV24,

            AppButton(
              label: product == null ? 'Send enquiry' : 'Send enquiry to ${product.artisanName}',
              icon: Icons.send_rounded,
              isLoading: _submitting,
              onPressed: product == null ? null : () => _submit(product),
            ),
            AppSpacing.gapV32,
          ],
        ),
      ),
    );
  }
}

class _ProductSummary extends StatelessWidget {
  final Product product;

  const _ProductSummary({required this.product});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final secondary = isDark ? AppColors.textSecondaryDark : AppColors.textSecondaryLight;
    final image = product.primaryImageUrl;

    return Container(
      padding: AppSpacing.paddingAllMd,
      decoration: BoxDecoration(
        color: isDark ? AppColors.cardDark : AppColors.cardLight,
        borderRadius: AppRadius.borderMd,
        border: Border.all(color: isDark ? AppColors.borderDark : AppColors.borderLight),
      ),
      child: Row(
        children: [
          ClipRRect(
            borderRadius: AppRadius.borderSm,
            child: image == null
                ? const AppImagePlaceholder(width: 64, height: 64)
                : Image.network(
                    image,
                    width: 64,
                    height: 64,
                    fit: BoxFit.cover,
                    errorBuilder: (_, __, ___) => const AppImagePlaceholder(width: 64, height: 64),
                  ),
          ),
          AppSpacing.gapH12,
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  product.title,
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                AppSpacing.gapV2,
                Text(
                  '${product.artisanName} · ${product.region}',
                  style: TextStyle(fontSize: 11, color: secondary),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                AppSpacing.gapV4,
                Text(
                  '${CurrencyFormatter.formatINR(product.price)} / unit · ${product.category}',
                  style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.primary),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
