import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_constants.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/widgets/app_button.dart';
import '../../../core/widgets/app_empty_state.dart';
import '../../auth/data/auth_repository.dart';
import '../../auth/data/supabase_auth_repository.dart';
import '../../seller/data/sellers_repository.dart';

class SellerStorefrontSettingsScreen extends ConsumerStatefulWidget {
  const SellerStorefrontSettingsScreen({super.key});

  @override
  ConsumerState<SellerStorefrontSettingsScreen> createState() => _SellerStorefrontSettingsScreenState();
}

class _SellerStorefrontSettingsScreenState extends ConsumerState<SellerStorefrontSettingsScreen> {
  final _formKey = GlobalKey<FormState>();
  final _shopNameController = TextEditingController();
  final _bioController = TextEditingController();
  final _locationController = TextEditingController();
  final _experienceController = TextEditingController();

  String? _artisanType;
  bool _isSaving = false;

  List<String> get _categoryOptions => AppConstants.craftCategories.skip(1).toList();

  @override
  void initState() {
    super.initState();
    final user = ref.read(currentUserProvider);
    _shopNameController.text = user?.shopName ?? '';
    _bioController.text = user?.bio ?? '';
    _locationController.text = (user?.sellerLocation ?? '').trim().isNotEmpty
        ? user!.sellerLocation!.trim()
        : [user?.city, user?.state].where((s) => (s ?? '').trim().isNotEmpty).join(', ');
    final type = user?.artisanType;
    _artisanType = type != null && _categoryOptions.contains(type) ? type : null;
  }

