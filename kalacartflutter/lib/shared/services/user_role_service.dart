import 'package:flutter_riverpod/flutter_riverpod.dart';

enum UserRole {
  buyer,
  artisanSeller,
}

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

  UserRoleState copyWith({
    UserRole? activeRole,
    String? userName,
    String? craftCluster,
    String? region,
  }) {
    return UserRoleState(
      activeRole: activeRole ?? this.activeRole,
      userName: userName ?? this.userName,
      craftCluster: craftCluster ?? this.craftCluster,
      region: region ?? this.region,
    );
  }
}

class UserRoleNotifier extends StateNotifier<UserRoleState> {
  UserRoleNotifier()
      : super(
          const UserRoleState(
            activeRole: UserRole.buyer,
            userName: 'Aditya (Artisan Explorer)',
            craftCluster: 'Jaipur Blue Pottery Collective',
            region: 'Rajasthan',
          ),
        );

  void toggleRole() {
    if (state.activeRole == UserRole.buyer) {
      state = state.copyWith(
        activeRole: UserRole.artisanSeller,
        userName: 'Ustad Kripal Kumbh',
        craftCluster: 'Jaipur Blue Pottery Guild',
        region: 'Rajasthan',
      );
    } else {
      state = state.copyWith(
        activeRole: UserRole.buyer,
        userName: 'Aditya (Artisan Explorer)',
        craftCluster: 'All India Craft Network',
        region: 'Pan India',
      );
    }
  }

  void setRole(UserRole role) {
    if (role == UserRole.buyer) {
      state = state.copyWith(
        activeRole: UserRole.buyer,
        userName: 'Aditya (Artisan Explorer)',
        craftCluster: 'All India Craft Network',
      );
    } else {
      state = state.copyWith(
        activeRole: UserRole.artisanSeller,
        userName: 'Ustad Kripal Kumbh',
        craftCluster: 'Jaipur Blue Pottery Guild',
      );
    }
  }
}

final userRoleProvider = StateNotifierProvider<UserRoleNotifier, UserRoleState>((ref) {
  return UserRoleNotifier();
});
