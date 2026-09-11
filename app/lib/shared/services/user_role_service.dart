import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../features/auth/data/auth_repository.dart';
import '../../features/auth/domain/user_model.dart';

enum UserRole {
  buyer,
  artisanSeller,
}

/// Read-only view of the signed-in user's role and display labels.
///
/// Derived from [currentUserProvider]; to change the role call
/// `AuthController.setAccountType`, which updates `profiles.role` in Supabase.
class UserRoleState {
  final UserRole activeRole;
  final String userName;
  final String craftCluster;
  final String region;

  const UserRoleState({
    required this.activeRole,
    required this.userName,
    required this.craftCluster,
    required this.region,
  });

  bool get isArtisanSeller => activeRole == UserRole.artisanSeller;
  bool get isBuyer => activeRole == UserRole.buyer;

  static const guest = UserRoleState(
    activeRole: UserRole.buyer,
    userName: 'Guest',
    craftCluster: 'All India Craft Network',
    region: 'India',
  );
}

final userRoleProvider = Provider<UserRoleState>((ref) {
  final user = ref.watch(currentUserProvider);
  if (user == null) return UserRoleState.guest;

  if (user.accountType == UserAccountType.artisan) {
    return UserRoleState(
      activeRole: UserRole.artisanSeller,
      userName: user.fullName,
      craftCluster: user.shopName ?? user.artisanType ?? 'Artisan Studio',
      region: (user.sellerLocation?.trim().isNotEmpty ?? false) ? user.sellerLocation!.trim() : user.regionLabel,
    );
  }

  return UserRoleState(
    activeRole: UserRole.buyer,
    userName: user.fullName,
    craftCluster: 'All India Craft Network',
    region: user.regionLabel,
  );
});
