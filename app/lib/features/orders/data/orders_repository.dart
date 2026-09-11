import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../../../shared/models/order_models.dart';
import '../../auth/data/auth_repository.dart';
import '../../auth/data/supabase_auth_repository.dart';

const _orderSelect = '*, products(title, category, image_urls), sellers(shop_name)';

class OrderLineInput {
  final String productId;
  final String sellerId;
  final int quantity;
  final double unitPrice;

  const OrderLineInput({
    required this.productId,
    required this.sellerId,
    required this.quantity,
    required this.unitPrice,
  });
}

class OrdersRepository {
  final SupabaseClient _client;

  OrdersRepository(this._client);

  /// Orders placed by the signed-in buyer, newest first.
  Future<List<OrderRecord>> getBuyerOrders(String buyerAuthId) async {
    final res = await _client
        .from('orders')
        .select(_orderSelect)
        .eq('buyer_id', buyerAuthId)
        .order('created_at', ascending: false);
    return (res as List).cast<Map<String, dynamic>>().map(OrderRecord.fromRow).toList();
  }

  /// Orders a seller has to fulfil, newest first. Buyer contact details are
  /// resolved from `profiles` in a second query because `orders.buyer_id`
  /// has no foreign key PostgREST can embed through.
  Future<List<OrderRecord>> getSellerOrders(String sellerId) async {
    final res = await _client
        .from('orders')
        .select(_orderSelect)
        .eq('seller_id', sellerId)
        .order('created_at', ascending: false);
    final orders = (res as List).cast<Map<String, dynamic>>().map(OrderRecord.fromRow).toList();

    final buyerIds = orders.map((o) => o.buyerId).where((id) => id.isNotEmpty).toSet().toList();
    if (buyerIds.isEmpty) return orders;

    Map<String, Map<String, dynamic>> profilesByAuthId = {};
    try {
      final profiles = await _client
          .from('profiles')
          .select('auth_user_id, full_name, phone')
          .inFilter('auth_user_id', buyerIds);
      for (final p in (profiles as List).cast<Map<String, dynamic>>()) {
        profilesByAuthId[p['auth_user_id'] as String] = p;
      }
    } catch (_) {
      // RLS may hide other users' profiles; fall back to anonymous buyers.
    }

    return orders.map((o) {
      final p = profilesByAuthId[o.buyerId];
      if (p == null) return o;
      return OrderRecord(
        id: o.id,
        buyerId: o.buyerId,
        sellerId: o.sellerId,
        productId: o.productId,
        quantity: o.quantity,
        unitPrice: o.unitPrice,
        totalAmount: o.totalAmount,
        status: o.status,
        paymentStatus: o.paymentStatus,
        shippingAddress: o.shippingAddress,
        createdAt: o.createdAt,
        updatedAt: o.updatedAt,
        productTitle: o.productTitle,
        productCategory: o.productCategory,
        productImageUrl: o.productImageUrl,
        sellerShopName: o.sellerShopName,
        buyerName: p['full_name'] as String?,
        buyerPhone: p['phone'] as String?,
      );
    }).toList();
  }

  Future<OrderRecord?> getOrder(String orderId) async {
    final row = await _client.from('orders').select(_orderSelect).eq('id', orderId).maybeSingle();
    return row == null ? null : OrderRecord.fromRow(row);
  }

  /// Creates one `orders` row per line and returns them.
  Future<List<OrderRecord>> placeOrders({
    required String buyerAuthId,
    required List<OrderLineInput> lines,
    required String shippingAddress,
    String paymentStatus = 'paid',
  }) async {
    if (lines.isEmpty) return const [];
    final rows = lines
        .map((l) => {
              'buyer_id': buyerAuthId,
              'seller_id': l.sellerId,
              'product_id': l.productId,
              'quantity': l.quantity,
              'unit_price': l.unitPrice,
              'total_amount': l.unitPrice * l.quantity,
              'order_status': OrderStatus.pending.dbValue,
              'payment_status': paymentStatus,
              'shipping_address': shippingAddress,
            })
        .toList();
    final res = await _client.from('orders').insert(rows).select(_orderSelect);
    return (res as List).cast<Map<String, dynamic>>().map(OrderRecord.fromRow).toList();
  }

  Future<OrderRecord> updateStatus(String orderId, OrderStatus status) async {
    final row = await _client
        .from('orders')
        .update({'order_status': status.dbValue, 'updated_at': DateTime.now().toUtc().toIso8601String()})
        .eq('id', orderId)
        .select(_orderSelect)
        .single();
    return OrderRecord.fromRow(row);
  }
}

final ordersRepositoryProvider = Provider<OrdersRepository>((ref) {
  return OrdersRepository(ref.watch(supabaseClientProvider));
});

/// Orders for the signed-in buyer.
final buyerOrdersProvider = FutureProvider.autoDispose<List<OrderRecord>>((ref) async {
  final user = ref.watch(currentUserProvider);
  if (user == null) return const [];
  return ref.watch(ordersRepositoryProvider).getBuyerOrders(user.id);
});

/// Orders for the signed-in seller's storefront.
final sellerOrdersProvider = FutureProvider.autoDispose<List<OrderRecord>>((ref) async {
  final user = ref.watch(currentUserProvider);
  final sellerId = user?.sellerId;
  if (sellerId == null) return const [];
  return ref.watch(ordersRepositoryProvider).getSellerOrders(sellerId);
});
