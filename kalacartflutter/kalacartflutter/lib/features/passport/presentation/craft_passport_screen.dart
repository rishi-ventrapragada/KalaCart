import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/widgets/app_card.dart';
import '../../../core/widgets/app_error_state.dart';
import '../../../core/widgets/app_image_placeholder.dart';
import '../../../core/widgets/app_loading_state.dart';
import '../../../shared/models/product.dart';
import '../../../shared/widgets/social_share_sheet.dart';
import '../../products/data/supabase_products_repository.dart';
import '../../seller/data/sellers_repository.dart';

/// Provenance certificate for a product. [passportId] is the PRODUCT id.
class CraftPassportScreen extends ConsumerWidget {
  final String passportId;

  const CraftPassportScreen({super.key, required this.passportId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final productAsync = ref.watch(productProvider(passportId));

    return productAsync.when(
      loading: () => Scaffold(
        appBar: AppBar(title: const Text('Craft Passport')),
        body: const AppLoadingState(message: 'Verifying provenance...'),
      ),
      error: (e, _) => Scaffold(
        appBar: AppBar(title: const Text('Craft Passport')),
        body: AppErrorState(
          message: 'Unable to load this passport right now.',
          onRetry: () => ref.invalidate(productProvider(passportId)),
        ),
      ),
      data: (product) {
        if (product == null) {
          return Scaffold(
            appBar: AppBar(title: const Text('Craft Passport')),
            body: AppErrorState(
              title: 'Passport not found',
              message: 'No craft matches this passport. It may have been removed.',
              retryLabel: 'Back to Discovery',
              onRetry: () => context.go('/discovery'),
            ),
          );
        }
        return _PassportBody(product: product);
      },
    );
  }
}

class _PassportBody extends ConsumerWidget {
  final Product product;

  const _PassportBody({required this.product});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final sellerAsync = ref.watch(sellerStorefrontProvider(product.sellerId));
    final seller = sellerAsync.valueOrNull;
    final isVerified = seller?.isVerified ?? false;
    final verificationKnown = sellerAsync.hasValue;
    final deepLink = 'https://kalacart.in/passport/${product.id}';
    final imageUrl = product.primaryImageUrl;

