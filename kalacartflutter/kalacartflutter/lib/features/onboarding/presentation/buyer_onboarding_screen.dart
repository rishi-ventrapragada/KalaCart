import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_constants.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/widgets/app_button.dart';
import '../../../core/widgets/app_chip.dart';
import '../../auth/data/auth_repository.dart';
import '../../auth/data/supabase_auth_repository.dart';
import '../../auth/domain/user_model.dart';

class BuyerOnboardingScreen extends ConsumerStatefulWidget {
  const BuyerOnboardingScreen({super.key});

  @override
  ConsumerState<BuyerOnboardingScreen> createState() => _BuyerOnboardingScreenState();
}

class _BuyerOnboardingScreenState extends ConsumerState<BuyerOnboardingScreen> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _nameController;
  late final TextEditingController _locationController;
  late final TextEditingController _phoneController;
  String _selectedLanguage = 'English';
  final Set<String> _selectedCategories = {};
  final Set<String> _selectedInterests = {};
  bool _isLoading = false;

  static const List<String> _availableInterests = [
    'GI Tagged Originals',
    'Home Decor & Pottery',
    'Handloom & Sarees',
    'B2B Custom RFQs',
    'Direct Artisan Connect',
    'Rare Heritage Craft Stories',
  ];

  static const List<String> _languages = [
    'English',
    'Hindi (हिन्दी)',
    'Telugu (తెలుగు)',
    'Bengali (বাংলা)',
    'Tamil (தமிழ்)',
    'Marathi (मराठी)',
  ];

  @override
  void initState() {
    super.initState();
    final user = ref.read(currentUserProvider);
    _nameController = TextEditingController(text: user?.fullName ?? '');
    final loc = [user?.city, user?.state].where((s) => s != null && s.trim().isNotEmpty).join(', ');
    _locationController = TextEditingController(text: loc);
    _phoneController = TextEditingController(text: user?.phoneNumber ?? '');
  }

  @override
  void dispose() {
    _nameController.dispose();
    _locationController.dispose();
    _phoneController.dispose();
    super.dispose();
  }

  Future<void> _handleComplete() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;

    setState(() => _isLoading = true);
    try {
      final buyerData = BuyerProfileData(
        name: _nameController.text.trim(),
        preferredCraftCategories: _selectedCategories.toList(),
        interests: _selectedInterests.toList(),
        location: _locationController.text.trim(),
        preferredLanguage: _selectedLanguage,
        phone: _phoneController.text.trim().isEmpty ? null : _phoneController.text.trim(),
      );
      await ref.read(authControllerProvider).completeBuyer(buyerData);
      if (mounted) context.go('/');
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(authErrorMessage(e)),
            backgroundColor: AppColors.error,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Buyer Profile Setup'),
        actions: [
          TextButton(
            onPressed: () => ref.read(authControllerProvider).signOut(),
            child: const Text('Sign out'),
          ),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: AppSpacing.paddingAllXl,
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Personalize Your Craft Feed',
                  style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800),
                ),
                AppSpacing.gapV8,
                Text(
                  'Tell us your craft preferences so we can recommend verified regional artisan clusters.',
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
                  ),
                ),
                AppSpacing.gapV24,

                TextFormField(
                  controller: _nameController,
                  textCapitalization: TextCapitalization.words,
                  decoration: const InputDecoration(
                    labelText: 'Your Name / Company Name *',
                    prefixIcon: Icon(Icons.person_outline),
                  ),
                  validator: (v) => (v == null || v.trim().length < 2) ? 'Enter your name' : null,
                ),
                AppSpacing.gapV16,

                TextFormField(
                  controller: _locationController,
                  textCapitalization: TextCapitalization.words,
                  decoration: const InputDecoration(
                    labelText: 'City, State *',
                    hintText: 'e.g. Bengaluru, Karnataka',
                    prefixIcon: Icon(Icons.location_on_outlined),
                  ),
                  validator: (v) => (v == null || v.trim().isEmpty) ? 'Enter your city' : null,
                ),
                AppSpacing.gapV16,

                TextFormField(
                  controller: _phoneController,
                  keyboardType: TextInputType.phone,
                  decoration: const InputDecoration(
                    labelText: 'Phone (optional)',
                    prefixIcon: Icon(Icons.phone_outlined),
                  ),
                ),
                AppSpacing.gapV20,

                Text('Preferred Language', style: theme.textTheme.titleSmall),
                AppSpacing.gapV8,
                DropdownButtonFormField<String>(
                  initialValue: _selectedLanguage,
                  items: _languages.map((lang) => DropdownMenuItem(value: lang, child: Text(lang))).toList(),
                  onChanged: (val) => setState(() => _selectedLanguage = val ?? _selectedLanguage),
                  decoration: const InputDecoration(prefixIcon: Icon(Icons.translate_rounded)),
                ),
                AppSpacing.gapV24,

                Text('Select Handicraft Traditions of Interest', style: theme.textTheme.titleSmall),
                AppSpacing.gapV8,
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: AppConstants.craftCategories.where((c) => c != 'All Crafts').map((cat) {
                    final isSelected = _selectedCategories.contains(cat);
                    return AppChip(
                      label: cat,
                      isSelected: isSelected,
                      onSelected: (selected) {
                        setState(() {
                          if (selected) {
                            _selectedCategories.add(cat);
                          } else {
                            _selectedCategories.remove(cat);
                          }
                        });
                      },
                    );
                  }).toList(),
                ),
                AppSpacing.gapV24,

                Text('What are you looking to do?', style: theme.textTheme.titleSmall),
                AppSpacing.gapV8,
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: _availableInterests.map((interest) {
                    final isSelected = _selectedInterests.contains(interest);
                    return AppChip(
                      label: interest,
                      isSelected: isSelected,
                      onSelected: (selected) {
                        setState(() {
                          if (selected) {
                            _selectedInterests.add(interest);
                          } else {
                            _selectedInterests.remove(interest);
                          }
                        });
                      },
                    );
                  }).toList(),
                ),
                AppSpacing.gapV32,

                AppButton(
                  label: 'Complete Setup & Explore',
                  isLoading: _isLoading,
                  onPressed: _handleComplete,
                ),
                AppSpacing.gapV16,
              ],
            ),
          ),
        ),
      ),
    );
  }
}