  @override
  void dispose() {
    _shopNameController.dispose();
    _bioController.dispose();
    _locationController.dispose();
    _experienceController.dispose();
    super.dispose();
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

  Future<void> _copyShareLink(String sellerId) async {
    await Clipboard.setData(ClipboardData(text: 'https://kalacart.in/artisan/$sellerId'));
    _showSnack('Storefront link copied to clipboard.');
  }

  Future<void> _save(String sellerId) async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    final experienceText = _experienceController.text.trim();
    final experienceYears = experienceText.isEmpty ? null : int.tryParse(experienceText);

    setState(() => _isSaving = true);
    try {
      await ref.read(sellersRepositoryProvider).updateStorefront(
            sellerId: sellerId,
            shopName: _shopNameController.text.trim(),
            artisanType: _artisanType!,
            bio: _bioController.text.trim(),
            location: _locationController.text.trim(),
            experienceYears: experienceYears,
          );
      await ref.read(authControllerProvider).refresh();
      if (!mounted) return;
      _showSnack('Storefront settings saved.');
      context.pop();
    } catch (e) {
      _showSnack(authErrorMessage(e), isError: true);
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final user = ref.watch(currentUserProvider);
    final sellerId = user?.sellerId;

    if (user != null && sellerId == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Storefront Settings')),
        body: AppEmptyState(
          icon: Icons.storefront_outlined,
          title: 'Complete your artisan storefront first',
          message: 'Once your storefront exists you can edit its name, craft type, story and location here.',
          actionLabel: 'Set up storefront',
          onAction: () => context.push('/artisan-onboarding'),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Storefront Settings'),
        actions: [
          IconButton(
            icon: const Icon(Icons.share_outlined),
            tooltip: 'Copy store link',
            onPressed: sellerId == null ? null : () => _copyShareLink(sellerId),
          ),
          IconButton(
            icon: const Icon(Icons.remove_red_eye_outlined),
            tooltip: 'Preview storefront',
            onPressed: sellerId == null ? null : () => context.push('/artisan/$sellerId'),
          ),
        ],
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: AppSpacing.paddingAllBase,
          children: [
            // Identity header (real data only)
            Container(
              padding: AppSpacing.paddingAllBase,
              decoration: BoxDecoration(
                color: isDark ? AppColors.surfaceDark : AppColors.surfaceLight,
                borderRadius: AppRadius.borderMd,
                border: Border.all(color: isDark ? AppColors.borderDark : AppColors.borderLight),
              ),
              child: Row(
                children: [
                  CircleAvatar(
                    radius: 28,
                    backgroundColor: AppColors.primary,
                    child: Text(
                      user?.initials ?? '?',
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 18),
                    ),
                  ),
                  AppSpacing.gapH12,
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          user?.fullName ?? 'Artisan',
                          style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        Text(
                          user?.email ?? '',
                          style: theme.textTheme.bodySmall,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        if (sellerId != null) ...[
                          AppSpacing.gapV4,
                          Text(
                            'kalacart.in/artisan/$sellerId',
                            style: theme.textTheme.bodySmall?.copyWith(fontSize: 11, color: AppColors.primary),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ],
                      ],
                    ),
                  ),
                ],
              ),
            ),
            AppSpacing.gapV20,

            TextFormField(
              controller: _shopNameController,
              textInputAction: TextInputAction.next,
              decoration: const InputDecoration(labelText: 'Storefront name *', prefixIcon: Icon(Icons.storefront)),
              validator: (v) {
                if (v == null || v.trim().isEmpty) return 'Storefront name is required';
                if (v.trim().length < 3) return 'Use at least 3 characters';
                return null;
              },
            ),
            AppSpacing.gapV12,

            DropdownButtonFormField<String>(
              initialValue: _artisanType,
              decoration: const InputDecoration(labelText: 'Craft type *', prefixIcon: Icon(Icons.brush_outlined)),
              items: _categoryOptions.map((c) => DropdownMenuItem(value: c, child: Text(c))).toList(),
              onChanged: _isSaving ? null : (v) => setState(() => _artisanType = v),
              validator: (v) => v == null ? 'Pick your primary craft' : null,
            ),
            AppSpacing.gapV12,

            TextFormField(
              controller: _locationController,
              textInputAction: TextInputAction.next,
              decoration: const InputDecoration(
                labelText: 'Village / City, State *',
                hintText: 'e.g. Kot Jewar, Rajasthan',
                prefixIcon: Icon(Icons.location_on_outlined),
              ),
              validator: (v) => (v == null || v.trim().isEmpty) ? 'Location is required' : null,
            ),
            AppSpacing.gapV12,

            TextFormField(
              controller: _experienceController,
              keyboardType: TextInputType.number,
              textInputAction: TextInputAction.next,
              decoration: const InputDecoration(
                labelText: 'Years of experience (optional)',
                prefixIcon: Icon(Icons.timeline_outlined),
              ),
              validator: (v) {
                if (v == null || v.trim().isEmpty) return null;
                final parsed = int.tryParse(v.trim());
                if (parsed == null || parsed < 0 || parsed > 100) return 'Enter a number between 0 and 100';
                return null;
              },
            ),
            AppSpacing.gapV12,

            TextFormField(
              controller: _bioController,
              maxLines: 4,
              maxLength: 600,
              decoration: const InputDecoration(
                labelText: 'Artisan story & heritage *',
                hintText: 'Tell buyers about your craft tradition, techniques and materials.',
                alignLabelWithHint: true,
              ),
              validator: (v) {
                if (v == null || v.trim().isEmpty) return 'A short story helps buyers trust your work';
                if (v.trim().length < 20) return 'Add a little more detail (at least 20 characters)';
                return null;
              },
            ),
            AppSpacing.gapV24,

            AppButton(
              label: 'Save Storefront Settings',
              icon: Icons.save_outlined,
              isLoading: _isSaving,
              onPressed: sellerId == null ? null : () => _save(sellerId),
            ),
            AppSpacing.gapV12,
            AppButton(
              label: 'Preview public storefront',
              icon: Icons.remove_red_eye_outlined,
              variant: AppButtonVariant.outline,
              onPressed: sellerId == null || _isSaving ? null : () => context.push('/artisan/$sellerId'),
            ),
            AppSpacing.gapV32,
          ],
        ),
      ),
    );
  }
}
