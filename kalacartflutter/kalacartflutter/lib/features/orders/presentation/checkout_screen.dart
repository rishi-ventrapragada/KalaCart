import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/utils/currency_formatter.dart';
import '../../../core/widgets/app_empty_state.dart';
import '../../../shared/models/order_models.dart';
import '../../auth/data/auth_repository.dart';
import '../../auth/data/supabase_auth_repository.dart';
import '../../products/data/cart_provider.dart';
import '../data/orders_repository.dart';

const List<String> _paymentMethods = [
  'UPI (Google Pay / PhonePe / Paytm)',
  'Credit / Debit Card',
  'Net Banking',
  'Bank Transfer (NEFT/RTGS for wholesale)',
];

class CheckoutScreen extends ConsumerStatefulWidget {
  const CheckoutScreen({super.key});

  @override
  ConsumerState<CheckoutScreen> createState() => _CheckoutScreenState();
}

class _CheckoutScreenState extends ConsumerState<CheckoutScreen> {
  final _addressFormKey = GlobalKey<FormState>();
  int _currentStep = 0;
  String _selectedPaymentMethod = _paymentMethods.first;
  bool _isPlacing = false;

  final _nameController = TextEditingController();
  final _phoneController = TextEditingController();
  final _addressController = TextEditingController();
  final _pincodeController = TextEditingController();
  final _cityController = TextEditingController();
  final _stateController = TextEditingController();

