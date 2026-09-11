import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../shared/models/buyer_models.dart';
import '../../../shared/models/seller_models.dart';

// Initial Mock Seller Products
final List<SellerProduct> initialSellerProducts = [
  SellerProduct(
    id: 'sp-001',
    title: 'Heritage Cobalt Floral Blue Pottery Vase',
    category: 'Pottery & Terracotta',
    retailPrice: 2450,
    originalPrice: 2850,
    stockQuantity: 18,
    status: ProductStatus.published,
    viewsCount: 1420,
    salesCount: 24,
    totalRevenue: 58800,
    material: 'Quartz Powder, Fuller Earth, Cobalt Oxide Glaze',
    dimensions: '14" Height x 7" Diameter',
    weight: '1.45 kg',
    description: 'Authentic GI-Certified Jaipur Blue Pottery crafted without clay using quartz stone and natural mineral glazes.',
    translations: {
      'hi': 'पारंपरिक जयपुर ब्लू पॉटरी फूलदान - प्राकृतिक कोबाल्ट ऑक्साइड ग्लेज़ के साथ हस्तनिर्मित।',
      'te': 'సాంప్రదాయ జైపూర్ బ్లూ పాటర్ గ్లాస్ - స్వచ్ఛమైన సహజ రంగులు.',
      'ta': 'பாரம்பரிய ஜெய்ப்பூர் நீல மட்பாண்ட பூச்சாடி.',
      'bn': 'ঐতিহ্যবাহী জয়পুর নীল মৃৎশিল্প ফুলদানি।',
    },
    isGiTagged: true,
    passportId: 'GI-IN-RAJ-2026-BP-0941',
    craftTechniques: ['Hand Glazing', 'Mineral Pigment Painting', 'Low Fire Kiln'],
    wholesaleTiers: const [
      WholesaleTier(minQuantity: 5, maxQuantity: 19, pricePerUnit: 1950),
      WholesaleTier(minQuantity: 20, maxQuantity: 99, pricePerUnit: 1650),
      WholesaleTier(minQuantity: 100, pricePerUnit: 1350),
    ],
    createdAt: DateTime.now().subtract(const Duration(days: 45)),
  ),
  SellerProduct(
    id: 'sp-002',
    title: 'Hand-Carved Ceramic Mughal Tile Coasters (Set of 4)',
    category: 'Pottery & Terracotta',
    retailPrice: 950,
    originalPrice: 1200,
    stockQuantity: 42,
    status: ProductStatus.published,
    viewsCount: 890,
    salesCount: 52,
    totalRevenue: 49400,
    material: 'Glazed Quartzite & Multani Mitti',
    dimensions: '4" x 4" Each',
    weight: '480 grams',
    description: 'Intricate Persian floral patterns painted by master craftsmen with heat-resistant enamel.',
    translations: {
      'hi': 'हस्तनिर्मित मुग़ल टाइल कोस्टर्स (4 का सेट)।',
      'te': 'మొఘల్ డిజైన్ సెరామిక్ కోస్టర్లు.',
    },
    isGiTagged: true,
    passportId: 'GI-IN-RAJ-2026-BP-0942',
    craftTechniques: ['Tile Pressing', 'Freehand Motifs'],
    wholesaleTiers: const [
      WholesaleTier(minQuantity: 10, maxQuantity: 49, pricePerUnit: 750),
      WholesaleTier(minQuantity: 50, pricePerUnit: 600),
    ],
    createdAt: DateTime.now().subtract(const Duration(days: 30)),
  ),
  SellerProduct(
    id: 'sp-003',
    title: 'Turquoise Lattice Terracotta Hanging Planter',
    category: 'Pottery & Terracotta',
    retailPrice: 1350,
    stockQuantity: 8,
    status: ProductStatus.draft,
    viewsCount: 45,
    salesCount: 0,
    totalRevenue: 0,
    material: 'Natural Red Clay & Turquoise Oxide',
    dimensions: '8" Diameter x 6" Height',
    weight: '820 grams',
    description: 'Draft listing prepared via AI Catalogue Studio. Pending final kiln drying verification.',
    translations: {
      'hi': 'फ़िरोज़ा जालीदार टेराकोटा हैंगिंग प्लांटर (ड्राफ्ट)।',
    },
    isGiTagged: true,
    passportId: 'GI-IN-RAJ-2026-BP-DRAFT-03',
    craftTechniques: ['Jali Lattice Cutting', 'Clay Wheel'],
    wholesaleTiers: const [],
    createdAt: DateTime.now().subtract(const Duration(days: 2)),
  ),
  SellerProduct(
    id: 'sp-004',
    title: 'Royal Indigo Palace Decanter & Tumbler Set',
    category: 'Pottery & Terracotta',
    retailPrice: 3800,
    originalPrice: 4500,
    stockQuantity: 5,
    status: ProductStatus.published,
    viewsCount: 620,
    salesCount: 6,
    totalRevenue: 22800,
    material: 'Quartz Powder, Copper Oxide, Gold Leaf Trim',
    dimensions: '16" Height with 4 tumblers',
    weight: '2.2 kg',
    description: 'Limited artisan edition recreating 18th-century royal court dinnerware.',
    translations: {
      'hi': 'शाही इंडिगो पैलेस डिकैन्टर एवं गिलास सेट।',
    },
    isGiTagged: true,
    passportId: 'GI-IN-RAJ-2026-BP-0944',
    craftTechniques: ['Gold Leaf Gilding', 'Mineral Glaze'],
    wholesaleTiers: const [
      WholesaleTier(minQuantity: 5, pricePerUnit: 2900),
    ],
    createdAt: DateTime.now().subtract(const Duration(days: 15)),
  ),
];

