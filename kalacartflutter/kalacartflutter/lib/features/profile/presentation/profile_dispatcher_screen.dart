import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../shared/services/user_role_service.dart';
import 'buyer_profile_screen.dart';
import 'seller_profile_screen.dart';

class ProfileDispatcherScreen extends ConsumerWidget {
  const ProfileDispatcherScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final userRole = ref.watch(userRoleProvider);

    if (userRole.isArtisanSeller) {
      return const SellerProfileScreen();
    } else {
      return const BuyerProfileScreen();
    }
  }
}
