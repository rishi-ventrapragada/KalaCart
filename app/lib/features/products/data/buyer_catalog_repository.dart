import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../shared/models/buyer_models.dart';

class CartItem {
  final BuyerCraftProduct product;
  final int quantity;
  final String? customNote;

  const CartItem({
    required this.product,
    this.quantity = 1,
    this.customNote,
  });

  CartItem copyWith({
    BuyerCraftProduct? product,
    int? quantity,
    String? customNote,
  }) {
    return CartItem(
      product: product ?? this.product,
      quantity: quantity ?? this.quantity,
      customNote: customNote ?? this.customNote,
    );
  }

  double get unitPrice {
    // Check wholesale tier pricing
    for (final tier in product.wholesaleTiers) {
      if (quantity >= tier.minQuantity &&
          (tier.maxQuantity == null || quantity <= tier.maxQuantity!)) {
        return tier.pricePerUnit;
      }
    }
    return product.retailPrice;
  }

  double get totalPrice => unitPrice * quantity;
}

class CartNotifier extends StateNotifier<List<CartItem>> {
  CartNotifier()
      : super([
          CartItem(
            product: mockCraftCatalog[0],
            quantity: 2,
          ),
          CartItem(
            product: mockCraftCatalog[2],
            quantity: 1,
          ),
        ]);