// Seller Product Notifier
class SellerProductNotifier extends StateNotifier<List<SellerProduct>> {
  SellerProductNotifier() : super(initialSellerProducts);

  void addProduct(SellerProduct product) {
    state = [product, ...state];
  }

  void updateProduct(SellerProduct product) {
    state = state.map((p) => p.id == product.id ? product : p).toList();
  }

  void duplicateProduct(String id) {
    final existing = state.firstWhere((p) => p.id == id);
    final duplicated = existing.copyWith(
      id: 'sp-${DateTime.now().millisecondsSinceEpoch}',
      title: '${existing.title} (Copy)',
      status: ProductStatus.draft,
      viewsCount: 0,
      salesCount: 0,
      totalRevenue: 0,
      createdAt: DateTime.now(),
    );
    state = [duplicated, ...state];
  }

  void deleteProduct(String id) {
    state = state.where((p) => p.id != id).toList();
  }

  void toggleStatus(String id) {
    state = state.map((p) {
      if (p.id == id) {
        final newStatus = p.status == ProductStatus.published
            ? ProductStatus.draft
            : ProductStatus.published;
        return p.copyWith(status: newStatus);
      }
      return p;
    }).toList();
  }
}

final sellerProductsProvider = StateNotifierProvider<SellerProductNotifier, List<SellerProduct>>((ref) {
  return SellerProductNotifier();
});

// Initial Mock Orders
final List<SellerOrder> initialSellerOrders = [
  SellerOrder(
    id: 'ord-101',
    orderNumber: 'KC-2026-89412',
    buyerName: 'Aarav Malhotra',
    buyerPhone: '+91 98112 34567',
    buyerAddress: 'A-42, Vasant Vihar, New Delhi - 110057',
    items: const [
      SellerOrderItem(
        productId: 'sp-001',
        productTitle: 'Heritage Cobalt Floral Blue Pottery Vase',
        quantity: 2,
        unitPrice: 2450,
      ),
    ],
    totalAmount: 4900,
    status: OrderStatus.pending,
    orderDate: DateTime.now().subtract(const Duration(hours: 3)),
  ),
  SellerOrder(
    id: 'ord-102',
    orderNumber: 'KC-2026-89390',
    buyerName: 'Priya Sundaram',
    buyerPhone: '+91 97234 56789',
    buyerAddress: 'B-12, Indiranagar, Bengaluru - 560038',
    items: const [
      SellerOrderItem(
        productId: 'sp-002',
        productTitle: 'Hand-Carved Ceramic Mughal Tile Coasters',
        quantity: 4,
        unitPrice: 950,
      ),
    ],
    totalAmount: 3800,
    status: OrderStatus.accepted,
    orderDate: DateTime.now().subtract(const Duration(hours: 18)),
  ),
  SellerOrder(
    id: 'ord-103',
    orderNumber: 'KC-2026-89215',
    buyerName: 'The Craft Collective India',
    buyerPhone: '+91 98450 11223',
    buyerAddress: 'Unit 402, Lower Parel, Mumbai - 400013',
    items: const [
      SellerOrderItem(
        productId: 'sp-001',
        productTitle: 'Heritage Cobalt Floral Blue Pottery Vase',
        quantity: 20,
        unitPrice: 1650,
        isWholesale: true,
      ),
    ],
    totalAmount: 33000,
    status: OrderStatus.processing,
    orderDate: DateTime.now().subtract(const Duration(days: 2)),
    trackingNumber: 'DELHIVERY-AWB-998812',
    courierPartner: 'Delhivery Express Artisan SafePack',
  ),
  SellerOrder(
    id: 'ord-104',
    orderNumber: 'KC-2026-88940',
    buyerName: 'Meenakshi Iyer',
    buyerPhone: '+91 94440 98765',
    buyerAddress: '14/2, Besant Nagar, Chennai - 600090',
    items: const [
      SellerOrderItem(
        productId: 'sp-004',
        productTitle: 'Royal Indigo Palace Decanter Set',
        quantity: 1,
        unitPrice: 3800,
      ),
    ],
    totalAmount: 3800,
    status: OrderStatus.shipped,
    orderDate: DateTime.now().subtract(const Duration(days: 4)),
    trackingNumber: 'BLUE-DART-7766554',
    courierPartner: 'BlueDart Air Craft Cargo',
  ),
  SellerOrder(
    id: 'ord-105',
    orderNumber: 'KC-2026-88410',
    buyerName: 'Rajesh Shah',
    buyerPhone: '+91 98200 44556',
    buyerAddress: 'Navrangpura, Ahmedabad - 380009',
    items: const [
      SellerOrderItem(
        productId: 'sp-002',
        productTitle: 'Hand-Carved Ceramic Mughal Tile Coasters',
        quantity: 2,
        unitPrice: 950,
      ),
    ],
    totalAmount: 1900,
    status: OrderStatus.delivered,
    orderDate: DateTime.now().subtract(const Duration(days: 8)),
    trackingNumber: 'INDIA-POST-SPEED-443322',
    courierPartner: 'India Post Speed Post',
  ),
];

