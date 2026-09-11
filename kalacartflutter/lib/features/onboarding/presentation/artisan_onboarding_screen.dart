import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_constants.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/widgets/app_button.dart';
import '../../../core/widgets/app_chip.dart';
import '../../auth/data/auth_repository.dart';
import '../../auth/domain/user_model.dart';
import '../../../shared/services/user_role_service.dart';

class ArtisanOnboardingScreen extends ConsumerStatefulWidget {
  const ArtisanOnboardingScreen({super.key});

  @override
  ConsumerState<ArtisanOnboardingScreen> createState() => _ArtisanOnboardingScreenState();
}

class _ArtisanOnboardingScreenState extends ConsumerState<ArtisanOnboardingScreen> {
  final _artisanNameController = TextEditingController(text: 'Ustad Kripal Kumbh');
  final _storefrontNameController = TextEditingController(text: 'Kripal Jaipur Pottery Guild');
  final _villageLocationController = TextEditingController(text: 'Jaipur, Rajasthan');
  final _bioController = TextEditingController(
    text: 'Heritage master artisan producing handmade GI-tagged Blue Pottery crafted from quartz stone and natural mineral glazes.',
  );
  String _selectedCategory = 'Pottery & Terracotta';
  final Set<String> _selectedMaterials = {'Quartz Powder', 'Multani Mitti', 'Natural Mineral Glaze'};
  final Set<String> _selectedLanguages = {'Hindi', 'Rajasthani', 'English'};
  bool _isLoading = false;

  final List<String> _availableMaterials = [
    'Quartz Powder',
    'Natural Mineral Glaze',
    'Pure Mulberry Silk',
    'Brass & Bell Metal',
    'Teakwood & Rosewood',
    'Natural Vegetable Dyes',
    'Clay & Terracotta',
  ];

  final List<String> _availableLanguages = [
    'Hindi',
    'English',
    'Rajasthani',
    'Telugu',
    'Bengali',
    'Tamil',
    'Odia',
  ];

  @override
  void dispose() {
    _artisanNameController.dispose();
    _storefrontNameController.dispose();
    _villageLocationController.dispose();
    _bioController.dispose();
    super.dispose();
  }

  Future<void> _handleComplete() async {
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
      );
      await ref.read(authControllerProvider.notifier).completeArtisan(artisanData);
      ref.read(userRoleProvider.notifier).setRole(UserRole.artisanSeller);
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
        title: const Text('Artisan Studio Setup'),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: AppSpacing.paddingAllXl,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Set Up Your Artisan Storefront',
                style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800),
              ),
              AppSpacing.gapV8,
              Text(
                'This information appears on your digital craft passport, B2B RFQ bids & storefront catalog.',
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
                ),
              ),
              AppSpacing.gapV24,

              // Profile Avatar Placeholder
              Center(
                child: Stack(
                  children: [
                    Container(
                      width: 88,
                      height: 88,
                      decoration: BoxDecoration(
                        color: theme.colorScheme.primaryContainer,
                        shape: BoxShape.circle,
                        border: Border.all(color: AppColors.primary, width: 2),
                      ),
                      child: const Center(
                        child: Icon(Icons.person_rounded, size: 48, color: AppColors.primary),
                      ),
                    ),
                    Positioned(
                      bottom: 0,
                      right: 0,
                      child: Container(
                        padding: const EdgeInsets.all(6),
                        decoration: const BoxDecoration(
                          color: AppColors.primary,
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(Icons.camera_alt_rounded, color: Colors.white, size: 16),
                      ),
                    ),
                  ],
                ),
              ),
              AppSpacing.gapV24,

              TextField(
                controller: _artisanNameController,
                decoration: const InputDecoration(
                  labelText: 'Master Artisan / Guild Leader Name',
                  prefixIcon: Icon(Icons.person_outline),
                ),
              ),
              AppSpacing.gapV16,

              TextField(
                controller: _storefrontNameController,
                decoration: const InputDecoration(
                  labelText: 'Storefront / Collective Name',
                  prefixIcon: Icon(Icons.storefront_outlined),
                ),
              ),
              AppSpacing.gapV16,

              TextField(
                controller: _villageLocationController,
                decoration: const InputDecoration(
                  labelText: 'Village / Cluster Location, State',
                  prefixIcon: Icon(Icons.location_on_outlined),
                ),
              ),
              AppSpacing.gapV16,

              DropdownButtonFormField<String>(
                initialValue: _selectedCategory,
                items: AppConstants.craftCategories
                    .where((c) => c != 'All Crafts')
                    .map((cat) => DropdownMenuItem(value: cat, child: Text(cat)))
                    .toList(),
                onChanged: (val) => setState(() => _selectedCategory = val!),
                decoration: const InputDecoration(
                  labelText: 'Primary Craft Discipline',
                  prefixIcon: Icon(Icons.palette_outlined),
                ),
              ),
              AppSpacing.gapV16,

              TextField(
                controller: _bioController,
                maxLines: 3,
                decoration: const InputDecoration(
                  labelText: 'Artisan Story & Technique Bio',
                  alignLabelWithHint: true,
                ),
              ),
              AppSpacing.gapV20,

              Text('Raw Materials Used (for Craft Passport)', style: theme.textTheme.titleSmall),
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
                label: 'Launch Artisan Studio',
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
