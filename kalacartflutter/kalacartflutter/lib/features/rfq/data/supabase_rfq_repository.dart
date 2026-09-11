import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../../../shared/models/enquiry_models.dart';
import '../../auth/data/auth_repository.dart';
import '../../auth/data/supabase_auth_repository.dart';

const _enquirySelect =
    '*, products(id, title, category, price, image_urls, seller_id, sellers(id, shop_name, profile_id))';

/// RFQs are rows of `enquiries`: a buyer asks a seller about one product for a
/// given quantity. Structured RFQ fields live inside `message` (see [RfqDetails]).
class SupabaseRfqRepository {
  final SupabaseClient _client;

  SupabaseRfqRepository(this._client);

  /// Enquiries raised by the signed-in buyer, newest first.
  Future<List<Enquiry>> getBuyerEnquiries(String buyerAuthId) async {
    final res = await _client
        .from('enquiries')
        .select(_enquirySelect)
        .eq('buyer_id', buyerAuthId)
        .order('created_at', ascending: false);
    return (res as List).cast<Map<String, dynamic>>().map(Enquiry.fromRow).toList();
  }

  /// Enquiries about any product owned by [sellerId], newest first.
  Future<List<Enquiry>> getSellerEnquiries(String sellerId) async {
    final res = await _client
        .from('enquiries')
        .select(_enquirySelect)
        .eq('products.seller_id', sellerId)
        .not('products', 'is', null)
        .order('created_at', ascending: false);
    return (res as List)
        .cast<Map<String, dynamic>>()
        .map(Enquiry.fromRow)
        .where((e) => e.sellerId == sellerId)
        .toList();
  }

  Future<Enquiry?> getEnquiry(String id) async {
    final row = await _client.from('enquiries').select(_enquirySelect).eq('id', id).maybeSingle();
    return row == null ? null : Enquiry.fromRow(row);
  }

  Future<Enquiry> submitEnquiry({
    required String buyerAuthId,
    required String productId,
    required int quantity,
    required RfqDetails details,
  }) async {
    final row = await _client
        .from('enquiries')
        .insert({
          'product_id': productId,
          'buyer_id': buyerAuthId,
          'message': details.serialize(),
          'quantity': quantity,
          'status': EnquiryStatus.pending.dbValue,
        })
        .select(_enquirySelect)
        .single();
    return Enquiry.fromRow(row);
  }

  Future<Enquiry> updateStatus(String id, EnquiryStatus status) async {
    final row = await _client
        .from('enquiries')
        .update({'status': status.dbValue})
        .eq('id', id)
        .select(_enquirySelect)
        .single();
    return Enquiry.fromRow(row);
  }
}

final supabaseRfqRepositoryProvider = Provider<SupabaseRfqRepository>((ref) {
  return SupabaseRfqRepository(ref.watch(supabaseClientProvider));
});

final buyerEnquiriesProvider = FutureProvider.autoDispose<List<Enquiry>>((ref) async {
  final user = ref.watch(currentUserProvider);
  if (user == null) return const [];
  return ref.watch(supabaseRfqRepositoryProvider).getBuyerEnquiries(user.id);
});

final sellerEnquiriesProvider = FutureProvider.autoDispose<List<Enquiry>>((ref) async {
  final user = ref.watch(currentUserProvider);
  final sellerId = user?.sellerId;
  if (sellerId == null) return const [];
  return ref.watch(supabaseRfqRepositoryProvider).getSellerEnquiries(sellerId);
});

final enquiryProvider = FutureProvider.autoDispose.family<Enquiry?, String>((ref, id) {
  return ref.watch(supabaseRfqRepositoryProvider).getEnquiry(id);
});