// Seller Orders Notifier
class SellerOrderNotifier extends StateNotifier<List<SellerOrder>> {
  SellerOrderNotifier() : super(initialSellerOrders);

  void updateOrderStatus(String orderId, OrderStatus newStatus, {String? tracking, String? courier}) {
    state = state.map((order) {
      if (order.id == orderId) {
        return order.copyWith(
          status: newStatus,
          trackingNumber: tracking ?? order.trackingNumber,
          courierPartner: courier ?? order.courierPartner,
        );
      }
      return order;
    }).toList();
  }

  void cancelOrder(String orderId) {
    updateOrderStatus(orderId, OrderStatus.cancelled);
  }
}

final sellerOrdersProvider = StateNotifierProvider<SellerOrderNotifier, List<SellerOrder>>((ref) {
  return SellerOrderNotifier();
});

// Initial Mock RFQs
final List<SellerRfq> initialSellerRfqs = [
  SellerRfq(
    id: 'rfq-201',
    rfqNumber: 'RFQ-IN-2026-081',
    buyerName: 'Ananya Deshmukh',
    buyerCompany: 'Heritage Retail & Boutiques LLP',
    buyerLocation: 'Mumbai, Maharashtra',
    craftRequired: 'Custom Glazed Cobalt Blue Pottery Vases with Corporate Crest',
    quantityRequired: 50,
    targetBudget: 75000,
    deliveryDeadline: 'Within 25 Days',
    status: RfqStatus.incoming,
    specifications: 'Need 50 units of 12-inch cobalt blue ceramic vases with engraved silver emblem for annual corporate celebration. Must be authentic GI-tagged Jaipur pottery.',
    postedAt: DateTime.now().subtract(const Duration(hours: 6)),
  ),
  SellerRfq(
    id: 'rfq-202',
    rfqNumber: 'RFQ-IN-2026-079',
    buyerName: 'Vikramaditya Hotels',
    buyerCompany: 'Palace Resort & Spa Collection',
    buyerLocation: 'Udaipur, Rajasthan',
    craftRequired: 'Mughal Tile Coaster Sets (Bulk 200 Sets)',
    quantityRequired: 200,
    targetBudget: 120000,
    deliveryDeadline: 'Within 40 Days',
    status: RfqStatus.matched,
    specifications: 'Custom turquoise & yellow floral motifs for 80 luxury suite tables. Food safe glaze certification required.',
    postedAt: DateTime.now().subtract(const Duration(days: 1)),
  ),
  SellerRfq(
    id: 'rfq-203',
    rfqNumber: 'RFQ-IN-2026-074',
    buyerName: 'Kaveri Arts & Exports',
    buyerCompany: 'Global Indian Heritage Inc.',
    buyerLocation: 'London, UK / Bengaluru',
    craftRequired: 'Royal Blue Pottery Dinner Plates (Batch of 100)',
    quantityRequired: 100,
    targetBudget: 150000,
    deliveryDeadline: 'Within 30 Days',
    status: RfqStatus.quoted,
    specifications: 'Export quality low-fire quartz dinner sets for diaspora exhibitions.',
    postedAt: DateTime.now().subtract(const Duration(days: 3)),
    quote: SellerQuoteSubmission(
      pricePerUnit: 1350,
      moq: 50,
      deliveryDays: 28,
      message: 'Greetings! Our master artisans will handcraft and low-fire these with 100% natural quartz and cobalt oxide mineral glazes. Includes export packaging and Craft Passport certificates.',
      hasVoiceNote: true,
      attachedPortfolioIds: ['sp-001', 'sp-004'],
      submittedAt: DateTime.now().subtract(const Duration(days: 2)),
    ),
  ),
];

