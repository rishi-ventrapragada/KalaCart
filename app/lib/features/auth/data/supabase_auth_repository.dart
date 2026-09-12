import 'dart:async';

import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../domain/user_model.dart';
import 'auth_repository.dart';

/// Auth + profile persistence backed by Supabase.
///
/// Tables used:
///  * `profiles` (auth_user_id, email, full_name, role, phone, city, state, avatar_url, ...)
///  * `sellers`  (profile_id, shop_name, artisan_type, bio, location, ...)
class SupabaseAuthRepository implements AuthRepository {
  final SupabaseClient _client;
  final _controller = StreamController<UserModel?>.broadcast();
  StreamSubscription<AuthState>? _authSub;
  UserModel? _cached;

  SupabaseAuthRepository(this._client) {
    _authSub = _client.auth.onAuthStateChange.listen(_onAuthChange, onError: (Object _) {});
  }

  void dispose() {
    _authSub?.cancel();
    _controller.close();
  }

  Future<void> _onAuthChange(AuthState data) async {
    final session = data.session;
    switch (data.event) {
      case AuthChangeEvent.signedOut:
        _emit(null);
        return;
      case AuthChangeEvent.tokenRefreshed:
        return; // nothing about the profile changed
      default:
        if (session == null) {
          if (data.event == AuthChangeEvent.initialSession) _emit(null);
          return;
        }
        try {
          _emit(await _loadUser(session.user));
        } catch (_) {
          _emit(_fallbackUser(session.user));
        }
    }
  }

  void _emit(UserModel? user) {
    _cached = user;
    if (!_controller.isClosed) _controller.add(user);
  }

  // ------------------------------------------------------------------ reads

  @override
  Stream<UserModel?> get authStateChanges => _controller.stream;

  @override
  UserModel? get currentUser => _cached;

  @override
  Future<UserModel?> restoreSession() async {
    final session = _client.auth.currentSession;
    if (session == null) {
      _emit(null);
      return null;
    }
    try {
      final user = await _loadUser(session.user);
      _emit(user);
      return user;
    } catch (_) {
      final user = _fallbackUser(session.user);
      _emit(user);
      return user;
    }
  }

  @override
  Future<UserModel?> refreshUser() async {
    final authUser = _client.auth.currentUser;
    if (authUser == null) {
      _emit(null);
      return null;
    }
    final user = await _loadUser(authUser);
    _emit(user);
    return user;
  }

  Future<UserModel> _loadUser(User authUser) async {
    Map<String, dynamic>? profile = await _client
        .from('profiles')
        .select()
        .eq('auth_user_id', authUser.id)
        .maybeSingle();

    profile ??= await _createProfile(authUser);

    Map<String, dynamic>? seller;
    if (profile != null) {
      seller = await _client
          .from('sellers')
          .select()
          .eq('profile_id', profile['id'])
          .maybeSingle();
    }
    return _buildUser(authUser, profile, seller);
  }

  Future<Map<String, dynamic>?> _createProfile(User authUser) async {
    final meta = authUser.userMetadata ?? const {};
    final email = authUser.email ?? '';
    try {
      return await _client
          .from('profiles')
          .insert({
            'auth_user_id': authUser.id,
            'email': email,
            'full_name': (meta['full_name'] as String?)?.trim().isNotEmpty == true
                ? meta['full_name']
                : email.split('@').first,
            'role': UserAccountType.fromDb(meta['role'] as String?).dbValue,
          })
          .select()
          .single();
    } catch (_) {
      // Either RLS forbids client inserts (a DB trigger will create it) or the
      // row already exists. Try one more read before giving up.
      try {
        return await _client.from('profiles').select().eq('auth_user_id', authUser.id).maybeSingle();
      } catch (_) {
        return null;
      }
    }
  }

