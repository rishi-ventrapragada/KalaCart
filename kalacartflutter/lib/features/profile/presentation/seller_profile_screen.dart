import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../shared/services/user_role_service.dart';
import '../../seller/data/seller_repository.dart';

class SellerProfileScreen extends ConsumerWidget {
  const SellerProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final userRole = ref.watch(userRoleProvider);
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final storefrontConfig = ref.watch(storefrontConfigProvider);

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
          // Profile Header
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(3),
                decoration: const BoxDecoration(
                  color: AppColors.secondary,
                  shape: BoxShape.circle,
                ),
                child: const CircleAvatar(
                  radius: 36,
                  backgroundColor: Colors.white,
                  child: Text('🏺', style: TextStyle(fontSize: 32)),
                ),
              ),
              AppSpacing.gapH16,
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Flexible(
                          child: Text(
                            storefrontConfig.artisanName,
                            style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                          ),
                        ),
                        const SizedBox(width: 4),
                        const Icon(Icons.verified, color: AppColors.success, size: 18),
                      ],
                    ),
                    Text(
                      '${userRole.craftCluster} · ${userRole.region}',
                      style: TextStyle(fontSize: 12, color: isDark ? AppColors.textTertiaryDark : AppColors.textSecondaryLight),
                    ),
                    AppSpacing.gapV4,
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: const BoxDecoration(
                        color: AppColors.secondaryContainer,
                        borderRadius: AppRadius.borderXs,
                      ),
                      child: const Text('MASTER GUILD AWARDEE', style: TextStyle(color: AppColors.onSecondaryContainer, fontSize: 9, fontWeight: FontWeight.bold)),
                    ),
                  ],
                ),
              ),
            ],
          ),
          AppSpacing.gapV24,

          // GI Tag Verification Status Card
          Container(
            padding: AppSpacing.paddingAllBase,
            decoration: BoxDecoration(
              color: AppColors.successContainer.withValues(alpha: 0.3),
              borderRadius: AppRadius.borderMd,
              border: Border.all(color: AppColors.success),
            ),
            child: const Row(
              children: [
                Icon(Icons.verified_user, color: AppColors.success, size: 24),
                SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('GI Certified Master Guild Verified', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppColors.success)),
                      Text('Registration: GI/APPLICATION/NO/04 (Govt. of India)', style: TextStyle(fontSize: 11)),
                    ],
                  ),
                ),
              ],
            ),
          ),
          AppSpacing.gapV20,

          // Settings Section
          Text('Artisan Studio Management', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
          AppSpacing.gapV8,

          _buildSettingsTile(
            icon: Icons.storefront_outlined,
            title: 'Storefront Identity & Collections',
            subtitle: 'Banner, bio, featured crafts & share link',
            onTap: () => context.push('/store-settings'),
          ),
          _buildSettingsTile(
            icon: Icons.account_balance_outlined,
            title: 'Payout Bank Account (UPI/NEFT)',
            subtitle: 'State Bank of India · A/C Ending in 9941',
            onTap: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Direct Escrow Payout linked to verified artisan bank account.')),
              );
            },
          ),
          _buildSettingsTile(
            icon: Icons.translate,
            title: 'Artisan Primary Language',
            subtitle: 'Hindi (हिंदी) & English with AI Audio Translator',
            onTap: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Language preferences updated.')),
              );
            },
          ),
          _buildSettingsTile(
            icon: Icons.swap_horiz_rounded,
            title: 'Switch to Buyer Mode',
            subtitle: 'Browse & purchase authentic crafts from other clusters',
            onTap: () {
              ref.read(userRoleProvider.notifier).setRole(UserRole.buyer);
              context.go('/');
            },
          ),
          _buildSettingsTile(
            icon: Icons.logout,
            title: 'Log Out',
            subtitle: 'Sign out of KalaCart Artisan Studio',
            textColor: Colors.red,
            onTap: () => context.go('/login'),
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
