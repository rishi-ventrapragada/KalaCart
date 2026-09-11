import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../constants/app_spacing.dart';
import '../widgets/app_button.dart';
import '../../features/auth/domain/user_model.dart';
import '../../features/auth/presentation/email_verification_screen.dart';
import '../../features/auth/presentation/forgot_password_screen.dart';
import '../../features/auth/presentation/login_screen.dart';
import '../../features/auth/presentation/reset_password_screen.dart';
import '../../features/auth/presentation/signup_screen.dart';
import '../../features/catalog_studio/presentation/catalog_studio_screen.dart';
import '../../features/catalog_studio/presentation/product_creation_wizard_screen.dart';
import '../../features/catalog_studio/presentation/seller_catalog_screen.dart';
import '../../features/chat/presentation/chat_screen.dart';
import '../../features/chat/presentation/conversation_list_screen.dart';
import '../../features/discovery/presentation/discovery_screen.dart';
import '../../features/home/presentation/main_application_shell.dart';
import '../../features/live/presentation/live_discovery_screen.dart';
import '../../features/live/presentation/live_viewer_screen.dart';
import '../../features/live/presentation/seller_live_dashboard_screen.dart';
import '../../features/live/presentation/seller_schedule_live_screen.dart';
import '../../features/onboarding/presentation/artisan_onboarding_screen.dart';
import '../../features/onboarding/presentation/buyer_onboarding_screen.dart';
import '../../features/onboarding/presentation/choose_account_type_screen.dart';
import '../../features/onboarding/presentation/splash_screen.dart';
import '../../features/onboarding/presentation/welcome_screen.dart';
import '../../features/orders/presentation/cart_screen.dart';
import '../../features/orders/presentation/checkout_screen.dart';
import '../../features/orders/presentation/orders_dispatcher_screen.dart';
import '../../features/passport/presentation/craft_passport_screen.dart';
import '../../features/products/presentation/product_details_screen.dart';
import '../../features/profile/presentation/artisan_storefront_screen.dart';
import '../../features/profile/presentation/profile_dispatcher_screen.dart';
import '../../features/profile/presentation/seller_storefront_settings_screen.dart';
import '../../features/rfq/presentation/buyer_create_rfq_screen.dart';
import '../../features/rfq/presentation/rfq_screen.dart';

class FeaturePlaceholderScreen extends StatelessWidget {
  final String title;
  final String description;
  final IconData icon;

