import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_constants.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/widgets/app_button.dart';
import '../../../core/widgets/app_chip.dart';
import '../../auth/data/auth_repository.dart';
import '../../auth/domain/user_model.dart';
import '../../../shared/services/user_role_service.dart';

class BuyerOnboardingScreen extends ConsumerStatefulWidget {
  const BuyerOnboardingScreen({super.key});

  @override
  ConsumerState<BuyerOnboardingScreen> createState() => _BuyerOnboardingScreenState();
}

class _BuyerOnboardingScreenState extends ConsumerState<BuyerOnboardingScreen> {
  final _nameController = TextEditingController(text: 'Aditya Explorer');
  final _locationController = TextEditingController(text: 'Bangalore, Karnataka');
  String _selectedLanguage = 'English';
  final Set<String> _selectedCategories = {'Handloom & Textiles', 'Pottery & Terracotta'};
  final Set<String> _selectedInterests = {'B2B Custom RFQs', 'GI Tagged Originals', 'Direct Artisan Connect'};
  bool _isLoading = false;

  final List<String> _availableInterests = [
    'GI Tagged Originals',
    'Home Decor & Pottery',
    'Handloom & Sarees',
    'B2B Custom RFQs',
    'Direct Artisan Connect',
    'Rare Heritage Craft Stories',
  ];

  final List<String> _languages = [
    'English',
    'Hindi (हिन्दी)',
    'Telugu (తెలుగు)',
    'Bengali (বাংলা)',
    'Tamil (தமிழ்)',
    'Marathi (मराठी)',
  ];

  @override
  void dispose() {
    _nameController.dispose();
    _locationController.dispose();
    super.dispose();
  }

  Future<void> _handleComplete() async {
    setState(() => _isLoading = true);
    try {
      final buyerData = BuyerProfileData(
        name: _nameController.text.trim(),
        preferredCraftCategories: _selectedCategories.toList(),
        interests: _selectedInterests.toList(),
        location: _locationController.text.trim(),
        preferredLanguage: _selectedLanguage,
      );
      await ref.read(authControllerProvider.notifier).completeBuyer(buyerData);
      ref.read(userRoleProvider.notifier).setRole(UserRole.buyer);
      if (mounted) {
        context.go('/');
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Buyer Profile Setup'),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: AppSpacing.paddingAllXl,
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

              TextField(
                controller: _nameController,
                decoration: const InputDecoration(
                  labelText: 'Your Name / Company Name',
                  prefixIcon: Icon(Icons.person_outline),
                ),
              ),
              AppSpacing.gapV16,

              TextField(
                controller: _locationController,
                decoration: const InputDecoration(
                  labelText: 'City / Region',
                  prefixIcon: Icon(Icons.location_on_outlined),
                ),
              ),
              AppSpacing.gapV20,

              Text('Preferred Language', style: theme.textTheme.titleSmall),
              AppSpacing.gapV8,
              DropdownButtonFormField<String>(
                initialValue: _selectedLanguage,
                items: _languages.map((lang) => DropdownMenuItem(value: lang, child: Text(lang))).toList(),
                onChanged: (val) => setState(() => _selectedLanguage = val!),
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
    );
  }
}
