import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../shared/models/passport_models.dart';

final List<DigitalCraftPassportRecord> mockPassportDatabase = [
  const DigitalCraftPassportRecord(
    passportId: 'GI-IN-RAJ-2026-BP-0941',
    productTitle: 'Heritage Cobalt Floral Blue Pottery Vase',
    category: 'Pottery & Terracotta',
    artisanName: 'Dr. Kripal Singh Shekhawat Master Guild',
    guildName: 'Kripal Kumbh Artisan Cooperative',
    village: 'Kot Jewar',
    district: 'Jaipur',
    state: 'Rajasthan',
    geoCoordinates: '26.9124° N, 75.7873° E',
    materialComposition: 'Quartz Powder, Fuller Earth (Multani Mitti), Natural Cobalt Oxide Glaze',
    craftTechnique: 'Clay-Free Low Fire Ceramic Molding & Mineral Glazing',
    giRegistrationNumber: 'GI/APPLICATION/NO/04',
    handcraftDuration: '28 Handcrafting Hours',
    sustainabilityGrade: 'A+ (100% Eco-Friendly Non-Clay Ceramic)',
    verificationDate: '12 January 2026',
    status: PassportVerificationStatus.verified,
    qrCodeData: 'https://kalacart.in/passport/GI-IN-RAJ-2026-BP-0941',
    rawMaterialProvenance: 'Makrana quartz deposits & Barmer fuller earth.',
  ),
  const DigitalCraftPassportRecord(
    passportId: 'GI-IN-AP-2026-KLM-0182',
    productTitle: 'Natural Indigo Handloom Kalamkari Saree',
    category: 'Handloom & Textiles',
    artisanName: 'Pedana Heritage Kalamkari Collective',
    guildName: 'Krishna District Handloom Weavers Society',
    village: 'Pedana',
    district: 'Krishna',
    state: 'Andhra Pradesh',
    geoCoordinates: '16.2570° N, 81.1444° E',
    materialComposition: '100% Pure Organic Cotton & Plant-Derived Natural Indigo Dyes',
    craftTechnique: 'Teakwood Block Stamping & Flowing Canal Washing',
    giRegistrationNumber: 'GI/APPLICATION/NO/19',
    handcraftDuration: '42 Handcrafting Hours',
    sustainabilityGrade: 'A+ (Zero Chemical Effluent Process)',
    verificationDate: '04 February 2026',
    status: PassportVerificationStatus.verified,
    qrCodeData: 'https://kalacart.in/passport/GI-IN-AP-2026-KLM-0182',
    rawMaterialProvenance: 'Guntur organic cotton & fermented indigo leaves.',
  ),
  const DigitalCraftPassportRecord(
    passportId: 'GI-IN-CHG-2026-DHK-4421',
    productTitle: 'Dhokra Lost-Wax Bell Metal Nandi Figurine',
    category: 'Brass & Metal Craft',
    artisanName: 'Bastar Bell Metal Guild',
    guildName: 'Ghadwa Artisan Council of Kondagaon',
    village: 'Kondagaon',
    district: 'Bastar',
    state: 'Chhattisgarh',
    geoCoordinates: '19.5984° N, 81.6688° E',
    materialComposition: 'Recycled Bell Metal (Kansa) & Pure Forest Beeswax Core',
    craftTechnique: 'Cire Perdue (Lost-Wax Casting)',
    giRegistrationNumber: 'GI/APPLICATION/NO/83',
    handcraftDuration: '36 Handcrafting Hours',
    sustainabilityGrade: 'A (100% Recycled Bell Metal)',
    verificationDate: '18 February 2026',
    status: PassportVerificationStatus.verified,
    qrCodeData: 'https://kalacart.in/passport/GI-IN-CHG-2026-DHK-4421',
    rawMaterialProvenance: 'Wild beeswax from Bastar forests & alluvial riverbed clay.',
  ),
];

final passportRepositoryProvider = Provider<List<DigitalCraftPassportRecord>>((ref) {
  return mockPassportDatabase;
});

final singlePassportProvider = Provider.family<DigitalCraftPassportRecord?, String>((ref, passportId) {
  final db = ref.watch(passportRepositoryProvider);
  return db.firstWhere(
    (p) => p.passportId.toLowerCase() == passportId.toLowerCase(),
    orElse: () => db.first,
  );
});
