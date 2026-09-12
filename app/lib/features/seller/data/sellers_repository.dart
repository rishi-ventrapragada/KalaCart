import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../../auth/data/supabase_auth_repository.dart';

/// Public storefront view of a `sellers` row joined with its profile.
class SellerStorefront {
  final String id; // sellers.id
  final String profileId;
  final String shopName;
  final String artisanName;
  final String? artisanType;
  final String? bio;
  final String? location;
  final String? city;
  final String? state;
  final String? avatarUrl;
  final int? experienceYears;
  final bool isVerified;
  final DateTime? createdAt;

  const SellerStorefront({
    required this.id,
    required this.profileId,
    required this.shopName,
    required this.artisanName,
    this.artisanType,
    this.bio,
    this.location,
    this.city,
    this.state,
    this.avatarUrl,
    this.experienceYears,
    this.isVerified = false,
    this.createdAt,
  });

  String get regionLabel {
    if ((location ?? '').trim().isNotEmpty) return location!.trim();
    final bits = [city, state].where((s) => s != null && s.trim().isNotEmpty).cast<String>().toList();
    return bits.isEmpty ? 'India' : bits.join(', ');
  }

  factory SellerStorefront.fromRow(Map<String, dynamic> row) {
    final profile = row['profiles'] as Map<String, dynamic>?;
    return SellerStorefront(
      id: row['id'] as String,
      profileId: row['profile_id'] as String? ?? '',
      shopName: (row['shop_name'] as String?)?.trim().isNotEmpty == true ? row['shop_name'] : 'Artisan Studio',
      artisanName: (profile?['full_name'] as String?) ?? 'Master Artisan',
      artisanType: row['artisan_type'] as String?,
      bio: row['bio'] as String?,
      // Not row['location']: that column is PostGIS geometry, so casting it to
      // String throws once a row actually holds a point. city/state below carry
      // the place text.
      location: null,
      city: profile?['city'] as String?,
      state: profile?['state'] as String?,
      avatarUrl: (profile?['avatar_url'] as String?) ?? profile?['profile_photo'] as String?,
      experienceYears: (row['experience'] as num?)?.toInt(),
      isVerified: profile?['is_verified'] as bool? ?? false,
      createdAt: DateTime.tryParse(row['created_at']?.toString() ?? ''),
    );
  }
}

class SellersRepository {
  final SupabaseClient _client;

  SellersRepository(this._client);

  static const _select =
      // `location` is not selected: it is PostGIS geometry and nothing reads it.
      'id, profile_id, shop_name, artisan_type, bio, experience, created_at, profiles(full_name, city, state, avatar_url, profile_photo, is_verified)';

  Future<SellerStorefront?> getById(String sellerId) async {
    final row = await _client.from('sellers').select(_select).eq('id', sellerId).maybeSingle();
    return row == null ? null : SellerStorefront.fromRow(row);
  }

  Future<List<SellerStorefront>> getAll({int limit = 20}) async {
    final res = await _client.from('sellers').select(_select).order('created_at', ascending: false).limit(limit);
    return (res as List).cast<Map<String, dynamic>>().map(SellerStorefront.fromRow).toList();
  }

  Future<void> updateStorefront({
    required String sellerId,
    required String shopName,
    required String artisanType,
    required String bio,
    required String location,
    int? experienceYears,
  }) async {
    // `location` is accepted for call-site compatibility but not written:
    // sellers.location is a PostGIS geometry column and a plain place name
    // fails it with "parse error - invalid geometry". Place text belongs on
    // profiles.city / profiles.state.
    await _client.from('sellers').update({
      'shop_name': shopName.trim(),
      'artisan_type': artisanType,
      'bio': bio.trim(),
      if (experienceYears != null) 'experience': experienceYears,
    }).eq('id', sellerId);
  }
}

final sellersRepositoryProvider = Provider<SellersRepository>((ref) {
  return SellersRepository(ref.watch(supabaseClientProvider));
});

final sellerStorefrontProvider = FutureProvider.autoDispose.family<SellerStorefront?, String>((ref, sellerId) {
  return ref.watch(sellersRepositoryProvider).getById(sellerId);
});

final featuredSellersProvider = FutureProvider.autoDispose<List<SellerStorefront>>((ref) {
  return ref.watch(sellersRepositoryProvider).getAll(limit: 10);
});
