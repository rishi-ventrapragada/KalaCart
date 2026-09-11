import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../domain/user_model.dart';
import 'auth_repository.dart';

class SupabaseAuthRepository implements AuthRepository {
  final SupabaseClient _client;

  SupabaseAuthRepository(this._client);

  @override
  Stream<UserModel?> get authStateChanges {
    return _client.auth.onAuthStateChange.asyncMap((data) async {
      final session = data.session;
      if (session == null) return null;
      return _fetchUserProfile(session.user.id, session.user.email ?? '');
    });
  }

  @override
  UserModel? get currentUser {
    final user = _client.auth.currentUser;
    if (user == null) return null;
    return UserModel(
      id: user.id,
      email: user.email ?? '',
      fullName: user.email?.split('@').first ?? 'Artisan User',
      accountType: UserAccountType.buyer,
      isEmailVerified: user.emailConfirmedAt != null,
    );
  }

  Future<UserModel> _fetchUserProfile(String authUserId, String email) async {
    try {
      final profileRes = await _client
          .from('profiles')
          .select()
          .eq('auth_user_id', authUserId)
          .maybeSingle();

      if (profileRes != null) {
        final roleStr = profileRes['role'] as String? ?? 'buyer';
        final accountType = roleStr == 'seller' || roleStr == 'artisan'
            ? UserAccountType.artisan
            : UserAccountType.buyer;

        return UserModel(
          id: profileRes['id'] as String,
          email: profileRes['email'] as String? ?? email,
          fullName: profileRes['full_name'] as String? ?? 'Artisan User',
          accountType: accountType,
          isEmailVerified: true,
          phoneNumber: profileRes['phone'],
        );
      }
    } catch (_) {}

    return UserModel(
      id: authUserId,
      email: email,
      fullName: email.split('@').first,
      accountType: UserAccountType.buyer,
      isEmailVerified: true,
    );
  }

  @override
  Future<UserModel> signInWithEmail({required String email, required String password}) async {
    final res = await _client.auth.signInWithPassword(email: email, password: password);
    final user = res.user;
    if (user == null) throw Exception('Login failed');
    return _fetchUserProfile(user.id, user.email ?? email);
  }

  @override
  Future<UserModel> signUpWithEmail({
    required String email,
    required String password,
    required String fullName,
    required UserAccountType accountType,
  }) async {
    final res = await _client.auth.signUp(email: email, password: password);
    final user = res.user;
    if (user == null) throw Exception('Registration failed');

    try {
      await _client.from('profiles').insert({
        'auth_user_id': user.id,
        'email': email,
        'full_name': fullName,
        'role': accountType == UserAccountType.artisan ? 'seller' : 'buyer',
      });
    } catch (_) {}

    return UserModel(
      id: user.id,
      email: email,
      fullName: fullName,
      accountType: accountType,
      isEmailVerified: false,
    );
  }

  @override
  Future<void> sendEmailVerification() async {
    final user = _client.auth.currentUser;
    if (user?.email != null) {
      await _client.auth.resend(type: OtpType.signup, email: user!.email!);
    }
  }

  @override
  Future<void> sendPasswordResetEmail(String email) async {
    await _client.auth.resetPasswordForEmail(email);
  }

  @override
  Future<void> resetPassword({required String email, required String newPassword}) async {
    await _client.auth.updateUser(UserAttributes(password: newPassword));
  }

  @override
  Future<UserModel> completeBuyerOnboarding(BuyerProfileData data) async {
    final user = _client.auth.currentUser;
    if (user != null) {
      await _client.from('profiles').update({
        'full_name': data.name,
        'city': data.location,
      }).eq('auth_user_id', user.id);
    }
    return currentUser ?? UserModel(
      id: user?.id ?? 'usr-01',
      email: user?.email ?? '',
      fullName: data.name,
      accountType: UserAccountType.buyer,
      isOnboarded: true,
      buyerProfile: data,
    );
  }

  @override
  Future<UserModel> completeArtisanOnboarding(ArtisanProfileData data) async {
    final user = _client.auth.currentUser;
    if (user != null) {
      final profile = await _client
          .from('profiles')
          .select('id')
          .eq('auth_user_id', user.id)
          .maybeSingle();

      if (profile != null) {
        final profileId = profile['id'] as String;
        await _client.from('sellers').insert({
          'profile_id': profileId,
          'shop_name': data.storefrontName,
          'artisan_type': data.craftCategory,
          'bio': data.bio,
        });
      }
    }
    return currentUser ?? UserModel(
      id: user?.id ?? 'usr-01',
      email: user?.email ?? '',
      fullName: data.artisanName,
      accountType: UserAccountType.artisan,
      isOnboarded: true,
      artisanProfile: data,
    );
  }

  @override
  Future<void> setAccountType(UserAccountType accountType) async {
    final user = _client.auth.currentUser;
    if (user != null) {
      await _client.from('profiles').update({
        'role': accountType == UserAccountType.artisan ? 'seller' : 'buyer',
      }).eq('auth_user_id', user.id);
    }
  }

  @override
  Future<void> signOut() async {
    await _client.auth.signOut();
  }
}

final supabaseClientProvider = Provider<SupabaseClient>((ref) {
  return Supabase.instance.client;
});

final supabaseAuthRepositoryProvider = Provider<AuthRepository>((ref) {
  return SupabaseAuthRepository(ref.watch(supabaseClientProvider));
});
