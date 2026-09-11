import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../shared/services/user_role_service.dart';

class BuyerProfileScreen extends ConsumerWidget {
  const BuyerProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Buyer Profile & Preferences'),
      ),
      body: ListView(
        padding: AppSpacing.paddingAllBase,
        children: [
          // Profile Header
          Row(
            children: [
              const CircleAvatar(
                radius: 36,
                backgroundColor: AppColors.primaryContainer,
                child: Text('PS', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 24, color: AppColors.primary)),
              ),
              AppSpacing.gapH16,
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Priya Sundaram', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
                    const Text('priya.sundaram@heritagebuyer.in', style: TextStyle(fontSize: 12, color: Colors.grey)),
                    AppSpacing.gapV4,
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: const BoxDecoration(
                        color: AppColors.primaryContainer,
                        borderRadius: AppRadius.borderXs,
                      ),
                      child: const Text('VERIFIED BUYER', style: TextStyle(color: AppColors.primary, fontSize: 9, fontWeight: FontWeight.bold)),
                    ),
                  ],
                ),
              ),
            ],
          ),
          AppSpacing.gapV24,

          // Settings Options
          _buildSettingsTile(
            icon: Icons.shopping_bag_outlined,
            title: 'My Orders & Deliveries',
            subtitle: 'Track shipments and digital craft certificates',
            onTap: () => context.push('/orders'),
          ),
          _buildSettingsTile(
            icon: Icons.handshake_outlined,
            title: 'My Custom RFQ Bids',
            subtitle: 'View wholesale quotes and artisan proposals',
            onTap: () => context.push('/rfq'),
          ),
          _buildSettingsTile(
            icon: Icons.chat_bubble_outline,
            title: 'Artisan Messages & Studio Chat',
            subtitle: 'Conversations with master craft guilds',
            onTap: () => context.push('/chat'),
          ),
          _buildSettingsTile(
            icon: Icons.verified_outlined,
            title: 'Saved Craft Passports',
            subtitle: 'Provenance certificates for purchased items',
            onTap: () => context.push('/passport/GI-IN-RAJ-2026-BP-0941'),
          ),
          _buildSettingsTile(
            icon: Icons.swap_horiz_rounded,
            title: 'Switch to Artisan Seller Mode',
            subtitle: 'Access Artisan Studio, Catalog Studio AI, and RFQs',
            onTap: () {
              ref.read(userRoleProvider.notifier).setRole(UserRole.artisanSeller);
              context.go('/');
            },
          ),
          _buildSettingsTile(
            icon: Icons.logout,
            title: 'Log Out',
            subtitle: 'Sign out of KalaCart',
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
