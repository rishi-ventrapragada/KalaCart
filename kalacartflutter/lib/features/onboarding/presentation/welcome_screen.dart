import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_constants.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/widgets/app_button.dart';

class WelcomeScreen extends StatelessWidget {
  const WelcomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: AppSpacing.paddingAllXl,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Spacer(),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: const BoxDecoration(
                  color: AppColors.primaryContainer,
                  borderRadius: AppRadius.borderLg,
                ),
                child: const Icon(
                  Icons.auto_awesome_rounded,
                  size: 40,
                  color: AppColors.primary,
                ),
              ),
              AppSpacing.gapV24,
              Text(
                'Welcome to\n${AppConstants.appName}',
                style: theme.textTheme.displaySmall?.copyWith(
                  fontWeight: FontWeight.w800,
                  height: 1.2,
                ),
              ),
              AppSpacing.gapV12,
              Text(
                'Connecting global buyers and connoisseurs directly to master Indian artisans with AI studio tools, verified provenance & custom B2B RFQs.',
                style: theme.textTheme.bodyLarge?.copyWith(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.75),
                  height: 1.5,
                ),
              ),
              const Spacer(),
              AppButton(
                label: 'Get Started',
                onPressed: () => context.push('/account-type'),
              ),
              AppSpacing.gapV12,
              AppButton(
                label: 'I Already Have an Account',
                variant: AppButtonVariant.outline,
                onPressed: () => context.push('/login'),
              ),
              AppSpacing.gapV12,
              Center(
                child: TextButton(
                  onPressed: () => context.go('/'),
                  child: const Text('Explore as Guest'),
                ),
              ),
              AppSpacing.gapV16,
            ],
          ),
        ),
      ),
    );
  }
}
