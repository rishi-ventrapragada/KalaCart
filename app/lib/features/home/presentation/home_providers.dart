import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../shared/models/craft_product.dart';

final mockProductsProvider = Provider<List<CraftProduct>>((ref) {
  return const [
    CraftProduct(
      id: 'prod-001',
      title: 'Handmade Blue Pottery Vase',
      artisanName: 'Kripal Kumbh',
      region: 'Jaipur, Rajasthan',
      price: 1850,
      rating: 4.9,
      category: 'Pottery & Terracotta',
      isGiTagged: true,
      isCustomizable: true,
    ),
    CraftProduct(
      id: 'prod-002',
      title: 'Kalamkari Hand-Painted Saree',
      artisanName: 'Pedana Craft Collective',
      region: 'Andhra Pradesh',
      price: 4200,
      rating: 4.8,
      category: 'Handloom & Textiles',
      isGiTagged: true,
      isCustomizable: false,
    ),
    CraftProduct(
      id: 'prod-003',
      title: 'Dhokra Brass Tribal Figurine',
      artisanName: 'Bastar Metal Works',
      region: 'Chhattisgarh',
      price: 2490,
      rating: 4.7,
      category: 'Brass & Metal Craft',
      isGiTagged: true,
      isCustomizable: true,
    ),
    CraftProduct(
      id: 'prod-004',
      title: 'Madhubani Tree of Life Painting',
      artisanName: 'Mithila Kala Kendra',
      region: 'Bihar',
      price: 3100,
      rating: 5.0,
      category: 'Paintings & Madhubani',
      isGiTagged: true,
      isCustomizable: true,
    ),
  ];
});

final selectedCategoryProvider = StateProvider<String>((ref) => 'All Crafts');