  UserModel _buildUser(User authUser, Map<String, dynamic>? profile, Map<String, dynamic>? seller) {
    final meta = authUser.userMetadata ?? const {};
    final email = (profile?['email'] as String?) ?? authUser.email ?? '';
    final fullName = _firstNonEmpty([
      profile?['full_name'] as String?,
      meta['full_name'] as String?,
      email.split('@').first,
    ]);
    final accountType = UserAccountType.fromDb((profile?['role'] as String?) ?? meta['role'] as String?);
    final city = profile?['city'] as String?;
    final state = profile?['state'] as String?;

    final onboarded = accountType == UserAccountType.artisan
        ? seller != null
        : (profile != null && fullName.isNotEmpty && (city ?? '').trim().isNotEmpty);

    return UserModel(
      id: authUser.id,
      profileId: profile?['id'] as String?,
      sellerId: seller?['id'] as String?,
      email: email,
      fullName: fullName,
      phoneNumber: profile?['phone'] as String?,
      accountType: accountType,
      isEmailVerified: authUser.emailConfirmedAt != null,
      isOnboarded: onboarded,
      city: city,
      state: state,
      avatarUrl: (profile?['avatar_url'] as String?) ?? profile?['profile_photo'] as String?,
      shopName: seller?['shop_name'] as String?,
      artisanType: seller?['artisan_type'] as String?,
      bio: seller?['bio'] as String?,
      // sellers.location is PostGIS geometry, so it is never a String -- an
      // `as String?` cast on a populated row would throw. Nothing writes it
      // any more; place text lives on profiles.city/state, which regionLabel
      // renders and the UI already falls back to.
      sellerLocation: null,
    );
  }

  UserModel _fallbackUser(User authUser) {
    final meta = authUser.userMetadata ?? const {};
    final email = authUser.email ?? '';
    return UserModel(
      id: authUser.id,
      email: email,
      fullName: _firstNonEmpty([meta['full_name'] as String?, email.split('@').first]),
      accountType: UserAccountType.fromDb(meta['role'] as String?),
      isEmailVerified: authUser.emailConfirmedAt != null,
      isOnboarded: false,
    );
  }

  static String _firstNonEmpty(List<String?> candidates) {
    for (final c in candidates) {
      if (c != null && c.trim().isNotEmpty) return c.trim();
    }
    return '';
  }

  // ----------------------------------------------------------------- writes

  @override
  Future<UserModel> signInWithEmail({required String email, required String password}) async {
    final res = await _client.auth.signInWithPassword(email: email, password: password);
    final user = res.user;
    if (user == null) throw const AuthException('Login failed. Please try again.');
    final model = await _loadUser(user);
    _emit(model);
    return model;
  }

  @override
  Future<UserModel> signUpWithEmail({
    required String email,
    required String password,
    required String fullName,
    required UserAccountType accountType,
  }) async {
    final res = await _client.auth.signUp(
      email: email,
      password: password,
      data: {'full_name': fullName, 'role': accountType.dbValue},
    );
    final user = res.user;
    if (user == null) throw const AuthException('Registration failed. Please try again.');

    // When confirmation is required Supabase returns a user with no identities
    // for an email that is already registered (to avoid account enumeration).
    if ((user.identities ?? const []).isEmpty && res.session == null) {
      throw const AuthException('An account with this email already exists. Please sign in.');
    }

    if (res.session != null) {
      // Email confirmation is disabled on the project: we are signed in already.
      final model = await _loadUser(user);
      _emit(model);
      return model;
    }

    return UserModel(
      id: user.id,
      email: email,
      fullName: fullName,
      accountType: accountType,
      isEmailVerified: false,
      isOnboarded: false,
    );
  }

  @override
  Future<void> sendEmailVerification(String email) async {
    await _client.auth.resend(type: OtpType.signup, email: email);
  }

  @override
  Future<void> sendPasswordResetEmail(String email) async {
    String? redirectTo;
    if (kIsWeb) {
      redirectTo = Uri.base.replace(fragment: '/reset-password', query: '').toString();
    }
    await _client.auth.resetPasswordForEmail(email, redirectTo: redirectTo);
  }

  @override
  Future<void> updatePassword(String newPassword) async {
    if (_client.auth.currentSession == null) {
      throw const AuthException('Open the password reset link from your email first, then set a new password.');
    }
    await _client.auth.updateUser(UserAttributes(password: newPassword));
  }

