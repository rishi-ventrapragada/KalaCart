import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../domain/user_model.dart';

abstract class AuthRepository {
  Stream<UserModel?> get authStateChanges;
  UserModel? get currentUser;
  Future<UserModel> signInWithEmail({required String email, required String password});
  Future<UserModel> signUpWithEmail({
    required String email,
    required String password,
    required String fullName,
    required UserAccountType accountType,
  });
  Future<void> sendEmailVerification();
  Future<void> sendPasswordResetEmail(String email);
  Future<void> resetPassword({required String email, required String newPassword});
  Future<UserModel> completeBuyerOnboarding(BuyerProfileData data);
  Future<UserModel> completeArtisanOnboarding(ArtisanProfileData data);
  Future<void> setAccountType(UserAccountType accountType);
  Future<void> signOut();
}

class MockAuthRepository implements AuthRepository {
  UserModel? _mockUser;
  final _stateController = StateController<UserModel?>(null);

  MockAuthRepository() {
    // Default initial mock state (unauthenticated or pre-seeded)
  }

  @override
  Stream<UserModel?> get authStateChanges => _stateController.stream;

  @override
  UserModel? get currentUser => _mockUser;

  @override
  Future<UserModel> signInWithEmail({required String email, required String password}) async {
    await Future.delayed(const Duration(milliseconds: 400));
    final isSeller = email.toLowerCase().contains('artisan') || email.toLowerCase().contains('seller');
    _mockUser = UserModel(
      id: 'usr-mock-001',
      email: email,
      fullName: isSeller ? 'Ustad Kripal Kumbh' : 'Aditya Craftsman',
      accountType: isSeller ? UserAccountType.artisan : UserAccountType.buyer,
      isEmailVerified: true,
      isOnboarded: true,
    );
    _stateController.state = _mockUser;
    return _mockUser!;
  }

  @override
  Future<UserModel> signUpWithEmail({
    required String email,
    required String password,
    required String fullName,
    required UserAccountType accountType,
  }) async {
    await Future.delayed(const Duration(milliseconds: 400));
    _mockUser = UserModel(
      id: 'usr-mock-new',
      email: email,
      fullName: fullName,
      accountType: accountType,
      isEmailVerified: false,
      isOnboarded: false,
    );
    _stateController.state = _mockUser;
    return _mockUser!;
  }

  @override
  Future<void> sendEmailVerification() async {
    await Future.delayed(const Duration(milliseconds: 300));
    if (_mockUser != null) {
      _mockUser = _mockUser!.copyWith(isEmailVerified: true);
      _stateController.state = _mockUser;
    }
  }

  @override
  Future<void> sendPasswordResetEmail(String email) async {
    await Future.delayed(const Duration(milliseconds: 300));
  }

  @override
  Future<void> resetPassword({required String email, required String newPassword}) async {
    await Future.delayed(const Duration(milliseconds: 400));
  }

  @override
  Future<UserModel> completeBuyerOnboarding(BuyerProfileData data) async {
    await Future.delayed(const Duration(milliseconds: 400));
    if (_mockUser != null) {
      _mockUser = _mockUser!.copyWith(
        isOnboarded: true,
        buyerProfile: data,
        accountType: UserAccountType.buyer,
      );
    } else {
      _mockUser = UserModel(
        id: 'usr-buyer-001',
        email: 'buyer@kalacart.in',
        fullName: data.name,
        accountType: UserAccountType.buyer,
        isEmailVerified: true,
        isOnboarded: true,
        buyerProfile: data,
      );
    }
    _stateController.state = _mockUser;
    return _mockUser!;
  }

  @override
  Future<UserModel> completeArtisanOnboarding(ArtisanProfileData data) async {
    await Future.delayed(const Duration(milliseconds: 400));
    if (_mockUser != null) {
      _mockUser = _mockUser!.copyWith(
        isOnboarded: true,
        artisanProfile: data,
        accountType: UserAccountType.artisan,
      );
    } else {
      _mockUser = UserModel(
        id: 'usr-artisan-001',
        email: 'artisan@kalacart.in',
        fullName: data.artisanName,
        accountType: UserAccountType.artisan,
        isEmailVerified: true,
        isOnboarded: true,
        artisanProfile: data,
      );
    }
    _stateController.state = _mockUser;
    return _mockUser!;
  }

  @override
  Future<void> setAccountType(UserAccountType accountType) async {
    if (_mockUser != null) {
      _mockUser = _mockUser!.copyWith(accountType: accountType);
      _stateController.state = _mockUser;
    }
  }

  @override
  Future<void> signOut() async {
    await Future.delayed(const Duration(milliseconds: 200));
    _mockUser = null;
    _stateController.state = null;
  }
}

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return MockAuthRepository();
});

class AuthNotifier extends StateNotifier<UserModel?> {
  final AuthRepository _repo;

  AuthNotifier(this._repo) : super(_repo.currentUser);

  Future<void> signIn(String email, String password) async {
    state = await _repo.signInWithEmail(email: email, password: password);
  }

  Future<void> signUp(String email, String password, String name, UserAccountType type) async {
    state = await _repo.signUpWithEmail(email: email, password: password, fullName: name, accountType: type);
  }

  Future<void> verifyEmail() async {
    await _repo.sendEmailVerification();
    state = _repo.currentUser;
  }

  Future<void> completeBuyer(BuyerProfileData data) async {
    state = await _repo.completeBuyerOnboarding(data);
  }

  Future<void> completeArtisan(ArtisanProfileData data) async {
    state = await _repo.completeArtisanOnboarding(data);
  }

  Future<void> setAccountType(UserAccountType type) async {
    await _repo.setAccountType(type);
    state = _repo.currentUser;
  }

  Future<void> signOut() async {
    await _repo.signOut();
    state = null;
  }
}

final authControllerProvider = StateNotifierProvider<AuthNotifier, UserModel?>((ref) {
  final repo = ref.watch(authRepositoryProvider);
  return AuthNotifier(repo);
});
