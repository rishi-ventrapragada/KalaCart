import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../../../shared/models/product.dart';
import '../../auth/data/auth_repository.dart';
import '../../auth/data/supabase_auth_repository.dart';

const productSelect = '*, sellers(id, shop_name, artisan_type, bio, location), wholesale_pricing(*)';

class SupabaseProductsRepository {
  final SupabaseClient _client;

  SupabaseProductsRepository(this._client);

  List<Product> _mapList(dynamic res) =>
      (res as List).cast<Map<String, dynamic>>().map(Product.fromRow).toList();

  /// Published, active products for buyers, newest first.
  Future<List<Product>> getPublishedProducts({String? category, String? query, int limit = 100}) async {
    var q = _client
        .from('products')
        .select(productSelect)
        .eq('is_active', true)
        // Buyers see only admin-approved listings. Not ProductStatus.published
        // .dbValue: that writes 'pending', the state a seller's submission lands
        // in. Filtering on it here would show buyers unreviewed products.
        .eq('status', kBuyerVisibleStatus);
    if (category != null && category.isNotEmpty && category != 'All Crafts') {
      q = q.eq('category', category);
    }
    if (query != null && query.trim().isNotEmpty) {
      final term = '%${query.trim()}%';
      q = q.or('title.ilike.$term,description.ilike.$term,material.ilike.$term,category.ilike.$term');
    }
    final res = await q.order('created_at', ascending: false).limit(limit);
    return _mapList(res);
  }

  Future<Product?> getProduct(String id) async {
    if (id.isEmpty) return null;
    final row = await _client.from('products').select(productSelect).eq('id', id).maybeSingle();
    return row == null ? null : Product.fromRow(row);
  }

  Future<List<Product>> getProductsByIds(List<String> ids) async {
    if (ids.isEmpty) return const [];
    final res = await _client.from('products').select(productSelect).inFilter('id', ids);
    return _mapList(res);
  }

  /// Every product (any status) belonging to a seller, newest first.
  Future<List<Product>> getSellerProducts(String sellerId) async {
    final res = await _client
        .from('products')
        .select(productSelect)
        .eq('seller_id', sellerId)
        .order('created_at', ascending: false);
    return _mapList(res);
  }

  /// Published products of one seller, for the public storefront.
  Future<List<Product>> getSellerPublishedProducts(String sellerId) async {
    final res = await _client
        .from('products')
        .select(productSelect)
        .eq('seller_id', sellerId)
        .eq('is_active', true)
        // Public storefront: approved listings only, same rule as the catalogue.
        .eq('status', kBuyerVisibleStatus)
        .order('created_at', ascending: false);
    return _mapList(res);
  }

  Future<Product> createProduct({required String sellerId, required ProductInput input}) async {
    final row = await _client.from('products').insert(input.toRow(sellerId: sellerId)).select().single();
    final productId = row['id'] as String;
    await _replaceTiers(productId, input.wholesaleTiers);
    return (await getProduct(productId))!;
  }

  Future<Product> updateProduct({required String productId, required String sellerId, required ProductInput input}) async {
    final payload = input.toRow(sellerId: sellerId)..remove('seller_id');
    await _client.from('products').update(payload).eq('id', productId);
    await _replaceTiers(productId, input.wholesaleTiers);
    return (await getProduct(productId))!;
  }

  Future<Product> setStatus(String productId, ProductStatus status) async {
    await _client.from('products').update({
      'status': status.dbValue,
      'is_active': status != ProductStatus.archived,
    }).eq('id', productId);
    return (await getProduct(productId))!;
  }

  Future<Product> updateStock(String productId, int stock) async {
    await _client.from('products').update({'stock': stock}).eq('id', productId);
    return (await getProduct(productId))!;
  }

  Future<void> deleteProduct(String productId) async {
    await _client.from('wholesale_pricing').delete().eq('product_id', productId);
    await _client.from('products').delete().eq('id', productId);
  }

  Future<Product> duplicateProduct(Product source) async {
    final input = ProductInput(
      title: '${source.title} (Copy)',
      description: source.description,
      category: source.category,
      material: source.material,
      price: source.price,
      stock: source.stock,
      imageUrls: source.imageUrls,
      status: ProductStatus.draft,
      city: source.city,
      state: source.state,
      wholesaleTiers: source.wholesaleTiers,
    );
    return createProduct(sellerId: source.sellerId, input: input);
  }

  Future<void> _replaceTiers(String productId, List<WholesaleTier> tiers) async {
    await _client.from('wholesale_pricing').delete().eq('product_id', productId);
    final valid = tiers.where((t) => t.minQuantity > 0 && t.pricePerUnit > 0).toList();
    if (valid.isEmpty) return;
    await _client.from('wholesale_pricing').insert([
      for (final t in valid) {'product_id': productId, 'min_quantity': t.minQuantity, 'price': t.pricePerUnit},
    ]);
  }
}

final supabaseProductsRepositoryProvider = Provider<SupabaseProductsRepository>((ref) {
  return SupabaseProductsRepository(ref.watch(supabaseClientProvider));
});

/// Buyer-facing catalogue. Invalidate to refresh.
final publishedProductsProvider = FutureProvider<List<Product>>((ref) {
  return ref.watch(supabaseProductsRepositoryProvider).getPublishedProducts();
});

/// Search + category filter over the catalogue (server-side).
class CatalogQuery {
  final String category;
  final String search;
  const CatalogQuery({this.category = 'All Crafts', this.search = ''});

  @override
  bool operator ==(Object other) =>
      other is CatalogQuery && other.category == category && other.search == search;

  @override
  int get hashCode => Object.hash(category, search);
}

final filteredProductsProvider = FutureProvider.autoDispose.family<List<Product>, CatalogQuery>((ref, q) {
  return ref
      .watch(supabaseProductsRepositoryProvider)
      .getPublishedProducts(category: q.category, query: q.search);
});

final productProvider = FutureProvider.autoDispose.family<Product?, String>((ref, id) {
  return ref.watch(supabaseProductsRepositoryProvider).getProduct(id);
});

/// Products of the signed-in seller (all statuses).
final sellerProductsProvider = FutureProvider<List<Product>>((ref) async {
  final user = ref.watch(currentUserProvider);
  final sellerId = user?.sellerId;
  if (sellerId == null) return const [];
  return ref.watch(supabaseProductsRepositoryProvider).getSellerProducts(sellerId);
});

/// Published products of an arbitrary seller, for storefront pages.
final sellerPublishedProductsProvider = FutureProvider.autoDispose.family<List<Product>, String>((ref, sellerId) {
  return ref.watch(supabaseProductsRepositoryProvider).getSellerPublishedProducts(sellerId);
});