  void addToCart(BuyerCraftProduct product, {int quantity = 1, String? note}) {
    final index = state.indexWhere((item) => item.product.id == product.id);
    if (index >= 0) {
      final existing = state[index];
      state = [
        ...state.sublist(0, index),
        existing.copyWith(quantity: existing.quantity + quantity),
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
    state = state.map((item) {
      if (item.product.id == productId) {
        return item.copyWith(quantity: newQuantity);
      }
      return item;
    }).toList();
  }

  void removeFromCart(String productId) {
    state = state.where((item) => item.product.id != productId).toList();
  }

  void clearCart() {
    state = [];
  }
}

final cartProvider = StateNotifierProvider<CartNotifier, List<CartItem>>((ref) {
  return CartNotifier();
});

final cartSubtotalProvider = Provider<double>((ref) {
  final cart = ref.watch(cartProvider);
  return cart.fold(0.0, (sum, item) => sum + item.totalPrice);
});

final cartItemCountProvider = Provider<int>((ref) {
  final cart = ref.watch(cartProvider);
  return cart.fold(0, (count, item) => count + item.quantity);
});

// Master Mock Database for Handicrafts
final List<BuyerCraftProduct> mockCraftCatalog = [
  const BuyerCraftProduct(
    id: 'prod-001',
    title: 'Heritage Cobalt Floral Blue Pottery Vase',
    artisanId: 'art-002',
    artisanName: 'Dr. Kripal Kumbh Studio',
    villageLocation: 'Kot Jewar, Jaipur',
    state: 'Rajasthan',
    retailPrice: 2450,
    originalPrice: 2850,
    wholesaleTiers: [
      WholesaleTier(minQuantity: 5, maxQuantity: 19, pricePerUnit: 1950),
      WholesaleTier(minQuantity: 20, maxQuantity: 99, pricePerUnit: 1650),
      WholesaleTier(minQuantity: 100, pricePerUnit: 1350),
    ],
    rating: 4.95,
    reviewCount: 142,
    category: 'Pottery & Terracotta',
    material: 'Quartz Powder, Fuller Earth (Multani Mitti), Natural Cobalt Oxide Glaze',
    dimensions: '14" Height x 7" Diameter',
    weight: '1.45 kg',
    description: 'Authentic GI-Certified Jaipur Blue Pottery crafted without clay using an ancient formulation of ground quartz stone, glass, plant gum, and natural mineral pigments. Hand-painted with traditional Mughal floral motifs and fired once at low kiln temperatures.',
    craftTechniques: ['Hand Glazing', 'Mineral Pigment Painting', 'Low Fire Kiln', 'GI Tagged Authenticity'],
    isGiTagged: true,
    isCustomizable: true,
    stockCount: 18,
    passport: CraftPassportData(
      passportId: 'GI-IN-RAJ-2026-BP-0941',
      giRegistrationNumber: 'GI/APPLICATION/NO/04',
      artisanSignature: 'Kripal Kumbh Master Guild Seal',
      geoCoordinates: '26.9124° N, 75.7873° E',
      craftClusterName: 'Jaipur Blue Pottery Cluster, Rajasthan',
      rawMaterialProvenance: 'Sourced directly from Makrana quartz deposits & Barmer fuller earth.',
      handcraftHours: '28 Handcrafting Hours',
      sustainabilityRating: 'A+ (100% Eco-Friendly Non-Clay Ceramic)',
    ),
    reviews: [
      CraftReview(
        id: 'rev-01',
        userName: 'Priya Sundaram',
        userLocation: 'Mumbai, Maharashtra',
        rating: 5.0,
        date: '2 days ago',
        comment: 'The glaze finish and intricate floral motifs are breathtaking. The digital craft passport showed the exact artisan village coordinates!',
      ),
      CraftReview(
        id: 'rev-02',
        userName: 'Aarav Malhotra',
        userLocation: 'New Delhi',
        rating: 4.9,
        date: '1 week ago',
        comment: 'Ordered a batch for corporate Diwali gifting. Packing was exceptional and the wholesale pricing tier applied seamlessly.',
      ),
    ],
  ),
  const BuyerCraftProduct(
    id: 'prod-002',
    title: 'Natural Indigo Handloom Kalamkari Saree',
    artisanId: 'art-004',
    artisanName: 'Pedana Heritage Kalamkari Collective',
    villageLocation: 'Pedana, Machilipatnam',
    state: 'Andhra Pradesh',
    retailPrice: 5600,
    originalPrice: 6500,
    wholesaleTiers: [
      WholesaleTier(minQuantity: 3, maxQuantity: 9, pricePerUnit: 4800),
      WholesaleTier(minQuantity: 10, maxQuantity: 49, pricePerUnit: 4200),
      WholesaleTier(minQuantity: 50, pricePerUnit: 3700),
    ],
    rating: 4.9,
    reviewCount: 96,
    category: 'Handloom & Textiles',
    material: 'Pure Organic Cotton & Plant-Derived Natural Indigo Dyes',
    dimensions: '6.5 Meters (Includes running blouse piece)',
    weight: '620 grams',
    description: 'Machilipatnam Machilipatnam style Kalamkari block printed with teakwood blocks and dyed using natural vegetable colours, myrobalan and flowing canal waters.',
    craftTechniques: ['Hand Block Printing', 'Canal Water Treatment', 'Organic Indigo Fermentation'],
    isGiTagged: true,
    isCustomizable: false,
    stockCount: 8,
    passport: CraftPassportData(
      passportId: 'GI-IN-AP-2026-KLM-0182',
      giRegistrationNumber: 'GI/APPLICATION/NO/19',
      artisanSignature: 'Pedana Handloom Society Seal',
      geoCoordinates: '16.2570° N, 81.1444° E',
      craftClusterName: 'Pedana Craft Cluster, Krishna District',
      rawMaterialProvenance: 'Guntur organic handloom cotton & fermented indigo leaves.',
      handcraftHours: '42 Handcrafting Hours',
    ),
  ),
  const BuyerCraftProduct(
    id: 'prod-003',
    title: 'Dhokra Lost-Wax Bell Metal Nandi Figurine',
    artisanId: 'art-003',
    artisanName: 'Bastar Bell Metal Guild',
    villageLocation: 'Kondagaon, Bastar',
    state: 'Chhattisgarh',
    retailPrice: 3200,
    originalPrice: 3800,
    wholesaleTiers: [
      WholesaleTier(minQuantity: 5, maxQuantity: 19, pricePerUnit: 2600),
      WholesaleTier(minQuantity: 20, pricePerUnit: 2100),
    ],
    rating: 4.88,
    reviewCount: 68,
    category: 'Brass & Metal Craft',
    material: 'Recycled Bell Metal & Pure Beeswax Core',
    dimensions: '9" L x 5" W x 8" H',
    weight: '2.1 kg',
    description: 'Preserving a 4,000-year-old non-ferrous lost-wax metal casting craft that traces directly back to the Dancing Girl of Mohenjo-daro.',
    craftTechniques: ['Lost-Wax Casting (Cire Perdue)', 'Beeswax Wire Modeling', 'Clay Mold Baking'],
    isGiTagged: true,
    isCustomizable: true,
    stockCount: 14,
    passport: CraftPassportData(
      passportId: 'GI-IN-CHG-2026-DHK-4421',
      giRegistrationNumber: 'GI/APPLICATION/NO/83',
      artisanSignature: 'Bastar Tribal Crafts Guild',
      geoCoordinates: '19.5984° N, 81.6688° E',
      craftClusterName: 'Kondagaon Dhokra Cluster',
      rawMaterialProvenance: 'Wild beeswax from Bastar forests and riverbed alluvial clay.',
      handcraftHours: '36 Handcrafting Hours',
    ),
  ),
  const BuyerCraftProduct(
    id: 'prod-004',
    title: 'Madhubani Kohbar Tree of Life Fine Art',
    artisanId: 'art-005',
    artisanName: 'Mithila Mahila Kala Kendra',
    villageLocation: 'Ranti Village, Madhubani',
    state: 'Bihar',
    retailPrice: 4800,
    originalPrice: 5500,
    wholesaleTiers: [
      WholesaleTier(minQuantity: 5, pricePerUnit: 3800),
    ],
    rating: 5.0,
    reviewCount: 110,
    category: 'Paintings & Madhubani',
    material: 'Handmade Acid-Free Cotton Paper & Natural Twig Pigments',
    dimensions: '22" x 30" (Unframed Canvas Sheet)',
    weight: '350 grams',
    description: 'Authentic Bharni & Kachni style Mithila painting created with bamboo twigs and natural dyes extracted from turmeric, indigo, soot, and marigold.',
    craftTechniques: ['Bamboo Twig Drawing', 'Mineral Pigment Mixing', 'Mithila Ritual Art'],
    isGiTagged: true,
    isCustomizable: true,
    stockCount: 6,
    passport: CraftPassportData(
      passportId: 'GI-IN-BIH-2026-MDH-8820',
      giRegistrationNumber: 'GI/APPLICATION/NO/105',
      artisanSignature: 'Mithila National Awardee Consortium',
      geoCoordinates: '26.3540° N, 86.0736° E',
      craftClusterName: 'Madhubani District Art Guild',
      rawMaterialProvenance: 'Handmade rag cotton sheet infused with cow dung wash.',
      handcraftHours: '48 Handcrafting Hours',
    ),
  ),
];

final buyerCatalogProvider = Provider<List<BuyerCraftProduct>>((ref) {
  return mockCraftCatalog;
});

final singleProductProvider = Provider.family<BuyerCraftProduct?, String>((ref, id) {
  final catalog = ref.watch(buyerCatalogProvider);
  return catalog.firstWhere((p) => p.id == id, orElse: () => catalog.first);
});
