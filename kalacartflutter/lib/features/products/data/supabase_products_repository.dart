import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../../../shared/models/buyer_models.dart';
import '../../auth/data/supabase_auth_repository.dart';

class SupabaseProductsRepository {
  final SupabaseClient _client;

  SupabaseProductsRepository(this._client);

  /// Fetch all active products
  Future<List<BuyerCraftProduct>> getProducts() async {
    try {
      final res = await _client
          .from('products')
          .select('*, sellers(shop_name, artisan_type), wholesale_pricing(*)')
          .eq('is_active', true)
          .order('created_at', ascending: false);

      return (res as List).map((row) {
        final seller = row['sellers'] as Map<String, dynamic>?;
        final wholesaleList = row['wholesale_pricing'] as List? ?? [];

        final wholesaleTiers = wholesaleList.map((w) {
          return WholesaleTier(
            minQuantity: w['min_quantity'] as int? ?? 1,
            pricePerUnit: (w['price'] as num?)?.toDouble() ?? 0.0,
          );
        }).toList();

        return BuyerCraftProduct(
          id: row['id'] as String,
          title: row['title'] as String? ?? 'Handcrafted Art',
          artisanName: seller?['shop_name'] as String? ?? 'Master Artisan',
          artisanId: row['seller_id'] as String? ?? 'art-001',
          villageLocation: row['city'] as String? ?? 'Jaipur',
          state: row['state'] as String? ?? 'Rajasthan',
          category: row['category'] as String? ?? 'Pottery & Terracotta',
          material: row['material'] as String? ?? 'Natural Clay',
          dimensions: '12" Height x 6" Base',
          weight: '1.2 kg',
          retailPrice: (row['price'] as num?)?.toDouble() ?? 1200.0,
          wholesaleTiers: wholesaleTiers,
          description: row['description'] as String? ?? '',
          isGiTagged: true,
          passport: const CraftPassportData(
            passportId: 'GI-IN-RAJ-2026-BP-0941',
            giRegistrationNumber: 'GI/2026/RAJ/0941',
            artisanSignature: 'Master Craftsman Verification',
            geoCoordinates: '26.9124° N, 75.7873° E',
            craftClusterName: 'Jaipur Blue Pottery Guild',
            rawMaterialProvenance: '100% Sourced from Makrana & Bikaner',
            handcraftHours: '18 Hours',
          ),
        );
      }).toList();
    } catch (_) {
      return [];
    }
  }

  /// Create a new product in the database
  Future<void> createProduct({
    required String title,
    required String description,
    required String category,
    required String material,
    required double price,
    required int stock,
    required List<String> imageUrls,
  }) async {
    final user = _client.auth.currentUser;
    if (user == null) return;

    await _client.from('products').insert({
      'seller_id': user.id,
      'title': title,
      'description': description,
      'category': category,
      'material': material,
      'price': price,
      'stock': stock,
      'image_urls': imageUrls,
      'is_active': true,
      'status': 'published',
    });
  }
}

final supabaseProductsRepositoryProvider = Provider<SupabaseProductsRepository>((ref) {
  return SupabaseProductsRepository(ref.watch(supabaseClientProvider));
});
