import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../auth/data/auth_repository.dart';
import '../../auth/data/supabase_auth_repository.dart';
import '../../auth/domain/user_model.dart';

class BuyerProfileScreen extends ConsumerWidget {
  const BuyerProfileScreen({super.key});

  Future<void> _switchToArtisan(BuildContext context, WidgetRef ref, UserModel user) async {
    if (!user.hasSellerProfile) {
      context.push('/artisan-onboarding');
      return;
    }
    try {
      await ref.read(authControllerProvider).setAccountType(UserAccountType.artisan);
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

    return Scaffold(
      appBar: AppBar(
        title: const Text('Buyer Profile & Preferences'),
        actions: [
          IconButton(
            icon: const Icon(Icons.edit_outlined),
            tooltip: 'Edit profile',
            onPressed: () => context.push('/buyer-onboarding'),
          ),
        ],
      ),
      body: ListView(
        padding: AppSpacing.paddingAllBase,
        children: [
          Row(
            children: [
              CircleAvatar(
                radius: 36,
                backgroundColor: AppColors.primaryContainer,
                child: Text(
                  user?.initials ?? '?',
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 24, color: AppColors.primary),
                ),
              ),
              AppSpacing.gapH16,
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(user?.fullName ?? 'Guest', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
                    Text(user?.email ?? '', style: const TextStyle(fontSize: 12, color: Colors.grey)),
                    if (user != null) ...[
                      AppSpacing.gapV4,
                      Row(
                        children: [
                          Icon(Icons.location_on_outlined, size: 14, color: theme.colorScheme.onSurface.withValues(alpha: 0.6)),
                          const SizedBox(width: 2),
                          Text(user.regionLabel, style: theme.textTheme.bodySmall),
                          AppSpacing.gapH8,
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            decoration: const BoxDecoration(
                              color: AppColors.primaryContainer,
                              borderRadius: AppRadius.borderXs,
                            ),
                            child: Text(
                              user.isEmailVerified ? 'VERIFIED BUYER' : 'EMAIL UNVERIFIED',
                              style: const TextStyle(color: AppColors.primary, fontSize: 9, fontWeight: FontWeight.bold),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),
          AppSpacing.gapV24,

          _buildSettingsTile(
            icon: Icons.shopping_bag_outlined,
            title: 'My Orders & Deliveries',
            subtitle: 'Track shipments and digital craft certificates',
            onTap: () => context.go('/orders'),
          ),
          _buildSettingsTile(
            icon: Icons.handshake_outlined,
            title: 'My Custom RFQ Bids',
            subtitle: 'View wholesale quotes and artisan proposals',
            onTap: () => context.go('/rfq'),
          ),
          _buildSettingsTile(
            icon: Icons.chat_bubble_outline,
            title: 'Artisan Messages & Studio Chat',
            subtitle: 'Conversations with master craft guilds',
            onTap: () => context.push('/chat'),
          ),
          _buildSettingsTile(
            icon: Icons.shopping_cart_outlined,
            title: 'My Cart',
            subtitle: 'Items waiting for checkout',
            onTap: () => context.push('/cart'),
          ),
          if (user != null)
            _buildSettingsTile(
              icon: Icons.swap_horiz_rounded,
              title: user.hasSellerProfile ? 'Switch to Artisan Seller Mode' : 'Become an Artisan Seller',
              subtitle: user.hasSellerProfile
                  ? 'Open your studio dashboard, catalog and RFQs'
                  : 'Set up a storefront and start listing crafts',
              onTap: () => _switchToArtisan(context, ref, user),
            ),
          _buildSettingsTile(
            icon: Icons.logout,
            title: 'Log Out',
            subtitle: 'Sign out of KalaCart',
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
