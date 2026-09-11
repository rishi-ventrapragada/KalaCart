import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/widgets/app_button.dart';
import '../data/auth_repository.dart';
import '../data/supabase_auth_repository.dart';

/// Shown after sign-up when the backend requires the email to be confirmed
/// through the link it sent. There is no code to type: the user opens the
/// link, then signs in.
class EmailVerificationScreen extends ConsumerStatefulWidget {
  final String email;
  final String accountType;

  const EmailVerificationScreen({
    super.key,
    required this.email,
    required this.accountType,
  });

  @override
  ConsumerState<EmailVerificationScreen> createState() => _EmailVerificationScreenState();
}

class _EmailVerificationScreenState extends ConsumerState<EmailVerificationScreen> {
  bool _isResending = false;

  Future<void> _resend() async {
    if (widget.email.isEmpty) return;
    setState(() => _isResending = true);
    try {
      await ref.read(authControllerProvider).resendVerification(widget.email);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Verification email re-sent to ${widget.email}'),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(authErrorMessage(e)),
            backgroundColor: AppColors.error,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isResending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(),
      body: SafeArea(
        child: Padding(
          padding: AppSpacing.paddingAllXl,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                padding: AppSpacing.paddingAllLg,
                decoration: const BoxDecoration(
                  color: AppColors.primaryContainer,
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.mark_email_read_outlined,
                  size: 56,
                  color: AppColors.primary,
                ),
              ),
              AppSpacing.gapV24,
              Text(
                'Confirm Your Email',
                style: theme.textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w800),
                textAlign: TextAlign.center,
              ),
              AppSpacing.gapV8,
              Text(
                'We sent a confirmation link to:\n${widget.email}\n\nOpen the link to activate your account, then come back and sign in.',
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
                  height: 1.5,
                ),
                textAlign: TextAlign.center,
              ),
              AppSpacing.gapV32,

              AppButton(
                label: "I've confirmed, take me to Sign In",
                onPressed: () => context.go('/login'),
              ),
              AppSpacing.gapV12,

              AppButton(
                label: 'Resend confirmation email',
                variant: AppButtonVariant.text,
                isLoading: _isResending,
                onPressed: _resend,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