  @override
  void initState() {
    super.initState();
    final user = ref.read(currentUserProvider);
    if (user != null) {
      _nameController.text = user.fullName;
      _phoneController.text = user.phoneNumber ?? '';
      _cityController.text = user.city ?? '';
      _stateController.text = user.state ?? '';
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _phoneController.dispose();
    _addressController.dispose();
    _pincodeController.dispose();
    _cityController.dispose();
    _stateController.dispose();
    super.dispose();
  }

  String _composeAddress() {
    final parts = <String>[
      _nameController.text.trim(),
      if (_phoneController.text.trim().isNotEmpty) _phoneController.text.trim(),
      _addressController.text.trim(),
      [
        _cityController.text.trim(),
        if (_stateController.text.trim().isNotEmpty) _stateController.text.trim(),
      ].join(', '),
      'PIN ${_pincodeController.text.trim()}',
    ];
    return parts.where((p) => p.isNotEmpty).join(', ');
  }

  void _showError(Object e) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(authErrorMessage(e)),
        behavior: SnackBarBehavior.floating,
        backgroundColor: AppColors.error,
      ),
    );
  }

  void _onContinue() {
    if (_currentStep == 0) {
      if (_addressFormKey.currentState?.validate() != true) return;
      setState(() => _currentStep = 1);
      return;
    }
    if (_currentStep == 1) {
      setState(() => _currentStep = 2);
      return;
    }
    _placeOrder();
  }

  Future<void> _placeOrder() async {
    if (_isPlacing) return;
    if (_addressFormKey.currentState?.validate() != true) {
      setState(() => _currentStep = 0);
      return;
    }
    final user = ref.read(currentUserProvider);
    if (user == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please sign in to place an order.'),
          behavior: SnackBarBehavior.floating,
          backgroundColor: AppColors.error,
        ),
      );
      return;
    }
    final cart = ref.read(cartProvider);
    if (cart.isEmpty) return;

    setState(() => _isPlacing = true);
    try {
      final lines = cart
          .map((item) => OrderLineInput(
                productId: item.product.id,
                sellerId: item.product.sellerId,
                quantity: item.quantity,
                unitPrice: item.unitPrice,
              ))
          .toList();
      final orders = await ref.read(ordersRepositoryProvider).placeOrders(
            buyerAuthId: user.id,
            lines: lines,
            shippingAddress: _composeAddress(),
          );
      if (!mounted) return;
      ref.read(cartProvider.notifier).clearCart();
      ref.invalidate(buyerOrdersProvider);
      _showOrderSuccessDialog(orders);
    } catch (e) {
      _showError(e);
    } finally {
      if (mounted) setState(() => _isPlacing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final cart = ref.watch(cartProvider);
    final subtotal = ref.watch(cartSubtotalProvider);
    final deliveryFee = ref.watch(cartDeliveryFeeProvider);
    final totalAmount = ref.watch(cartTotalProvider);
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    if (cart.isEmpty && !_isPlacing) {
      return Scaffold(
        appBar: AppBar(title: const Text('Checkout')),
        body: AppEmptyState(
          icon: Icons.shopping_basket_outlined,
          title: 'Nothing to check out',
          message: 'Add some handmade crafts to your cart first.',
          actionLabel: 'Explore Handicrafts',
          onAction: () => context.go('/discovery'),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Checkout'),
      ),
      body: Stepper(
        type: StepperType.vertical,
        currentStep: _currentStep,
        onStepTapped: _isPlacing
            ? null
            : (step) {
                if (step > 0 && _addressFormKey.currentState?.validate() != true) {
                  setState(() => _currentStep = 0);
                  return;
                }
                setState(() => _currentStep = step);
              },
        onStepContinue: _isPlacing ? null : _onContinue,
        onStepCancel: _isPlacing || _currentStep == 0 ? null : () => setState(() => _currentStep -= 1),
        controlsBuilder: (context, details) {
          final isLast = _currentStep == 2;
          return Padding(
            padding: const EdgeInsets.only(top: 16),
            child: Row(
              children: [
                Expanded(
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      shape: AppRadius.shapeMd,
                    ),
                    onPressed: details.onStepContinue,
                    child: _isPlacing && isLast
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(strokeWidth: 2.5, color: Colors.white),
                          )
                        : Text(
                            isLast ? 'Place Order (${CurrencyFormatter.formatINR(totalAmount)})' : 'Continue',
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
          // Step 1: Delivery Address
          Step(
            title: const Text('Delivery Address'),
            subtitle: _nameController.text.trim().isEmpty
                ? null
                : Text(
                    '${_nameController.text.trim()}${_cityController.text.trim().isEmpty ? '' : ', ${_cityController.text.trim()}'}',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
            isActive: _currentStep >= 0,
            state: _currentStep > 0 ? StepState.complete : StepState.indexed,
            content: Form(
              key: _addressFormKey,
              autovalidateMode: AutovalidateMode.onUserInteraction,
              child: Column(
                children: [
                  TextFormField(
                    controller: _nameController,
                    textCapitalization: TextCapitalization.words,
                    decoration: const InputDecoration(labelText: 'Full Name *', prefixIcon: Icon(Icons.person_outline)),
                    validator: (v) => (v ?? '').trim().isEmpty ? 'Please enter the recipient name' : null,
                    onChanged: (_) => setState(() {}),
                  ),
                  AppSpacing.gapV12,
                  TextFormField(
                    controller: _phoneController,
                    keyboardType: TextInputType.phone,
                    decoration: const InputDecoration(labelText: 'Mobile Number', prefixIcon: Icon(Icons.phone_outlined)),
                  ),
                  AppSpacing.gapV12,
                  TextFormField(
                    controller: _addressController,
                    decoration: const InputDecoration(
                      labelText: 'Street Address & Flat / House *',
                      prefixIcon: Icon(Icons.home_outlined),
                    ),
                    validator: (v) => (v ?? '').trim().isEmpty ? 'Please enter your street address' : null,
                  ),
                  AppSpacing.gapV12,
                  Row(
                    children: [
                      Expanded(
                        child: TextFormField(
                          controller: _pincodeController,
                          keyboardType: TextInputType.number,
                          maxLength: 6,
                          decoration: const InputDecoration(
                            labelText: 'PIN Code *',
                            prefixIcon: Icon(Icons.pin_drop_outlined),
                            counterText: '',
                          ),
                          validator: (v) {
                            final value = (v ?? '').trim();
                            if (value.isEmpty) return 'Enter PIN code';
                            if (!RegExp(r'^\d{6}$').hasMatch(value)) return 'Enter a 6-digit PIN';
                            return null;
                          },
                        ),
                      ),
                      AppSpacing.gapH12,
                      Expanded(
                        child: TextFormField(
                          controller: _cityController,
                          textCapitalization: TextCapitalization.words,
                          decoration: const InputDecoration(labelText: 'City *'),
                          validator: (v) => (v ?? '').trim().isEmpty ? 'Enter city' : null,
                          onChanged: (_) => setState(() {}),
                        ),
                      ),
                    ],
                  ),
                  AppSpacing.gapV12,
                  TextFormField(
                    controller: _stateController,
                    textCapitalization: TextCapitalization.words,
                    decoration: const InputDecoration(labelText: 'State', prefixIcon: Icon(Icons.map_outlined)),
                  ),
                ],
              ),
            ),
          ),

          // Step 2: Review items
          Step(
            title: const Text('Review Items'),
            subtitle: Text('${cart.length} ${cart.length == 1 ? 'item' : 'items'} · ${CurrencyFormatter.formatINR(totalAmount)}'),
            isActive: _currentStep >= 1,
            state: _currentStep > 1 ? StepState.complete : StepState.indexed,
            content: Container(
              padding: AppSpacing.paddingAllBase,
              decoration: BoxDecoration(
                color: isDark ? AppColors.surfaceDark : AppColors.surfaceLight,
                borderRadius: AppRadius.borderMd,
                border: Border.all(color: isDark ? AppColors.borderDark : AppColors.borderLight),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  ...cart.map(
                    (item) => Padding(
                      padding: const EdgeInsets.symmetric(vertical: 3),
                      child: Row(
                        children: [
                          Expanded(
                            child: Text(
                              '${item.product.title} × ${item.quantity}',
                              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          AppSpacing.gapH8,
                          Text(
                            CurrencyFormatter.formatINR(item.totalPrice),
                            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
                          ),
                        ],
                      ),
                    ),
                  ),
                  AppSpacing.gapV8,
                  const Divider(height: 1),
                  AppSpacing.gapV8,
                  _SummaryRow(label: 'Subtotal', value: CurrencyFormatter.formatINR(subtotal)),
                  _SummaryRow(
                    label: 'Packaging & Delivery',
                    value: deliveryFee == 0 ? 'FREE' : CurrencyFormatter.formatINR(deliveryFee),
                  ),
                  _SummaryRow(label: 'Total', value: CurrencyFormatter.formatINR(totalAmount), isBold: true),
                  AppSpacing.gapV8,
                  const Row(
                    children: [
                      Icon(Icons.shield_outlined, color: AppColors.success, size: 16),
                      SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          'Each item is packed by the artisan and shipped separately.',
                          style: TextStyle(fontSize: 11, color: Colors.grey),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),

          // Step 3: Payment
          Step(
            title: const Text('Payment'),
            subtitle: Text(_selectedPaymentMethod, maxLines: 1, overflow: TextOverflow.ellipsis),
            isActive: _currentStep >= 2,
            state: StepState.indexed,
            content: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  padding: AppSpacing.paddingAllBase,
                  decoration: BoxDecoration(
                    color: AppColors.warningContainer.withValues(alpha: 0.5),
                    borderRadius: AppRadius.borderMd,
                  ),
                  child: const Row(
                    children: [
                      Icon(Icons.info_outline, color: AppColors.warning, size: 18),
                      SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          'Demo checkout – no real payment is charged. Your order is recorded so the artisan can start work.',
                          style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600),
                        ),
                      ),
                    ],
                  ),
                ),
                AppSpacing.gapV12,
                RadioGroup<String>(
                  groupValue: _selectedPaymentMethod,
                  onChanged: (v) {
                    if (_isPlacing) return;
                    setState(() => _selectedPaymentMethod = v ?? _paymentMethods.first);
                  },
                  child: Column(
                    children: _paymentMethods
                        .map(
                          (method) => RadioListTile<String>(
                            value: method,
                            contentPadding: EdgeInsets.zero,
                            dense: true,
                            activeColor: AppColors.primary,
                            title: Text(
                              method,
                              style: TextStyle(
                                fontSize: 13,
                                fontWeight: _selectedPaymentMethod == method ? FontWeight.bold : FontWeight.w500,
                                color: _selectedPaymentMethod == method ? AppColors.primary : null,
                              ),
                            ),
                          ),
                        )
                        .toList(),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  void _showOrderSuccessDialog(List<OrderRecord> orders) {
    final total = orders.fold<double>(0, (sum, o) => sum + o.totalAmount);
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (dialogContext) {
        return AlertDialog(
          shape: const RoundedRectangleBorder(
            borderRadius: BorderRadius.all(Radius.circular(20)),
          ),
          title: const Column(
            children: [
              Icon(Icons.check_circle_rounded, color: AppColors.success, size: 54),
              SizedBox(height: 8),
              Text('Order Placed!'),
            ],
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'Thank you for supporting Indian artisans directly.',
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.grey.shade700, fontSize: 13),
              ),
              AppSpacing.gapV12,
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.successContainer.withValues(alpha: 0.3),
                  borderRadius: AppRadius.borderMd,
                ),
                child: Column(
                  children: [
                    Text(
                      orders.length == 1 ? 'ORDER NUMBER' : 'ORDER NUMBERS',
                      style: const TextStyle(fontSize: 10, color: Colors.grey, fontWeight: FontWeight.bold, letterSpacing: 0.5),
                    ),
                    const SizedBox(height: 4),
                    ...orders.map(
                      (o) => Text(
                        o.orderNumber,
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, fontFamily: 'monospace'),
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      'Total: ${CurrencyFormatter.formatINR(total)}',
                      style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary),
                    ),
                  ],
                ),
              ),
            ],
          ),
          actions: [
            ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: AppColors.primary, foregroundColor: Colors.white),
              onPressed: () {
                Navigator.of(dialogContext).pop();
                if (mounted) context.go('/orders');
              },
              child: const Text('View My Orders'),
            ),
          ],
        );
      },
    );
  }
}

class _SummaryRow extends StatelessWidget {
  final String label;
  final String value;
  final bool isBold;

  const _SummaryRow({required this.label, required this.value, this.isBold = false});

  @override
  Widget build(BuildContext context) {
    final style = TextStyle(fontSize: isBold ? 13 : 12, fontWeight: isBold ? FontWeight.bold : FontWeight.w500);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: style),
          Text(value, style: style.copyWith(color: isBold ? AppColors.primary : null)),
        ],
      ),
    );
  }
}
