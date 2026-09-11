import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../domain/user_model.dart';
import 'supabase_auth_repository.dart';

/// Contract for authentication + profile persistence.
///
/// The production implementation is [SupabaseAuthRepository]. [MockAuthRepository]
/// is kept for widget tests and for running the UI without a backend.
abstract class AuthRepository {
  /// Emits whenever the signed-in user (or their profile) changes. `null` = signed out.
  Stream<UserModel?> get authStateChanges;

  /// Last known user, synchronously. May be null while a session is still being resolved.
  UserModel? get currentUser;

  /// Resolves any persisted session into a full [UserModel]. Returns null when signed out.
  Future<UserModel?> restoreSession();

  Future<UserModel> signInWithEmail({required String email, required String password});

  /// Creates the account. When email confirmation is required by the backend the
  /// returned user has `isEmailVerified == false` and there is no active session yet.
  Future<UserModel> signUpWithEmail({
    required String email,
    required String password,
    required String fullName,
    required UserAccountType accountType,
  });

  Future<void> sendEmailVerification(String email);
  Future<void> sendPasswordResetEmail(String email);

  /// Sets a new password for the currently authenticated (or recovery) session.
  Future<void> updatePassword(String newPassword);

  Future<UserModel> completeBuyerOnboarding(BuyerProfileData data);
  Future<UserModel> completeArtisanOnboarding(ArtisanProfileData data);
  Future<UserModel> setAccountType(UserAccountType accountType);

  /// Re-reads the profile for the current session and emits it.
  Future<UserModel?> refreshUser();

  Future<void> signOut();
}

/// In-memory implementation used by tests. Any email/password signs in; an email
/// containing "artisan" or "seller" becomes an artisan account.
class MockAuthRepository implements AuthRepository {
  UserModel? _user;
  final _controller = StreamController<UserModel?>.broadcast();

  void _emit(UserModel? user) {
    _user = user;
    if (!_controller.isClosed) _controller.add(user);
  }

  @override
  Stream<UserModel?> get authStateChanges => _controller.stream;

  @override
  UserModel? get currentUser => _user;

  @override
  Future<UserModel?> restoreSession() async => _user;

  @override
  Future<UserModel> signInWithEmail({required String email, required String password}) async {
    await Future.delayed(const Duration(milliseconds: 300));
    final lower = email.toLowerCase();
    final isSeller = lower.contains('artisan') || lower.contains('seller');
    final user = UserModel(
      id: 'usr-mock-001',
      profileId: 'prof-mock-001',
      sellerId: isSeller ? 'sel-mock-001' : null,
      email: email,
      fullName: isSeller ? 'Demo Artisan' : 'Demo Buyer',
      accountType: isSeller ? UserAccountType.artisan : UserAccountType.buyer,
      isEmailVerified: true,
      isOnboarded: true,
      city: isSeller ? 'Jaipur' : 'Bengaluru',
      state: isSeller ? 'Rajasthan' : 'Karnataka',
      shopName: isSeller ? 'Demo Blue Pottery Studio' : null,
      artisanType: isSeller ? 'Pottery & Terracotta' : null,
    );
    _emit(user);
    return user;
  }

  @override
  Future<UserModel> signUpWithEmail({
    required String email,
    required String password,
    required String fullName,
    required UserAccountType accountType,
  }) async {
    await Future.delayed(const Duration(milliseconds: 300));
    final user = UserModel(
      id: 'usr-mock-new',
      profileId: 'prof-mock-new',
      email: email,
      fullName: fullName,
      accountType: accountType,
      isEmailVerified: true,
      isOnboarded: false,
    );
    _emit(user);
    return user;
  }

  @override
  Future<void> sendEmailVerification(String email) async {}

  @override
  Future<void> sendPasswordResetEmail(String email) async {}

  @override
  Future<void> updatePassword(String newPassword) async {}

  @override
  Future<UserModel> completeBuyerOnboarding(BuyerProfileData data) async {
    final loc = splitLocation(data.location);
    final user = (_user ??
            UserModel(id: 'usr-mock-buyer', email: 'buyer@example.com', fullName: data.name, accountType: UserAccountType.buyer))
        .copyWith(
      fullName: data.name,
      city: loc.city,
      state: loc.state,
      accountType: UserAccountType.buyer,
      isOnboarded: true,
    );
    _emit(user);
    return user;
  }