  const FeaturePlaceholderScreen({
    super.key,
    required this.title,
    required this.description,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Text(title),
      ),
      body: Center(
        child: Padding(
          padding: AppSpacing.paddingAllXl,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                padding: AppSpacing.paddingAllLg,
                decoration: BoxDecoration(
                  color: theme.colorScheme.primaryContainer.withValues(alpha: 0.4),
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  icon,
                  size: 48,
                  color: theme.colorScheme.primary,
                ),
              ),
              AppSpacing.gapV16,
              Text(
                title,
                style: theme.textTheme.headlineSmall,
                textAlign: TextAlign.center,
              ),
              AppSpacing.gapV8,
              Text(
                description,
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
                ),
                textAlign: TextAlign.center,
              ),
              AppSpacing.gapV24,
              SizedBox(
                width: 160,
                child: AppButton(
                  label: 'Back to Home',
                  icon: Icons.arrow_back,
                  onPressed: () {
                    if (context.canPop()) {
                      context.pop();
                    } else {
                      context.go('/');
                    }
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

final GlobalKey<NavigatorState> _rootNavigatorKey = GlobalKey<NavigatorState>();
final GlobalKey<NavigatorState> _shellNavigatorKey = GlobalKey<NavigatorState>();

final appRouter = GoRouter(
  navigatorKey: _rootNavigatorKey,
  initialLocation: '/splash',
  routes: [
    GoRoute(
      path: '/splash',
      builder: (context, state) => const SplashScreen(),
    ),
    GoRoute(
      path: '/welcome',
      builder: (context, state) => const WelcomeScreen(),
    ),
    GoRoute(
      path: '/account-type',
      builder: (context, state) => const ChooseAccountTypeScreen(),
    ),
    GoRoute(
      path: '/login',
      builder: (context, state) => const LoginScreen(),
    ),
    GoRoute(
      path: '/signup',
      builder: (context, state) {
        final typeStr = state.uri.queryParameters['type'];
        final accountType = typeStr == 'artisan' ? UserAccountType.artisan : UserAccountType.buyer;
        return SignUpScreen(accountType: accountType);
      },
    ),
    GoRoute(
      path: '/email-verification',
      builder: (context, state) {
        final email = state.uri.queryParameters['email'] ?? 'user@kalacart.in';
        final type = state.uri.queryParameters['type'] ?? 'buyer';
        return EmailVerificationScreen(email: email, accountType: type);
      },
    ),
    GoRoute(
      path: '/forgot-password',
      builder: (context, state) => const ForgotPasswordScreen(),
    ),
    GoRoute(
      path: '/reset-password',
      builder: (context, state) {
        final email = state.uri.queryParameters['email'] ?? 'user@kalacart.in';
        return ResetPasswordScreen(email: email);
      },
    ),
    GoRoute(
      path: '/buyer-onboarding',
      builder: (context, state) => const BuyerOnboardingScreen(),
    ),
    GoRoute(
      path: '/artisan-onboarding',
      builder: (context, state) => const ArtisanOnboardingScreen(),
    ),

    // Main Shell Navigation
    ShellRoute(
      navigatorKey: _shellNavigatorKey,
      builder: (context, state, child) {
        return MainApplicationShell(child: child);
      },
      routes: [
        GoRoute(
          path: '/',
          builder: (context, state) => const AppHomeDispatcher(),
        ),
        GoRoute(
          path: '/discovery',
          builder: (context, state) => const DiscoveryScreen(),
        ),
        GoRoute(
          path: '/catalog-studio',
          builder: (context, state) => const SellerCatalogScreen(),
        ),
        GoRoute(
          path: '/rfq',
          builder: (context, state) => const RfqScreen(),
        ),
        GoRoute(
          path: '/orders',
          builder: (context, state) => const OrdersDispatcherScreen(),
        ),
        GoRoute(
          path: '/craft-passport',
          builder: (context, state) => const CraftPassportScreen(passportId: 'GI-IN-RAJ-2026-BP-0941'),
        ),
        GoRoute(
          path: '/profile',
          builder: (context, state) => const ProfileDispatcherScreen(),
        ),
      ],
    ),

    // Deep-links & Sub-routes
    GoRoute(
      path: '/products/:id',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) {
        final id = state.pathParameters['id'] ?? 'prod-001';
        return ProductDetailsScreen(productId: id);
      },
    ),
    GoRoute(
      path: '/product/:id',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) {
        final id = state.pathParameters['id'] ?? 'prod-001';
        return ProductDetailsScreen(productId: id);
      },
    ),
    GoRoute(
      path: '/artisan/:id',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) {
        final id = state.pathParameters['id'] ?? 'art-002';
        return ArtisanStorefrontScreen(artisanId: id);
      },
    ),
    GoRoute(
      path: '/store/:slug',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) {
        final slug = state.pathParameters['slug'] ?? 'kripal-kumbh-jaipur';
        return ArtisanStorefrontScreen(artisanId: slug);
      },
    ),
    GoRoute(
      path: '/passport/:id',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) {
        final id = state.pathParameters['id'] ?? 'GI-IN-RAJ-2026-BP-0941';
        return CraftPassportScreen(passportId: id);
      },
    ),
    GoRoute(
      path: '/live/:id',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) {
        final id = state.pathParameters['id'] ?? 'live-01';
        return LiveViewerScreen(sessionId: id);
      },
    ),
    GoRoute(
      path: '/live-discovery',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) => const LiveDiscoveryScreen(),
    ),
    GoRoute(
      path: '/seller/live/schedule',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) => const SellerScheduleLiveScreen(),
    ),
    GoRoute(
      path: '/seller/live/:id',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) {
        final id = state.pathParameters['id'] ?? 'live-01';
        return SellerLiveDashboardScreen(sessionId: id);
      },
    ),
    GoRoute(
      path: '/cart',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) => const CartScreen(),
    ),
    GoRoute(
      path: '/checkout',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) => const CheckoutScreen(),
    ),
    GoRoute(
      path: '/rfq/create',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) => const BuyerCreateRfqScreen(),
    ),
    GoRoute(
      path: '/chat',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) => const ConversationListScreen(),
    ),
    GoRoute(
      path: '/chat/:id',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) {
        final id = state.pathParameters['id'] ?? 'conv-01';
        return ChatScreen(conversationId: id);
      },
    ),
    GoRoute(
      path: '/catalog-studio/ai',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) => const CatalogStudioScreen(),
    ),
    GoRoute(
      path: '/catalog-studio/create',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) => const ProductCreationWizardScreen(),
    ),
    GoRoute(
      path: '/store-settings',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) => const SellerStorefrontSettingsScreen(),
    ),
    GoRoute(
      path: '/notifications',
      parentNavigatorKey: _rootNavigatorKey,
      builder: (context, state) => const FeaturePlaceholderScreen(
        title: 'Notifications',
        description: 'Real-time updates on your orders, RFQ bids, and artisan live broadcasts.',
        icon: Icons.notifications_active_outlined,
      ),
    ),
  ],
);
