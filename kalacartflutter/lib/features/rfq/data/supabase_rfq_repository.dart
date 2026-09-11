import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../../../shared/models/chat_rfq_models.dart';
import '../../auth/data/supabase_auth_repository.dart';

class SupabaseRfqRepository {
  final SupabaseClient _client;

  SupabaseRfqRepository(this._client);

  /// Fetch enquiries / RFQs for current user
  Future<List<BuyerRfqSubmission>> getEnquiries() async {
    try {
      final res = await _client
          .from('enquiries')
          .select('*, products(title, price)')
          .order('created_at', ascending: false);

      return (res as List).map((row) {
        final product = row['products'] as Map<String, dynamic>?;

        return BuyerRfqSubmission(
          id: row['id'] as String,
          title: product?['title'] as String? ?? 'Custom Craft Inquiry',
          category: 'Pottery & Terracotta',
          quantity: row['quantity'] as int? ?? 1,
          targetPricePerUnit: (product?['price'] as num?)?.toDouble() ?? 1000.0,
          customizationNotes: row['message'] as String? ?? '',
          deliveryRequiredBy: 'Within 30 Days',
          destinationPincode: '560038',
          createdAt: row['created_at'] != null ? DateTime.parse(row['created_at']) : DateTime.now(),
        );
      }).toList();
    } catch (_) {
      return [];
    }
  }

  /// Create a new RFQ / Enquiry
  Future<void> submitEnquiry({
    String? productId,
    required String message,
    required int quantity,
    String? guestName,
    String? guestContact,
  }) async {
    final user = _client.auth.currentUser;
    await _client.from('enquiries').insert({
      'product_id': productId,
      'buyer_id': user?.id,
      'message': message,
      'quantity': quantity,
      'status': 'pending',
      'guest_name': guestName,
      'guest_contact': guestContact,
    });
  }
}

final supabaseRfqRepositoryProvider = Provider<SupabaseRfqRepository>((ref) {
  return SupabaseRfqRepository(ref.watch(supabaseClientProvider));
});
