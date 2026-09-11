import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/offline_status_bar.dart';
import '../../../shared/services/user_role_service.dart';
import 'buyer_home_shell.dart';
import 'seller_home_shell.dart';

class MainApplicationShell extends ConsumerWidget {
  final Widget child;

  const MainApplicationShell({super.key, required this.child});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final userRole = ref.watch(userRoleProvider);
    final themeMode = ref.watch(themeModeProvider);
    final isBuyer = userRole.activeRole == UserRole.buyer;

    final location = GoRouterState.of(context).uri.toString();
    int selectedIndex = _calculateSelectedIndex(location, isBuyer);

    return Scaffold(
      body: Column(
        children: [
          const OfflineStatusBar(),
          Expanded(child: child),
        ],
      ),
      bottomSheet: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.surface,
          border: Border(
            top: BorderSide(
              color: Theme.of(context).dividerColor.withValues(alpha: 0.1),
            ),
          ),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              children: [
                Icon(
                  isBuyer ? Icons.shopping_bag_outlined : Icons.handyman_outlined,
                  size: 16,
                  color: isBuyer ? AppColors.primary : AppColors.secondary,
                ),
                AppSpacing.gapH8,
                Text(
                  isBuyer ? 'Buyer Mode' : 'Artisan Seller Mode',
                  style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold),
                ),
              ],
            ),
            Row(
              children: [
                TextButton(
                  onPressed: () {
                    ref.read(userRoleProvider.notifier).toggleRole();
                    context.go('/');
                  },
                  style: TextButton.styleFrom(
                    visualDensity: VisualDensity.compact,
                    padding: const EdgeInsets.symmetric(horizontal: 8),
                  ),
                  child: Text(
                    isBuyer ? 'Switch to Artisan' : 'Switch to Buyer',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      color: isBuyer ? AppColors.secondary : AppColors.primary,
                    ),
                  ),
                ),
                IconButton(
                  icon: Icon(
                    themeMode == ThemeMode.dark ? Icons.light_mode_rounded : Icons.dark_mode_rounded,
                    size: 16,
                  ),
                  visualDensity: VisualDensity.compact,
                  onPressed: () {
                    ref.read(themeModeProvider.notifier).state =
                        themeMode == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark;
                  },
                ),
              ],
            ),
          ],
        ),
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: selectedIndex,
        onDestinationSelected: (index) => _onItemTapped(index, context, isBuyer),
        destinations: isBuyer ? _buyerDestinations : _sellerDestinations,
      ),
    );
  }

  static const List<NavigationDestination> _buyerDestinations = [
    NavigationDestination(
      icon: Icon(Icons.home_outlined),
      selectedIcon: Icon(Icons.home_rounded),
      label: 'Home',
    ),
    NavigationDestination(
      icon: Icon(Icons.explore_outlined),
      selectedIcon: Icon(Icons.explore_rounded),
      label: 'Discover',
    ),
    NavigationDestination(
      icon: Icon(Icons.handshake_outlined),
      selectedIcon: Icon(Icons.handshake_rounded),
      label: 'RFQ',
    ),
    NavigationDestination(
      icon: Icon(Icons.local_shipping_outlined),
      selectedIcon: Icon(Icons.local_shipping_rounded),
      label: 'Orders',
    ),
    NavigationDestination(
      icon: Icon(Icons.person_outline_rounded),
      selectedIcon: Icon(Icons.person_rounded),
      label: 'Profile',
    ),
  ];

  static const List<NavigationDestination> _sellerDestinations = [
    NavigationDestination(
      icon: Icon(Icons.dashboard_outlined),
      selectedIcon: Icon(Icons.dashboard_rounded),
      label: 'Home',
    ),
    NavigationDestination(
      icon: Icon(Icons.inventory_2_outlined),
      selectedIcon: Icon(Icons.inventory_2_rounded),
      label: 'Catalog',
    ),
    NavigationDestination(
      icon: Icon(Icons.assignment_outlined),
      selectedIcon: Icon(Icons.assignment_rounded),
      label: 'RFQs',
    ),
    NavigationDestination(
      icon: Icon(Icons.receipt_long_outlined),
      selectedIcon: Icon(Icons.receipt_long_rounded),
      label: 'Orders',
    ),
    NavigationDestination(
      icon: Icon(Icons.storefront_outlined),
      selectedIcon: Icon(Icons.storefront_rounded),
      label: 'Studio',
    ),
  ];

  int _calculateSelectedIndex(String location, bool isBuyer) {
    if (location == '/' || location.isEmpty) return 0;
    if (isBuyer) {
      if (location.startsWith('/discovery')) return 1;
      if (location.startsWith('/rfq')) return 2;
      if (location.startsWith('/orders')) return 3;
      if (location.startsWith('/profile') || location.startsWith('/settings')) return 4;
    } else {
      if (location.startsWith('/catalog') || location.startsWith('/catalog-studio')) return 1;
      if (location.startsWith('/rfq')) return 2;
      if (location.startsWith('/orders')) return 3;
      if (location.startsWith('/profile') || location.startsWith('/settings')) return 4;
    }
    return 0;
  }

  void _onItemTapped(int index, BuildContext context, bool isBuyer) {
    if (isBuyer) {
      switch (index) {
        case 0:
          context.go('/');
          break;
        case 1:
          context.go('/discovery');
          break;
        case 2:
          context.go('/rfq');
          break;
        case 3:
          context.go('/orders');
          break;
        case 4:
          context.go('/profile');
          break;
      }
    } else {
      switch (index) {
        case 0:
          context.go('/');
          break;
        case 1:
          context.go('/catalog-studio');
          break;
        case 2:
          context.go('/rfq');
          break;
        case 3:
          context.go('/orders');
          break;
        case 4:
          context.go('/profile');
          break;
      }
    }
  }
}

class AppHomeDispatcher extends ConsumerWidget {
  const AppHomeDispatcher({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final userRole = ref.watch(userRoleProvider);
    if (userRole.activeRole == UserRole.artisanSeller) {
      return const SellerHomeShell();
    }
    return const BuyerHomeShell();
  }
}
