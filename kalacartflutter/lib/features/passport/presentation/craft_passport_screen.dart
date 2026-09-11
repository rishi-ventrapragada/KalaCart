import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/widgets/app_card.dart';
import '../../../shared/widgets/social_share_sheet.dart';
import '../data/passport_repository.dart';

class CraftPassportScreen extends ConsumerStatefulWidget {
  final String passportId;

  const CraftPassportScreen({super.key, required this.passportId});

  @override
  ConsumerState<CraftPassportScreen> createState() => _CraftPassportScreenState();
}

class _CraftPassportScreenState extends ConsumerState<CraftPassportScreen> {
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final passport = ref.watch(singlePassportProvider(widget.passportId)) ?? mockPassportDatabase.first;

    return Scaffold(
      appBar: AppBar(
        title: const Row(
          children: [
            Icon(Icons.verified, color: AppColors.success, size: 20),
            AppSpacing.gapH8,
            Text('Digital Craft Passport'),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.qr_code_scanner_rounded),
            tooltip: 'Scan Passport QR Code',
            onPressed: () => _openQrScannerSimulator(context),
          ),
          IconButton(
            icon: const Icon(Icons.share_outlined),
            tooltip: 'Share Certificate',
            onPressed: () {
              SocialShareSheet.show(
                context,
                title: 'GI Digital Passport: ${passport.productTitle}',
                subtitle: '${passport.artisanName} · ${passport.village}, ${passport.state}',
                deepLink: 'https://kalacart.in/passport/${passport.passportId}',
                entityType: 'passport',
              );
            },
          ),
        ],
      ),
      body: ListView(
        padding: AppSpacing.paddingAllBase,
        children: [
          // Holographic Trust Header Certificate Card
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
                          Icon(Icons.verified_user, color: Colors.white, size: 12),
                          SizedBox(width: 4),
                          Text('AUTHENTIC GI CERTIFIED', style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 0.5)),
                        ],
                      ),
                    ),
                    const Icon(Icons.shield_outlined, color: Colors.white70, size: 24),
                  ],
                ),
                AppSpacing.gapV16,
                Text(
                  passport.productTitle,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                AppSpacing.gapV6,
                Text(
                  'Passport ID: ${passport.passportId}',
                  style: const TextStyle(color: Colors.white70, fontSize: 12, fontFamily: 'monospace', fontWeight: FontWeight.bold),
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
                        const Text('GI Registration #', style: TextStyle(color: Colors.white60, fontSize: 10)),
                        Text(passport.giRegistrationNumber, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 12)),
                      ],
                    ),
                    const Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text('Verification Status', style: TextStyle(color: Colors.white60, fontSize: 10)),
                        Text('VERIFIED & ACTIVE', style: TextStyle(color: Color(0xFF69F0AE), fontWeight: FontWeight.bold, fontSize: 12)),
                      ],
                    ),
                  ],
                ),
              ],
            ),
          ),
          AppSpacing.gapV20,

          // Master Artisan & Cluster Section
          AppCard(
            padding: AppSpacing.paddingAllBase,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.handyman_outlined, color: AppColors.primary, size: 20),
                    AppSpacing.gapH8,
                    Text('Artisan Guild & Provenance', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
                  ],
                ),
                AppSpacing.gapV12,
                _buildInfoRow('Master Artisan', passport.artisanName),
                _buildInfoRow('Artisan Guild', passport.guildName),
                _buildInfoRow('Village & District', '${passport.village}, ${passport.district}'),
                _buildInfoRow('State', passport.state),
                _buildInfoRow('Geo Coordinates', passport.geoCoordinates),
                _buildInfoRow('Raw Material Source', passport.rawMaterialProvenance),
              ],
            ),
          ),
          AppSpacing.gapV16,

          // Craft Technique & Sustainability Grade
          AppCard(
            padding: AppSpacing.paddingAllBase,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.eco_outlined, color: AppColors.success, size: 20),
                    AppSpacing.gapH8,
                    Text('Technique & Eco-Footprint', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
                  ],
                ),
                AppSpacing.gapV12,
                _buildInfoRow('Craft Category', passport.category),
                _buildInfoRow('Technique', passport.craftTechnique),
                _buildInfoRow('Material Composition', passport.materialComposition),
                _buildInfoRow('Handcrafting Hours', passport.handcraftDuration),
                _buildInfoRow('Sustainability Grade', passport.sustainabilityGrade),
                _buildInfoRow('Verification Date', passport.verificationDate),
              ],
            ),
          ),
          AppSpacing.gapV20,

          // Government GI Certificate Preview Placeholder
          AppCard(
            padding: AppSpacing.paddingAllBase,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text('Official GI Certificate', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: const BoxDecoration(
                        color: AppColors.successContainer,
                        borderRadius: AppRadius.borderXs,
                      ),
                      child: const Text('GOVT. OF INDIA CERTIFIED', style: TextStyle(color: AppColors.success, fontSize: 9, fontWeight: FontWeight.bold)),
                    ),
                  ],
                ),
                AppSpacing.gapV8,
                Container(
                  height: 120,
                  width: double.infinity,
                  decoration: BoxDecoration(
                    color: isDark ? AppColors.surfaceDark : Colors.grey.shade100,
                    borderRadius: AppRadius.borderMd,
                    border: Border.all(color: isDark ? AppColors.borderDark : AppColors.borderLight),
                  ),
                  child: Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.picture_as_pdf_outlined, color: Colors.red, size: 36),
                        AppSpacing.gapV4,
                        Text('GI Certificate PDF: ${passport.passportId}.pdf', style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                        const Text('Cryptographically Signed & Timestamped', style: TextStyle(fontSize: 10, color: Colors.grey)),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
          AppSpacing.gapV20,

          // Passport QR Code Box
          Container(
            padding: AppSpacing.paddingAllBase,
            decoration: BoxDecoration(
              color: isDark ? AppColors.surfaceDark : Colors.white,
              borderRadius: AppRadius.borderMd,
              border: Border.all(color: isDark ? AppColors.borderDark : AppColors.borderLight),
            ),
            child: Column(
              children: [
                const Text('Public Verification QR Code', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
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
                Text(passport.qrCodeData, style: const TextStyle(fontSize: 11, color: AppColors.primary, fontWeight: FontWeight.bold)),
                AppSpacing.gapV4,
                const Text('Scan with any standard smartphone camera to verify authentic craft provenance.', textAlign: TextAlign.center, style: TextStyle(fontSize: 10, color: Colors.grey)),
              ],
            ),
          ),
          AppSpacing.gapV32,
        ],
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 130,
            child: Text(label, style: const TextStyle(fontSize: 11, color: Colors.grey, fontWeight: FontWeight.bold)),
          ),
          Expanded(
            child: Text(value, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
          ),
        ],
      ),
    );
  }

  void _openQrScannerSimulator(BuildContext context) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (context) {
        return Padding(
          padding: AppSpacing.paddingAllLg,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Row(
                children: [
                  Icon(Icons.qr_code_scanner_rounded, color: AppColors.primary, size: 24),
                  SizedBox(width: 8),
                  Text('Craft Passport QR Scanner', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                ],
              ),
              AppSpacing.gapV16,
              Container(
                height: 160,
                width: 160,
                decoration: const BoxDecoration(
                  color: Colors.black,
                  borderRadius: AppRadius.borderMd,
                ),
                child: const Center(
                  child: Icon(Icons.filter_center_focus_rounded, size: 80, color: AppColors.primary),
                ),
              ),
              AppSpacing.gapV16,
              const Text('Point camera at handicraft tag QR code to verify GI certificate.'),
              AppSpacing.gapV16,
              Row(
                children: [
                  Expanded(
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(backgroundColor: AppColors.success, foregroundColor: Colors.white),
                      onPressed: () {
                        Navigator.pop(context);
                        _showVerificationResultModal(context, success: true);
                      },
                      child: const Text('Simulate Valid Scan'),
                    ),
                  ),
                  AppSpacing.gapH12,
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () {
                        Navigator.pop(context);
                        _showVerificationResultModal(context, success: false);
                      },
                      child: const Text('Simulate Fake Tag'),
                    ),
                  ),
                ],
              ),
            ],
          ),
        );
      },
    );
  }

  void _showVerificationResultModal(BuildContext context, {required bool success}) {
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: Row(
            children: [
              Icon(
                success ? Icons.verified_rounded : Icons.warning_amber_rounded,
                color: success ? AppColors.success : Colors.red,
              ),
              const SizedBox(width: 8),
              Text(success ? 'GI Verification Verified!' : 'Unregistered Craft Tag!'),
            ],
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                success
                    ? '100% Genuine GI Tagged Handicraft from Jaipur Blue Pottery Cluster. Verified on Govt. Registry.'
                    : 'Warning: This QR code is not registered in the KalaCart GI Registry database. Be cautious of machine-made counterfeits.',
                style: const TextStyle(fontSize: 13, height: 1.35),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Close'),
            ),
          ],
        );
      },
    );
  }
}
