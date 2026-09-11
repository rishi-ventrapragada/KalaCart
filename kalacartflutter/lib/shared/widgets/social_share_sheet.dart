import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';
import '../../core/constants/app_radius.dart';
import '../../core/constants/app_spacing.dart';

class SocialShareSheet extends StatelessWidget {
  final String title;
  final String deepLink;
  final String entityType; // 'product', 'store', 'live', 'passport'
  final String? subtitle;

  const SocialShareSheet({
    super.key,
    required this.title,
    required this.deepLink,
    required this.entityType,
    this.subtitle,
  });

  static void show(
    BuildContext context, {
    required String title,
    required String deepLink,
    required String entityType,
    String? subtitle,
  }) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (context) => SocialShareSheet(
        title: title,
        deepLink: deepLink,
        entityType: entityType,
        subtitle: subtitle,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    IconData headerIcon;
    Color iconColor;
    String badgeText;

    switch (entityType) {
      case 'passport':
        headerIcon = Icons.verified_outlined;
        iconColor = AppColors.success;
        badgeText = 'VERIFIED CRAFT PASSPORT';
        break;
      case 'live':
        headerIcon = Icons.sensors_rounded;
        iconColor = Colors.red;
        badgeText = 'LIVE ARTISAN WORKSHOP';
        break;
      case 'store':
        headerIcon = Icons.storefront_rounded;
        iconColor = AppColors.secondary;
        badgeText = 'MASTER ARTISAN STOREFRONT';
        break;
      case 'product':
      default:
        headerIcon = Icons.shopping_bag_outlined;
        iconColor = AppColors.primary;
        badgeText = 'GI HANDICRAFT';
        break;
    }

    return Padding(
      padding: AppSpacing.paddingAllLg,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: iconColor.withValues(alpha: 0.15),
                  borderRadius: AppRadius.borderSm,
                ),
                child: Row(
                  children: [
                    Icon(headerIcon, size: 14, color: iconColor),
                    const SizedBox(width: 4),
                    Text(
                      badgeText,
                      style: TextStyle(
                        color: iconColor,
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 0.5,
                      ),
                    ),
                  ],
                ),
              ),
              IconButton(
                icon: const Icon(Icons.close),
                onPressed: () => Navigator.pop(context),
              ),
            ],
          ),
          AppSpacing.gapV12,
          Text(
            title,
            style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
          if (subtitle != null) ...[
            AppSpacing.gapV4,
            Text(
              subtitle!,
              style: theme.textTheme.bodySmall?.copyWith(
                color: isDark ? AppColors.textSecondaryDark : AppColors.textSecondaryLight,
              ),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ],
          AppSpacing.gapV16,

          // Deep Link Box
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            decoration: BoxDecoration(
              color: isDark ? AppColors.surfaceDark : Colors.grey.shade100,
              borderRadius: AppRadius.borderMd,
              border: Border.all(
                color: isDark ? AppColors.borderDark : AppColors.borderLight,
              ),
            ),
            child: Row(
              children: [
                const Icon(Icons.link, size: 18, color: AppColors.primary),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    deepLink,
                    style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.copy, size: 18),
                  tooltip: 'Copy Link',
                  onPressed: () {
                    Navigator.pop(context);
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text('Deep link copied: $deepLink'),
                        behavior: SnackBarBehavior.floating,
                      ),
                    );
                  },
                ),
              ],
            ),
          ),
          AppSpacing.gapV20,

          // Social Channel Buttons
          Text('Share via', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
          AppSpacing.gapV12,
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildShareOption(
                context,
                icon: Icons.chat_bubble_outline,
                label: 'WhatsApp',
                color: const Color(0xFF25D366),
              ),
              _buildShareOption(
                context,
                icon: Icons.camera_alt_outlined,
                label: 'Instagram',
                color: const Color(0xFFE1306C),
              ),
              _buildShareOption(
                context,
                icon: Icons.send_outlined,
                label: 'Telegram',
                color: const Color(0xFF0088CC),
              ),
              _buildShareOption(
                context,
                icon: Icons.mail_outline,
                label: 'Email',
                color: Colors.orange,
              ),
              _buildShareOption(
                context,
                icon: Icons.qr_code_rounded,
                label: 'QR Code',
                color: Colors.indigo,
                onTap: () {
                  Navigator.pop(context);
                  _showQrDialog(context, deepLink, title);
                },
              ),
            ],
          ),
          AppSpacing.gapV20,
        ],
      ),
    );
  }

  static Widget _buildShareOption(
    BuildContext context, {
    required IconData icon,
    required String label,
    required Color color,
    VoidCallback? onTap,
  }) {
    return GestureDetector(
      onTap: onTap ??
          () {
            Navigator.pop(context);
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text('Opening $label to share craft link...'),
                behavior: SnackBarBehavior.floating,
              ),
            );
          },
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.15),
              shape: BoxShape.circle,
            ),
            child: Icon(icon, color: color, size: 24),
          ),
          const SizedBox(height: 6),
          Text(label, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }

  static void _showQrDialog(BuildContext context, String link, String title) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Scan QR Code for $title'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              height: 160,
              width: 160,
              color: Colors.white,
              child: const Center(
                child: Icon(Icons.qr_code_2_rounded, size: 140, color: Colors.black87),
              ),
            ),
            AppSpacing.gapV8,
            Text(link, style: const TextStyle(fontSize: 11, color: Colors.grey)),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Done')),
        ],
      ),
    );
  }
}
