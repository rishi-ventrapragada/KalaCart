import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../shared/services/user_role_service.dart';
import 'buyer_orders_screen.dart';
import 'seller_orders_screen.dart';

class OrdersDispatcherScreen extends ConsumerWidget {
  const OrdersDispatcherScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final userRole = ref.watch(userRoleProvider);

    if (userRole.isArtisanSeller) {
      return const SellerOrdersScreen();
    } else {
      return const BuyerOrdersScreen();
    }
  }
}
