import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../shared/models/product.dart';

/// A product in the local cart. The cart lives in memory for the session;
/// orders are only persisted when checkout succeeds.
class CartItem {
  final Product product;
  final int quantity;
  final String? customNote;

  const CartItem({required this.product, this.quantity = 1, this.customNote});

  CartItem copyWith({Product? product, int? quantity, String? customNote}) => CartItem(
        product: product ?? this.product,
        quantity: quantity ?? this.quantity,
        customNote: customNote ?? this.customNote,
      );

  double get unitPrice => product.unitPriceFor(quantity);
  double get totalPrice => unitPrice * quantity;
  bool get isWholesaleRate => unitPrice < product.price;
}

class CartNotifier extends StateNotifier<List<CartItem>> {
  CartNotifier() : super(const []);

  void addToCart(Product product, {int quantity = 1, String? note}) {
    final index = state.indexWhere((item) => item.product.id == product.id);
    if (index >= 0) {
      final existing = state[index];
      state = [
        ...state.sublist(0, index),
        existing.copyWith(quantity: existing.quantity + quantity, product: product),
        ...state.sublist(index + 1),
      ];
    } else {
      state = [...state, CartItem(product: product, quantity: quantity, customNote: note)];
    }
  }

  void updateQuantity(String productId, int newQuantity) {
    if (newQuantity <= 0) {
      removeFromCart(productId);
      return;
    }
    state = state.map((item) => item.product.id == productId ? item.copyWith(quantity: newQuantity) : item).toList();
  }

  void removeFromCart(String productId) {
    state = state.where((item) => item.product.id != productId).toList();
  }

  void clearCart() => state = const [];
}

final cartProvider = StateNotifierProvider<CartNotifier, List<CartItem>>((ref) => CartNotifier());

final cartSubtotalProvider = Provider<double>((ref) {
  return ref.watch(cartProvider).fold(0.0, (sum, item) => sum + item.totalPrice);
});

final cartItemCountProvider = Provider<int>((ref) {
  return ref.watch(cartProvider).fold(0, (count, item) => count + item.quantity);
});

/// Free delivery above this subtotal; otherwise a flat fee applies.
const double kFreeDeliveryThreshold = 3000;
const double kDeliveryFee = 150;

final cartDeliveryFeeProvider = Provider<double>((ref) {
  final subtotal = ref.watch(cartSubtotalProvider);
  if (subtotal <= 0) return 0;
  return subtotal >= kFreeDeliveryThreshold ? 0 : kDeliveryFee;
});

final cartTotalProvider = Provider<double>((ref) {
  return ref.watch(cartSubtotalProvider) + ref.watch(cartDeliveryFeeProvider);
});