  @override
  Future<UserModel> completeArtisanOnboarding(ArtisanProfileData data) async {
    final loc = splitLocation(data.villageLocation);
    final user = (_user ??
            UserModel(id: 'usr-mock-artisan', email: 'artisan@example.com', fullName: data.artisanName, accountType: UserAccountType.artisan))
        .copyWith(
      fullName: data.artisanName,
      sellerId: 'sel-mock-new',
      shopName: data.storefrontName,
      artisanType: data.craftCategory,
      bio: data.bio,
      sellerLocation: data.villageLocation,
      city: loc.city,
      state: loc.state,
      accountType: UserAccountType.artisan,
      isOnboarded: true,
    );
    _emit(user);
    return user;
  }

  @override
  Future<UserModel> setAccountType(UserAccountType accountType) async {
    final user = _user;
    if (user == null) throw StateError('Not signed in');
    final updated = user.copyWith(
      accountType: accountType,
      isOnboarded: accountType == UserAccountType.artisan ? user.hasSellerProfile : true,
    );
    _emit(updated);
    return updated;
  }

  @override
  Future<UserModel?> refreshUser() async => _user;

  @override
  Future<void> signOut() async => _emit(null);
}

// ---------------------------------------------------------------------------
// Providers
// ---------------------------------------------------------------------------

/// The active repository. Override this in tests with [MockAuthRepository].
final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return ref.watch(supabaseAuthRepositoryProvider);
});

/// The signed-in user. Loading until the persisted session has been resolved,
/// then `null` (signed out) or a [UserModel].
final authStateProvider = StreamProvider<UserModel?>((ref) {
  final repo = ref.watch(authRepositoryProvider);
  final controller = StreamController<UserModel?>();

  final sub = repo.authStateChanges.listen(
    (user) {
      if (!controller.isClosed) controller.add(user);
    },
    onError: (Object e, StackTrace s) {
      if (!controller.isClosed) controller.add(null);
    },
  );

  repo.restoreSession().then((user) {
    if (!controller.isClosed) controller.add(user);
  }).catchError((Object _) {
    if (!controller.isClosed) controller.add(null);
  });

  ref.onDispose(() {
    sub.cancel();
    controller.close();
  });
  return controller.stream;
});

/// Convenience: the current user or null. Null while loading as well.
final currentUserProvider = Provider<UserModel?>((ref) {
  return ref.watch(authStateProvider).valueOrNull;
});

final isAuthenticatedProvider = Provider<bool>((ref) {
  return ref.watch(currentUserProvider) != null;
});

/// Thin facade the screens call. All methods surface errors to the caller so
/// the UI can show them; use [authErrorMessage] to turn them into text.
class AuthController {
  final Ref _ref;
  AuthController(this._ref);

  AuthRepository get _repo => _ref.read(authRepositoryProvider);

  Future<UserModel> signIn(String email, String password) =>
      _repo.signInWithEmail(email: email.trim(), password: password);

  Future<UserModel> signUp({
    required String email,
    required String password,
    required String fullName,
    required UserAccountType accountType,
  }) =>
      _repo.signUpWithEmail(
        email: email.trim(),
        password: password,
        fullName: fullName.trim(),
        accountType: accountType,
      );

  Future<void> resendVerification(String email) => _repo.sendEmailVerification(email.trim());

  Future<void> sendPasswordReset(String email) => _repo.sendPasswordResetEmail(email.trim());

  Future<void> updatePassword(String newPassword) => _repo.updatePassword(newPassword);

  Future<UserModel> completeBuyer(BuyerProfileData data) => _repo.completeBuyerOnboarding(data);

  Future<UserModel> completeArtisan(ArtisanProfileData data) => _repo.completeArtisanOnboarding(data);

  Future<UserModel> setAccountType(UserAccountType type) => _repo.setAccountType(type);

  Future<UserModel?> refresh() => _repo.refreshUser();

  Future<void> signOut() => _repo.signOut();
}

final authControllerProvider = Provider<AuthController>((ref) => AuthController(ref));
