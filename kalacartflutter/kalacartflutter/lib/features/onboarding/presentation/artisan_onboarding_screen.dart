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

class ArtisanOnboardingScreen extends ConsumerStatefulWidget {
  const ArtisanOnboardingScreen({super.key});

  @override
  ConsumerState<ArtisanOnboardingScreen> createState() => _ArtisanOnboardingScreenState();
}

class _ArtisanOnboardingScreenState extends ConsumerState<ArtisanOnboardingScreen> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _artisanNameController;
  late final TextEditingController _storefrontNameController;
  late final TextEditingController _villageLocationController;
  late final TextEditingController _bioController;
  late final TextEditingController _phoneController;
  late String _selectedCategory;
  final Set<String> _selectedMaterials = {};
  final Set<String> _selectedLanguages = {};
  bool _isLoading = false;

  static const List<String> _availableMaterials = [
    'Quartz Powder',
    'Multani Mitti',
    'Natural Mineral Glaze',
    'Pure Mulberry Silk',
    'Brass & Bell Metal',
    'Teakwood & Rosewood',
    'Natural Vegetable Dyes',
    'Clay & Terracotta',
  ];

  static const List<String> _availableLanguages = [
    'Hindi',
    'English',
    'Rajasthani',
    'Telugu',
    'Bengali',
    'Tamil',
    'Odia',
  ];

  List<String> get _categories => AppConstants.craftCategories.where((c) => c != 'All Crafts').toList();

  @override
  void initState() {
    super.initState();
    final user = ref.read(currentUserProvider);
    _artisanNameController = TextEditingController(text: user?.fullName ?? '');
    _storefrontNameController = TextEditingController(text: user?.shopName ?? '');
    final loc = user?.sellerLocation ??
        [user?.city, user?.state].where((s) => s != null && s.trim().isNotEmpty).join(', ');
    _villageLocationController = TextEditingController(text: loc);
    _bioController = TextEditingController(text: user?.bio ?? '');
    _phoneController = TextEditingController(text: user?.phoneNumber ?? '');
    _selectedCategory = _categories.contains(user?.artisanType) ? user!.artisanType! : _categories.first;
  }

  @override
  void dispose() {
    _artisanNameController.dispose();
    _storefrontNameController.dispose();
    _villageLocationController.dispose();
    _bioController.dispose();
    _phoneController.dispose();
    super.dispose();
  }

  Future<void> _handleComplete() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;

    setState(() => _isLoading = true);
    try {
      final artisanData = ArtisanProfileData(
        artisanName: _artisanNameController.text.trim(),
        storefrontName: _storefrontNameController.text.trim(),
        craftCategory: _selectedCategory,
        villageLocation: _villageLocationController.text.trim(),
        bio: _bioController.text.trim(),
        rawMaterials: _selectedMaterials.toList(),
        languages: _selectedLanguages.toList(),
        phone: _phoneController.text.trim().isEmpty ? null : _phoneController.text.trim(),
      );
      await ref.read(authControllerProvider).completeArtisan(artisanData);
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
    final user = ref.watch(currentUserProvider);
    final alreadyOnboarded = user?.isOnboarded ?? false;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Artisan Studio Setup'),
        actions: [
          if (!alreadyOnboarded)
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
                  'Set Up Your Artisan Storefront',
                  style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800),
                ),
                AppSpacing.gapV8,
                Text(
                  'This information appears on your storefront, B2B RFQ bids and product listings.',
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
                  ),
                ),
                AppSpacing.gapV24,

                Center(
                  child: Container(
                    width: 88,
                    height: 88,
                    decoration: BoxDecoration(
                      color: theme.colorScheme.primaryContainer,
                      shape: BoxShape.circle,
                      border: Border.all(color: AppColors.primary, width: 2),
                    ),
                    child: Center(
                      child: Text(
                        user?.initials ?? '?',
                        style: theme.textTheme.headlineMedium?.copyWith(
                          color: AppColors.primary,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ),
                  ),
                ),
                AppSpacing.gapV24,

                TextFormField(
                  controller: _artisanNameController,
                  textCapitalization: TextCapitalization.words,
                  decoration: const InputDecoration(
                    labelText: 'Master Artisan / Guild Leader Name *',
                    prefixIcon: Icon(Icons.person_outline),
                  ),
                  validator: (v) => (v == null || v.trim().length < 2) ? 'Enter your name' : null,
                ),
                AppSpacing.gapV16,

                TextFormField(
                  controller: _storefrontNameController,
                  textCapitalization: TextCapitalization.words,
                  decoration: const InputDecoration(
                    labelText: 'Storefront / Collective Name *',
                    prefixIcon: Icon(Icons.storefront_outlined),
                  ),
                  validator: (v) => (v == null || v.trim().length < 2) ? 'Enter your storefront name' : null,
                ),
                AppSpacing.gapV16,

                TextFormField(
                  controller: _villageLocationController,
                  textCapitalization: TextCapitalization.words,
                  decoration: const InputDecoration(
                    labelText: 'Village / Cluster, State *',
                    hintText: 'e.g. Jaipur, Rajasthan',
                    prefixIcon: Icon(Icons.location_on_outlined),
                  ),
                  validator: (v) => (v == null || v.trim().isEmpty) ? 'Enter your location' : null,
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
                AppSpacing.gapV16,

                DropdownButtonFormField<String>(
                  initialValue: _selectedCategory,
                  items: _categories.map((cat) => DropdownMenuItem(value: cat, child: Text(cat))).toList(),
                  onChanged: (val) => setState(() => _selectedCategory = val ?? _selectedCategory),
                  decoration: const InputDecoration(
                    labelText: 'Primary Craft Discipline',
                    prefixIcon: Icon(Icons.palette_outlined),
                  ),
                ),
                AppSpacing.gapV16,

                TextFormField(
                  controller: _bioController,
                  maxLines: 3,
                  textCapitalization: TextCapitalization.sentences,
                  decoration: const InputDecoration(
                    labelText: 'Artisan Story & Technique Bio *',
                    alignLabelWithHint: true,
                  ),
                  validator: (v) => (v == null || v.trim().length < 20) ? 'Tell buyers a little more (20+ characters)' : null,
                ),
                AppSpacing.gapV20,

                Text('Raw Materials Used', style: theme.textTheme.titleSmall),
                AppSpacing.gapV8,
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: _availableMaterials.map((mat) {
                    final isSelected = _selectedMaterials.contains(mat);
                    return AppChip(
                      label: mat,
                      isSelected: isSelected,
                      onSelected: (selected) {
                        setState(() {
                          if (selected) {
                            _selectedMaterials.add(mat);
                          } else {
                            _selectedMaterials.remove(mat);
                          }
                        });
                      },
                    );
                  }).toList(),
                ),
                AppSpacing.gapV20,

                Text('Spoken Languages', style: theme.textTheme.titleSmall),
                AppSpacing.gapV8,
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: _availableLanguages.map((lang) {
                    final isSelected = _selectedLanguages.contains(lang);
                    return AppChip(
                      label: lang,
                      isSelected: isSelected,
                      onSelected: (selected) {
                        setState(() {
                          if (selected) {
                            _selectedLanguages.add(lang);
                          } else {
                            _selectedLanguages.remove(lang);
                          }
                        });
                      },
                    );
                  }).toList(),
                ),
                AppSpacing.gapV32,

                AppButton(
                  label: alreadyOnboarded ? 'Save Storefront' : 'Launch Artisan Studio',
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
