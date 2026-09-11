import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/widgets/app_button.dart';
import '../../../core/widgets/app_card.dart';
import '../../auth/domain/user_model.dart';

class ChooseAccountTypeScreen extends StatefulWidget {
  const ChooseAccountTypeScreen({super.key});

  @override
  State<ChooseAccountTypeScreen> createState() => _ChooseAccountTypeScreenState();
}

class _ChooseAccountTypeScreenState extends State<ChooseAccountTypeScreen> {
  UserAccountType _selectedType = UserAccountType.buyer;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Account Type'),
      ),
      body: SafeArea(
        child: Padding(
          padding: AppSpacing.paddingAllXl,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'How will you use KalaCart?',
                style: theme.textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w800),
              ),
              AppSpacing.gapV8,
              Text(
                'Choose how you want to experience the platform. You can switch later from your profile.',
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
                ),
              ),
              AppSpacing.gapV32,

              AppCard(
                padding: AppSpacing.paddingAllLg,
                backgroundColor: _selectedType == UserAccountType.buyer
                    ? theme.colorScheme.primaryContainer.withValues(alpha: 0.3)
                    : null,
                onTap: () => setState(() => _selectedType = UserAccountType.buyer),
                child: Row(
                  children: [
                    Container(
                      padding: AppSpacing.paddingAllBase,
                      decoration: const BoxDecoration(
                        color: AppColors.primaryContainer,
                        borderRadius: AppRadius.borderMd,
                      ),
                      child: const Icon(Icons.shopping_bag_outlined, color: AppColors.primary, size: 28),
                    ),
                    AppSpacing.gapH16,
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('I am a Buyer / Collector', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                          AppSpacing.gapV4,
                          Text('Discover GI-tagged crafts, request custom quotes (RFQ), buy authentic handlooms & decor.', style: theme.textTheme.bodySmall),
                        ],
                      ),
                    ),
                    Icon(
                      _selectedType == UserAccountType.buyer ? Icons.radio_button_checked : Icons.radio_button_off,
                      color: theme.colorScheme.primary,
                    ),
                  ],
                ),
              ),

              AppSpacing.gapV16,

              AppCard(
                padding: AppSpacing.paddingAllLg,
                backgroundColor: _selectedType == UserAccountType.artisan
                    ? AppColors.secondaryContainer.withValues(alpha: 0.35)
                    : null,
                onTap: () => setState(() => _selectedType = UserAccountType.artisan),
                child: Row(
                  children: [
                    Container(
                      padding: AppSpacing.paddingAllBase,
                      decoration: const BoxDecoration(
                        color: AppColors.secondaryContainer,
                        borderRadius: AppRadius.borderMd,
                      ),
                      child: const Icon(Icons.handyman_outlined, color: AppColors.secondary, size: 28),
                    ),
                    AppSpacing.gapH16,
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('I am an Artisan / Weaver / Guild', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                          AppSpacing.gapV4,
                          Text('Catalog your crafts, respond to B2B batch RFQs & sell direct.', style: theme.textTheme.bodySmall),
                        ],
                      ),
                    ),
                    Icon(
                      _selectedType == UserAccountType.artisan ? Icons.radio_button_checked : Icons.radio_button_off,
                      color: AppColors.secondary,
                    ),
                  ],
                ),
              ),

              const Spacer(),

              AppButton(
                label: 'Continue',
                onPressed: () => context.push('/signup?type=${_selectedType.name}'),
              ),
              AppSpacing.gapV16,
            ],
          ),
        ),
      ),
    );
  }
}
