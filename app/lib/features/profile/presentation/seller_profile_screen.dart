import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../auth/data/auth_repository.dart';
import '../../auth/data/supabase_auth_repository.dart';
import '../../auth/domain/user_model.dart';

class SellerProfileScreen extends ConsumerWidget {
  const SellerProfileScreen({super.key});

  Future<void> _switchToBuyer(BuildContext context, WidgetRef ref) async {
    try {
      await ref.read(authControllerProvider).setAccountType(UserAccountType.buyer);
      if (context.mounted) context.go('/');
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(authErrorMessage(e)), backgroundColor: AppColors.error),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(currentUserProvider);
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    final shopName = user?.shopName ?? 'Artisan Studio';
    final location = (user?.sellerLocation?.trim().isNotEmpty ?? false) ? user!.sellerLocation!.trim() : (user?.regionLabel ?? 'India');
    final craft = user?.artisanType ?? 'Handicrafts';

    return Scaffold(
      appBar: AppBar(
        title: const Text('Artisan Guild Profile & Settings'),
        actions: [
          IconButton(
            icon: const Icon(Icons.edit_outlined),
            tooltip: 'Edit Storefront',
            onPressed: () => context.push('/store-settings'),
          ),
        ],
      ),
      body: ListView(
        padding: AppSpacing.paddingAllBase,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(3),
                decoration: const BoxDecoration(
                  color: AppColors.secondary,
                  shape: BoxShape.circle,
                ),
                child: CircleAvatar(
                  radius: 36,
                  backgroundColor: Colors.white,
                  child: Text(
                    user?.initials ?? '?',
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 24, color: AppColors.secondary),
                  ),
                ),
              ),
              AppSpacing.gapH16,
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      shopName,
                      style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                    ),
                    Text(
                      '${user?.fullName ?? ''} · $location',
                      style: TextStyle(fontSize: 12, color: isDark ? AppColors.textTertiaryDark : AppColors.textSecondaryLight),
                    ),
                    AppSpacing.gapV4,
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: const BoxDecoration(
                        color: AppColors.secondaryContainer,
                        borderRadius: AppRadius.borderXs,
                      ),
                      child: Text(
                        craft.toUpperCase(),
                        style: const TextStyle(color: AppColors.onSecondaryContainer, fontSize: 9, fontWeight: FontWeight.bold),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          AppSpacing.gapV24,

          if ((user?.bio ?? '').trim().isNotEmpty)
            Container(
              padding: AppSpacing.paddingAllBase,
              decoration: BoxDecoration(
                color: AppColors.secondaryContainer.withValues(alpha: isDark ? 0.15 : 0.3),
                borderRadius: AppRadius.borderMd,
              ),
              child: Text(user!.bio!, style: theme.textTheme.bodySmall?.copyWith(height: 1.5)),
            ),
          AppSpacing.gapV20,

          Text('Artisan Studio Management', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
          AppSpacing.gapV8,

          _buildSettingsTile(
            icon: Icons.storefront_outlined,
            title: 'Storefront Identity & Collections',
            subtitle: 'Store name, bio, craft discipline & location',
            onTap: () => context.push('/store-settings'),
          ),
          _buildSettingsTile(
            icon: Icons.inventory_2_outlined,
            title: 'My Catalog & Inventory',
            subtitle: 'Products, stock and pricing',
            onTap: () => context.go('/catalog-studio'),
          ),
          _buildSettingsTile(
            icon: Icons.receipt_long_outlined,
            title: 'Orders to Fulfil',
            subtitle: 'Accept, pack and dispatch buyer orders',
            onTap: () => context.go('/orders'),
          ),
          _buildSettingsTile(
            icon: Icons.chat_bubble_outline,
            title: 'Buyer Messages',
            subtitle: 'Conversations with buyers about their enquiries',
            onTap: () => context.push('/chat'),
          ),
          _buildSettingsTile(
            icon: Icons.swap_horiz_rounded,
            title: 'Switch to Buyer Mode',
            subtitle: 'Browse & purchase authentic crafts from other clusters',
            onTap: () => _switchToBuyer(context, ref),
          ),
          _buildSettingsTile(
            icon: Icons.logout,
            title: 'Log Out',
            subtitle: 'Sign out of KalaCart Artisan Studio',
            textColor: Colors.red,
            onTap: () async {
              await ref.read(authControllerProvider).signOut();
              if (context.mounted) context.go('/welcome');
            },
          ),
          AppSpacing.gapV32,
        ],
      ),
    );
  }

  Widget _buildSettingsTile({
    required IconData icon,
    required String title,
    required String subtitle,
    required VoidCallback onTap,
    Color? textColor,
  }) {
    return ListTile(
      leading: Icon(icon, color: textColor ?? AppColors.primary),
      title: Text(title, style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13, color: textColor)),
      subtitle: Text(subtitle, style: const TextStyle(fontSize: 11, color: Colors.grey)),
      trailing: const Icon(Icons.chevron_right, size: 18, color: Colors.grey),
      onTap: onTap,
    );
  }
}