  @override
  Future<UserModel> completeBuyerOnboarding(BuyerProfileData data) async {
    final authUser = _requireUser();
    final loc = splitLocation(data.location);
    await _ensureProfileRow(authUser);
    await _client.from('profiles').update({
      'full_name': data.name.trim(),
      'city': loc.city,
      'state': loc.state,
      if (data.phone != null && data.phone!.trim().isNotEmpty) 'phone': data.phone!.trim(),
      'role': UserAccountType.buyer.dbValue,
    }).eq('auth_user_id', authUser.id);

    final model = await _loadUser(authUser);
    _emit(model);
    return model;
  }

  @override
  Future<UserModel> completeArtisanOnboarding(ArtisanProfileData data) async {
    final authUser = _requireUser();
    final loc = splitLocation(data.villageLocation);
    final profile = await _ensureProfileRow(authUser);
    final profileId = profile['id'] as String;

    await _client.from('profiles').update({
      'full_name': data.artisanName.trim(),
      'city': loc.city,
      'state': loc.state,
      if (data.phone != null && data.phone!.trim().isNotEmpty) 'phone': data.phone!.trim(),
      'role': UserAccountType.artisan.dbValue,
    }).eq('auth_user_id', authUser.id);

    // `location` is deliberately not written. sellers.location is a PostGIS
    // geometry column, so posting the typed village string into it fails with
    // "parse error - invalid geometry" and the whole onboarding save is lost.
    // The text is not dropped: splitLocation() above already stored it as
    // profiles.city / profiles.state, which is what regionLabel renders.
    final sellerPayload = {
      'shop_name': data.storefrontName.trim(),
      'artisan_type': data.craftCategory,
      'bio': data.bio.trim(),
    };

    final existing = await _client.from('sellers').select('id').eq('profile_id', profileId).maybeSingle();
    if (existing == null) {
      await _client.from('sellers').insert({'profile_id': profileId, ...sellerPayload});
    } else {
      await _client.from('sellers').update(sellerPayload).eq('id', existing['id']);
    }

    final model = await _loadUser(authUser);
    _emit(model);
    return model;
  }

  @override
  Future<UserModel> setAccountType(UserAccountType accountType) async {
    final authUser = _requireUser();
    await _ensureProfileRow(authUser);
    await _client.from('profiles').update({'role': accountType.dbValue}).eq('auth_user_id', authUser.id);
    final model = await _loadUser(authUser);
    _emit(model);
    return model;
  }

  @override
  Future<void> signOut() async {
    await _client.auth.signOut();
    _emit(null);
  }

  User _requireUser() {
    final user = _client.auth.currentUser;
    if (user == null) throw const AuthException('You are not signed in.');
    return user;
  }

  Future<Map<String, dynamic>> _ensureProfileRow(User authUser) async {
    final existing = await _client.from('profiles').select().eq('auth_user_id', authUser.id).maybeSingle();
    if (existing != null) return existing;
    final created = await _createProfile(authUser);
    if (created == null) {
      throw const AuthException('Could not create your profile. Please try again.');
    }
    return created;
  }
}

/// Human-readable message for any error thrown by the auth layer.
String authErrorMessage(Object error) {
  if (error is AuthException) {
    final m = error.message;
    if (m.toLowerCase().contains('invalid login credentials')) {
      return 'Incorrect email or password.';
    }
    if (m.toLowerCase().contains('email not confirmed')) {
      return 'Please confirm your email address first. Check your inbox for the verification link.';
    }
    return m;
  }
  if (error is PostgrestException) return error.message;
  final text = error.toString();
  if (text.contains('SocketException') || text.contains('Failed host lookup') || text.contains('ClientException')) {
    return 'No internet connection. Please check your network and try again.';
  }
  return 'Something went wrong. Please try again.';
}

final supabaseClientProvider = Provider<SupabaseClient>((ref) {
  return Supabase.instance.client;
});

final supabaseAuthRepositoryProvider = Provider<AuthRepository>((ref) {
  final repo = SupabaseAuthRepository(ref.watch(supabaseClientProvider));
  ref.onDispose(repo.dispose);
  return repo;
});
