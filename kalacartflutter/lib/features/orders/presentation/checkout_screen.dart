import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/utils/currency_formatter.dart';
import '../../products/data/buyer_catalog_repository.dart';

class CheckoutScreen extends ConsumerStatefulWidget {
  const CheckoutScreen({super.key});

  @override
  ConsumerState<CheckoutScreen> createState() => _CheckoutScreenState();
}

class _CheckoutScreenState extends ConsumerState<CheckoutScreen> {
  int _currentStep = 0;
  String _selectedPaymentMethod = 'UPI Escrow (Google Pay / PhonePe)';

  final TextEditingController _nameController = TextEditingController(text: 'Priya Sundaram');
  final TextEditingController _phoneController = TextEditingController(text: '+91 98765 43210');
  final TextEditingController _addressController = TextEditingController(text: 'Flat 402, Lotus Towers, Indiranagar');
  final TextEditingController _pincodeController = TextEditingController(text: '560038');
  final TextEditingController _cityController = TextEditingController(text: 'Bengaluru, Karnataka');

  @override
  void dispose() {
    _nameController.dispose();
    _phoneController.dispose();
    _addressController.dispose();
    _pincodeController.dispose();
    _cityController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final subtotal = ref.watch(cartSubtotalProvider);
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final totalAmount = subtotal > 3000 ? subtotal : subtotal + 150.0;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Artisan Direct Checkout'),
      ),
      body: Stepper(
        type: StepperType.vertical,
        currentStep: _currentStep,
        onStepTapped: (step) => setState(() => _currentStep = step),
        onStepContinue: () {
          if (_currentStep < 2) {
            setState(() => _currentStep += 1);
          } else {
            _showOrderSuccessDialog(context, totalAmount);
          }
        },
        onStepCancel: () {
          if (_currentStep > 0) {
            setState(() => _currentStep -= 1);
          }
        },
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
                    child: Text(
                      isLast ? 'Pay & Place Order (${CurrencyFormatter.formatINR(totalAmount)})' : 'Continue to Next Step',
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
            title: const Text('1. Delivery Address'),
            subtitle: Text('${_nameController.text}, ${_cityController.text}'),
            isActive: _currentStep >= 0,
            state: _currentStep > 0 ? StepState.complete : StepState.indexed,
            content: Column(
              children: [
                TextField(
                  controller: _nameController,
                  decoration: const InputDecoration(labelText: 'Full Name *', prefixIcon: Icon(Icons.person_outline)),
                ),
                AppSpacing.gapV12,
                TextField(
                  controller: _phoneController,
                  keyboardType: TextInputType.phone,
                  decoration: const InputDecoration(labelText: 'Mobile Number *', prefixIcon: Icon(Icons.phone_outlined)),
                ),
                AppSpacing.gapV12,
                TextField(
                  controller: _addressController,
                  decoration: const InputDecoration(labelText: 'Street Address & Flat / House *', prefixIcon: Icon(Icons.home_outlined)),
                ),
                AppSpacing.gapV12,
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: _pincodeController,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(labelText: 'PIN Code *', prefixIcon: Icon(Icons.pin_drop_outlined)),
                      ),
                    ),
                    AppSpacing.gapH12,
                    Expanded(
                      child: TextField(
                        controller: _cityController,
                        decoration: const InputDecoration(labelText: 'City & State *'),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),

          // Step 2: Artisan Safe Dispatch
          Step(
            title: const Text('2. Artisan Safe Shipping'),
            subtitle: const Text('GI Tagged Craft Transit with Safe Packaging'),
            isActive: _currentStep >= 1,
            state: _currentStep > 1 ? StepState.complete : StepState.indexed,
            content: Container(
              padding: AppSpacing.paddingAllBase,
              decoration: BoxDecoration(
                color: isDark ? AppColors.surfaceDark : AppColors.surfaceLight,
                borderRadius: AppRadius.borderMd,
                border: Border.all(color: isDark ? AppColors.borderDark : AppColors.borderLight),
              ),
              child: const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.shield_outlined, color: AppColors.success, size: 20),
                      SizedBox(width: 8),
                      Text('100% Breakage-Free Artisan Safe Transit', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                    ],
                  ),
                  SizedBox(height: 6),
                  Text(
                    'Fragile pottery and heritage handlooms are packed using biodegradable honeycomb cushioning directly at the artisan cluster.',
                    style: TextStyle(fontSize: 11, color: Colors.grey),
                  ),
                ],
              ),
            ),
          ),

          // Step 3: Payment
          Step(
            title: const Text('3. Secure Payment & Escrow'),
            subtitle: Text(_selectedPaymentMethod),
            isActive: _currentStep >= 2,
            state: StepState.indexed,
            content: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  padding: AppSpacing.paddingAllBase,
                  decoration: BoxDecoration(
                    color: AppColors.primaryContainer.withValues(alpha: 0.3),
                    borderRadius: AppRadius.borderMd,
                  ),
                  child: const Row(
                    children: [
                      Icon(Icons.lock_outline, color: AppColors.primary, size: 18),
                      SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          'KalaCart Artisan Escrow: Funds are held securely and released to the artisan once you receive and verify the authentic GI craft.',
                          style: TextStyle(fontSize: 11, fontWeight: FontWeight.w500),
                        ),
                      ),
                    ],
                  ),
                ),
                AppSpacing.gapV12,
                ...[
                  'UPI Escrow (Google Pay / PhonePe / Paytm)',
                  'Credit / Debit Card (Visa, Mastercard, RuPay)',
                  'Net Banking (All Indian Banks)',
                  'Direct Artisan Bank Wire (NEFT/RTGS for Wholesale)',
                ].map((method) {
                  final isSelected = _selectedPaymentMethod == method;
                  return InkWell(
                    onTap: () {
                      setState(() => _selectedPaymentMethod = method);
                    },
                    borderRadius: AppRadius.borderMd,
                    child: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      child: Row(
                        children: [
                          Icon(
                            isSelected ? Icons.radio_button_checked : Icons.radio_button_unchecked,
                            color: isSelected ? AppColors.primary : Colors.grey,
                            size: 20,
                          ),
                          AppSpacing.gapH12,
                          Expanded(
                            child: Text(
                              method,
                              style: TextStyle(
                                fontSize: 13,
                                fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
                                color: isSelected ? AppColors.primary : null,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  );
                }),
              ],
            ),
          ),
        ],
      ),
    );
  }

  void _showOrderSuccessDialog(BuildContext context, double amount) {
    ref.read(cartProvider.notifier).clearCart();

    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) {
        return AlertDialog(
          shape: const RoundedRectangleBorder(
            borderRadius: BorderRadius.all(Radius.circular(20)),
          ),
          title: const Column(
            children: [
              Icon(Icons.check_circle_rounded, color: AppColors.success, size: 54),
              SizedBox(height: 8),
              Text('Order Confirmed!'),
            ],
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'Thank you for empowering Indian Master Artisans directly.',
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
                    const Text('ORDER ID: KC-2026-99142', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                    const SizedBox(height: 4),
                    Text('Total Paid: ${CurrencyFormatter.formatINR(amount)}', style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary)),
                    const SizedBox(height: 4),
                    const Text('Digital Craft Passport generated.', style: TextStyle(fontSize: 11, color: AppColors.success)),
                  ],
                ),
              ),
            ],
          ),
          actions: [
            ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: AppColors.primary, foregroundColor: Colors.white),
              onPressed: () {
                Navigator.pop(context);
                context.go('/');
              },
              child: const Text('Back to Home'),
            ),
          ],
        );
      },
    );
  }
}