    return Scaffold(
      appBar: AppBar(
        title: const Row(
          children: [
            Icon(Icons.verified, color: AppColors.success, size: 20),
            AppSpacing.gapH8,
            Text('Craft Passport'),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.share_outlined),
            tooltip: 'Share Certificate',
            onPressed: () {
              SocialShareSheet.show(
                context,
                title: 'Craft Passport: ${product.title}',
                subtitle: '${product.artisanName} · ${product.region}',
                deepLink: deepLink,
                entityType: 'passport',
              );
            },
          ),
        ],
      ),
      body: ListView(
        padding: AppSpacing.paddingAllBase,
        children: [
          // Certificate Header Card
          Container(
            padding: AppSpacing.paddingAllLg,
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF0F381E), Color(0xFF1E5B33), Color(0xFF134224)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: AppRadius.borderLg,
              boxShadow: [
                BoxShadow(
                  color: Colors.green.withValues(alpha: 0.3),
                  blurRadius: 16,
                  offset: const Offset(0, 6),
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.2),
                        borderRadius: AppRadius.borderSm,
                      ),
                      child: const Row(
                        children: [
                          Icon(Icons.handshake_rounded, color: Colors.white, size: 12),
                          SizedBox(width: 4),
                          Text(
                            'HANDMADE PROVENANCE',
                            style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 0.5),
                          ),
                        ],
                      ),
                    ),
                    const Icon(Icons.shield_outlined, color: Colors.white70, size: 24),
                  ],
                ),
                AppSpacing.gapV16,
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    SizedBox(
                      width: 64,
                      height: 64,
                      child: ClipRRect(
                        borderRadius: AppRadius.borderSm,
                        child: imageUrl == null
                            ? const AppImagePlaceholder(icon: Icons.palette_outlined)
                            : Image.network(
                                imageUrl,
                                fit: BoxFit.cover,
                                errorBuilder: (_, __, ___) => const AppImagePlaceholder(icon: Icons.palette_outlined),
                              ),
                      ),
                    ),
                    AppSpacing.gapH12,
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            product.title,
                            style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
                          ),
                          AppSpacing.gapV6,
                          Text(
                            'Passport ID: ${product.passportCode}',
                            style: const TextStyle(
                              color: Colors.white70,
                              fontSize: 12,
                              fontFamily: 'monospace',
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                AppSpacing.gapV16,
                const Divider(color: Colors.white24, height: 1),
                AppSpacing.gapV12,
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Listed on', style: TextStyle(color: Colors.white60, fontSize: 10)),
                        Text(
                          DateFormat('d MMM yyyy').format(product.createdAt.toLocal()),
                          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 12),
                        ),
                      ],
                    ),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        const Text('Artisan status', style: TextStyle(color: Colors.white60, fontSize: 10)),
                        if (!verificationKnown)
                          const Text('Checking...', style: TextStyle(color: Colors.white70, fontSize: 12))
                        else
                          Text(
                            isVerified ? 'VERIFIED ARTISAN' : 'VERIFICATION PENDING',
                            style: TextStyle(
                              color: isVerified ? const Color(0xFF69F0AE) : const Color(0xFFFFE082),
                              fontWeight: FontWeight.bold,
                              fontSize: 12,
                            ),
                          ),
                      ],
                    ),
                  ],
                ),
              ],
            ),
          ),
          AppSpacing.gapV20,

          // Artisan Section
          AppCard(
            padding: AppSpacing.paddingAllBase,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.handyman_outlined, color: AppColors.primary, size: 20),
                    AppSpacing.gapH8,
                    Text('Artisan & Origin', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
                    const Spacer(),
                    if (product.sellerId.isNotEmpty)
                      TextButton(
                        onPressed: () => context.push('/artisan/${product.sellerId}'),
                        child: const Text('View studio'),
                      ),
                  ],
                ),
                AppSpacing.gapV12,
                _InfoRow(label: 'Studio', value: seller?.shopName ?? product.artisanName),
                _InfoRow(label: 'Artisan', value: seller?.artisanName ?? 'Not provided'),
                _InfoRow(
                  label: 'Craft Type',
                  value: (seller?.artisanType ?? product.sellerArtisanType ?? '').trim().isEmpty
                      ? 'Not provided'
                      : (seller?.artisanType ?? product.sellerArtisanType)!,
                ),
                _InfoRow(label: 'Region', value: product.region),
                if (seller?.experienceYears != null && seller!.experienceYears! > 0)
                  _InfoRow(label: 'Experience', value: '${seller.experienceYears} years'),
                if (sellerAsync.hasError)
                  Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: Text(
                      'Artisan profile could not be loaded.',
                      style: theme.textTheme.bodySmall?.copyWith(color: AppColors.error),
                    ),
                  ),
              ],
            ),
          ),
          AppSpacing.gapV16,

          // Craft Details
          AppCard(
            padding: AppSpacing.paddingAllBase,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.eco_outlined, color: AppColors.success, size: 20),
                    AppSpacing.gapH8,
                    Text('Craft Details', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
                  ],
                ),
                AppSpacing.gapV12,
                _InfoRow(label: 'Category', value: product.category),
                _InfoRow(label: 'Material', value: product.material.trim().isEmpty ? 'Not provided' : product.material),
                _InfoRow(label: 'Listed', value: DateFormat('d MMM yyyy').format(product.createdAt.toLocal())),
                _InfoRow(label: 'Listing Status', value: product.isPublished ? 'Published' : 'Not currently listed'),
                if (product.description.trim().isNotEmpty) ...[
                  AppSpacing.gapV8,
                  Text(
                    product.description,
                    style: theme.textTheme.bodySmall?.copyWith(
                      height: 1.4,
                      color: isDark ? AppColors.textSecondaryDark : AppColors.textSecondaryLight,
                    ),
                  ),
                ],
              ],
            ),
          ),
          AppSpacing.gapV20,

          // Passport code / QR
          Container(
            padding: AppSpacing.paddingAllBase,
            decoration: BoxDecoration(
              color: isDark ? AppColors.surfaceDark : Colors.white,
              borderRadius: AppRadius.borderMd,
              border: Border.all(color: isDark ? AppColors.borderDark : AppColors.borderLight),
            ),
            child: Column(
              children: [
                const Text('Passport Code', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                AppSpacing.gapV8,
                Container(
                  height: 140,
                  width: 140,
                  color: Colors.white,
                  child: const Center(
                    child: Icon(Icons.qr_code_2_rounded, size: 120, color: Colors.black87),
                  ),
                ),
                AppSpacing.gapV8,
                Text(
                  product.passportCode,
                  style: const TextStyle(
                    fontSize: 13,
                    color: AppColors.primary,
                    fontWeight: FontWeight.bold,
                    fontFamily: 'monospace',
                  ),
                ),
                AppSpacing.gapV4,
                Text(
                  deepLink,
                  style: const TextStyle(fontSize: 10, color: Colors.grey),
                  textAlign: TextAlign.center,
                ),
                AppSpacing.gapV12,
                OutlinedButton.icon(
                  style: OutlinedButton.styleFrom(shape: AppRadius.shapeMd),
                  icon: const Icon(Icons.copy, size: 16),
                  label: const Text('Copy passport link'),
                  onPressed: () async {
                    final messenger = ScaffoldMessenger.of(context);
                    await Clipboard.setData(ClipboardData(text: deepLink));
                    messenger.showSnackBar(
                      const SnackBar(
                        content: Text('Passport link copied to clipboard.'),
                        behavior: SnackBarBehavior.floating,
                      ),
                    );
                  },
                ),
              ],
            ),
          ),
          AppSpacing.gapV16,
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                foregroundColor: Colors.white,
                shape: AppRadius.shapeMd,
                padding: const EdgeInsets.symmetric(vertical: 12),
              ),
              icon: const Icon(Icons.shopping_bag_outlined, size: 18),
              label: const Text('View this craft', style: TextStyle(fontWeight: FontWeight.bold)),
              onPressed: () => context.push('/products/${product.id}'),
            ),
          ),
          AppSpacing.gapV32,
        ],
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  final String label;
  final String value;

  const _InfoRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(label, style: const TextStyle(fontSize: 11, color: Colors.grey, fontWeight: FontWeight.bold)),
          ),
          Expanded(
            child: Text(value, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
          ),
        ],
      ),
    );
  }
}
