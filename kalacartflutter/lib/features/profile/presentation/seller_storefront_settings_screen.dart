import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../shared/widgets/social_share_sheet.dart';
import '../../seller/data/seller_repository.dart';

class SellerStorefrontSettingsScreen extends ConsumerStatefulWidget {
  const SellerStorefrontSettingsScreen({super.key});

  @override
  ConsumerState<SellerStorefrontSettingsScreen> createState() => _SellerStorefrontSettingsScreenState();
}

class _SellerStorefrontSettingsScreenState extends ConsumerState<SellerStorefrontSettingsScreen> {
  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _artisanNameController = TextEditingController();
  final TextEditingController _taglineController = TextEditingController();
  final TextEditingController _bioController = TextEditingController();
  final TextEditingController _newCollectionController = TextEditingController();

  @override
  void initState() {
    super.initState();
    final config = ref.read(storefrontConfigProvider);
    _nameController.text = config.storeName;
    _artisanNameController.text = config.artisanName;
    _taglineController.text = config.tagline;
    _bioController.text = config.bio;
  }

  @override
  void dispose() {
    _nameController.dispose();
    _artisanNameController.dispose();
    _taglineController.dispose();
    _bioController.dispose();
    _newCollectionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final config = ref.watch(storefrontConfigProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Storefront Studio Settings'),
        actions: [
          IconButton(
            icon: const Icon(Icons.share_outlined),
            tooltip: 'Share Store Link',
            onPressed: () {
              SocialShareSheet.show(
                context,
                title: config.storeName,
                subtitle: '${config.clusterRegion}, ${config.state}',
                deepLink: config.shareUrl,
                entityType: 'store',
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.remove_red_eye_outlined),
            tooltip: 'Preview Storefront',
            onPressed: () => context.push('/store/kripal-kumbh-jaipur'),
          ),
        ],
      ),
      body: ListView(
        padding: AppSpacing.paddingAllBase,
        children: [
          // Banner Customization Card
          Container(
            height: 140,
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: [Color(0xFF0D47A1), Color(0xFF1976D2), Color(0xFF00838F)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: AppRadius.borderMd,
            ),
            child: Center(
              child: ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.white,
                  foregroundColor: Colors.black87,
                ),
                icon: const Icon(Icons.camera_alt_outlined, size: 16),
                label: const Text('Change Store Banner'),
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Banner image selector opened.')),
                  );
                },
              ),
            ),
          ),
          AppSpacing.gapV16,

          // Profile Image Picker
          Center(
            child: Stack(
              children: [
                const CircleAvatar(
                  radius: 40,
                  backgroundColor: AppColors.primary,
                  child: Text('🏺', style: TextStyle(fontSize: 36)),
                ),
                Positioned(
                  bottom: 0,
                  right: 0,
                  child: Container(
                    padding: const EdgeInsets.all(6),
                    decoration: const BoxDecoration(
                      color: AppColors.secondary,
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.edit, size: 14, color: Colors.white),
                  ),
                ),
              ],
            ),
          ),
          AppSpacing.gapV20,

          // Text Fields
          TextField(
            controller: _nameController,
            decoration: const InputDecoration(labelText: 'Storefront Name *', prefixIcon: Icon(Icons.storefront)),
          ),
          AppSpacing.gapV12,

          TextField(
            controller: _artisanNameController,
            decoration: const InputDecoration(labelText: 'Master Artisan / Guild Leader Name *', prefixIcon: Icon(Icons.person_outline)),
          ),
          AppSpacing.gapV12,

          TextField(
            controller: _taglineController,
            decoration: const InputDecoration(labelText: 'Tagline *', prefixIcon: Icon(Icons.short_text)),
          ),
          AppSpacing.gapV12,

          TextField(
            controller: _bioController,
            maxLines: 3,
            decoration: const InputDecoration(labelText: 'Artisan Bio & Heritage Narrative *', alignLabelWithHint: true),
          ),
          AppSpacing.gapV20,

          // Collections Management
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Store Collections (${config.collections.length})', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
              TextButton.icon(
                icon: const Icon(Icons.add, size: 16),
                label: const Text('Add Collection'),
                onPressed: () => _showAddCollectionDialog(context),
              ),
            ],
          ),
          AppSpacing.gapV8,
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: config.collections.map((col) {
              return Chip(
                label: Text(col, style: const TextStyle(fontSize: 12)),
                deleteIcon: const Icon(Icons.close, size: 14),
                onDeleted: () {
                  ref.read(storefrontConfigProvider.notifier).removeCollection(col);
                },
              );
            }).toList(),
          ),
          AppSpacing.gapV24,

          // Save Changes
          SizedBox(
            height: 48,
            child: ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                foregroundColor: Colors.white,
                shape: AppRadius.shapeMd,
              ),
              onPressed: () {
                final updated = config.copyWith(
                  storeName: _nameController.text,
                  artisanName: _artisanNameController.text,
                  tagline: _taglineController.text,
                  bio: _bioController.text,
                );
                ref.read(storefrontConfigProvider.notifier).updateConfig(updated);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('🎉 Storefront settings saved!')),
                );
                context.pop();
              },
              child: const Text('Save Storefront Settings', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
            ),
          ),
          AppSpacing.gapV32,
        ],
      ),
    );
  }

  void _showAddCollectionDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Create New Collection'),
          content: TextField(
            controller: _newCollectionController,
            decoration: const InputDecoration(hintText: 'e.g. Festive Brass Bells 2026'),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
            ElevatedButton(
              onPressed: () {
                if (_newCollectionController.text.trim().isNotEmpty) {
                  ref.read(storefrontConfigProvider.notifier).addCollection(_newCollectionController.text.trim());
                  _newCollectionController.clear();
                }
                Navigator.pop(context);
              },
              child: const Text('Add'),
            ),
          ],
        );
      },
    );
  }
}