// Seller RFQ Notifier
class SellerRfqNotifier extends StateNotifier<List<SellerRfq>> {
  SellerRfqNotifier() : super(initialSellerRfqs);

  void submitQuotation({
    required String rfqId,
    required double pricePerUnit,
    required int moq,
    required int deliveryDays,
    required String message,
    bool hasVoiceNote = false,
    List<String> portfolioIds = const [],
  }) {
    state = state.map((rfq) {
      if (rfq.id == rfqId) {
        return rfq.copyWith(
          status: RfqStatus.quoted,
          quote: SellerQuoteSubmission(
            pricePerUnit: pricePerUnit,
            moq: moq,
            deliveryDays: deliveryDays,
            message: message,
            hasVoiceNote: hasVoiceNote,
            attachedPortfolioIds: portfolioIds,
            submittedAt: DateTime.now(),
          ),
        );
      }
      return rfq;
    }).toList();
  }

  void rejectRfq(String rfqId) {
    state = state.map((rfq) {
      if (rfq.id == rfqId) {
        return rfq.copyWith(status: RfqStatus.rejected);
      }
      return rfq;
    }).toList();
  }
}

final sellerRfqsProvider = StateNotifierProvider<SellerRfqNotifier, List<SellerRfq>>((ref) {
  return SellerRfqNotifier();
});

// Storefront Config Notifier
class StorefrontConfigNotifier extends StateNotifier<ArtisanStorefrontConfig> {
  StorefrontConfigNotifier()
      : super(const ArtisanStorefrontConfig(
          storeName: 'Dr. Kripal Kumbh Heritage Studio',
          artisanName: 'Dr. Kripal Singh Shekhawat Guild',
          tagline: 'Preserving 17th Century Jaipur Blue Pottery & Mineral Glazes',
          bio: 'National Award-winning master artisan studio dedicated to keeping alive authentic clay-free quartz pottery. Every piece is hand-shaped, mineral-painted, and fired in traditional wood and gas kilns in Jaipur.',
          clusterRegion: 'Kot Jewar & Jaipur',
          state: 'Rajasthan',
          isGiCertified: true,
          isNationalAwardee: true,
          isStoreOpen: true,
          isLiveNow: false,
          collections: ['Royal Cobalt Glazes', 'Mughal Architectural Tiles', 'Palace Tea Sets', 'GI Heritage Keepsakes'],
          featuredProductIds: ['sp-001', 'sp-002', 'sp-004'],
        ));

  void updateConfig(ArtisanStorefrontConfig config) {
    state = config;
  }

  void toggleStoreOpen() {
    state = state.copyWith(isStoreOpen: !state.isStoreOpen);
  }

  void toggleLiveStatus() {
    state = state.copyWith(isLiveNow: !state.isLiveNow);
  }

  void addCollection(String name) {
    if (!state.collections.contains(name)) {
      state = state.copyWith(collections: [...state.collections, name]);
    }
  }

  void removeCollection(String name) {
    state = state.copyWith(collections: state.collections.where((c) => c != name).toList());
  }
}

final storefrontConfigProvider = StateNotifierProvider<StorefrontConfigNotifier, ArtisanStorefrontConfig>((ref) {
  return StorefrontConfigNotifier();
});

// Summary Analytics
final sellerAnalyticsProvider = Provider<Map<String, dynamic>>((ref) {
  final products = ref.watch(sellerProductsProvider);
  final orders = ref.watch(sellerOrdersProvider);
  final rfqs = ref.watch(sellerRfqsProvider);

  final totalRevenue = products.fold<double>(0, (sum, p) => sum + p.totalRevenue);
  final totalSalesCount = products.fold<int>(0, (sum, p) => sum + p.salesCount);
  final activeProductsCount = products.where((p) => p.status == ProductStatus.published).length;
  final draftProductsCount = products.where((p) => p.status == ProductStatus.draft).length;
  final pendingOrdersCount = orders.where((o) => o.status == OrderStatus.pending).length;
  final openRfqsCount = rfqs.where((r) => r.status == RfqStatus.incoming || r.status == RfqStatus.matched).length;
  final totalRfqPotential = rfqs.fold<double>(0, (sum, r) => sum + r.targetBudget);

  return {
    'totalRevenue': totalRevenue,
    'totalSalesCount': totalSalesCount,
    'activeProductsCount': activeProductsCount,
    'draftProductsCount': draftProductsCount,
    'pendingOrdersCount': pendingOrdersCount,
    'openRfqsCount': openRfqsCount,
    'totalRfqPotential': totalRfqPotential,
    'totalOrdersCount': orders.length,
  };
});
