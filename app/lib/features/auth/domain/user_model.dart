enum UserAccountType {
  buyer,
  artisan;

  /// Value stored in `profiles.role`.
  String get dbValue => this == UserAccountType.artisan ? 'seller' : 'buyer';

  static UserAccountType fromDb(String? value) {
    switch (value) {
      case 'seller':
      case 'artisan':
        return UserAccountType.artisan;
      default:
        return UserAccountType.buyer;
    }
  }
}

/// The signed-in user as the app sees it: the Supabase auth user merged with
/// the `profiles` row and, for artisans, the `sellers` row.
class UserModel {
  /// Supabase auth user id (`auth.users.id`).
  final String id;

  /// `profiles.id` once the profile row exists.
  final String? profileId;

  /// `sellers.id` once the artisan has completed storefront onboarding.
  final String? sellerId;

  final String email;
  final String fullName;
  final String? phoneNumber;
  final UserAccountType accountType;
  final bool isEmailVerified;

  /// Buyer: profile has a name and a city. Artisan: a `sellers` row exists.
  final bool isOnboarded;

  final String? city;
  final String? state;
  final String? avatarUrl;

  // Seller storefront fields (artisan accounts only)
  final String? shopName;
  final String? artisanType;
  final String? bio;
  final String? sellerLocation;

  const UserModel({
    required this.id,
    this.profileId,
    this.sellerId,
    required this.email,
    required this.fullName,
    this.phoneNumber,
    required this.accountType,
    this.isEmailVerified = false,
    this.isOnboarded = false,
    this.city,
    this.state,
    this.avatarUrl,
    this.shopName,
    this.artisanType,
    this.bio,
    this.sellerLocation,
  });

  bool get isArtisan => accountType == UserAccountType.artisan;
  bool get isBuyer => accountType == UserAccountType.buyer;
  bool get hasSellerProfile => sellerId != null;

  String get initials {
    final parts = fullName.trim().split(RegExp(r'\s+')).where((p) => p.isNotEmpty).toList();
    if (parts.isEmpty) return email.isNotEmpty ? email[0].toUpperCase() : '?';
    if (parts.length == 1) return parts.first[0].toUpperCase();
    return (parts.first[0] + parts.last[0]).toUpperCase();
  }

  String get regionLabel {
    final bits = [city, state].where((s) => s != null && s.trim().isNotEmpty).cast<String>().toList();
    return bits.isEmpty ? 'India' : bits.join(', ');
  }

  UserModel copyWith({
    String? id,
    String? profileId,
    String? sellerId,
    String? email,
    String? fullName,
    String? phoneNumber,
    UserAccountType? accountType,
    bool? isEmailVerified,
    bool? isOnboarded,
    String? city,
    String? state,
    String? avatarUrl,
    String? shopName,
    String? artisanType,
    String? bio,
    String? sellerLocation,
  }) {
    return UserModel(
      id: id ?? this.id,
      profileId: profileId ?? this.profileId,
      sellerId: sellerId ?? this.sellerId,
      email: email ?? this.email,
      fullName: fullName ?? this.fullName,
      phoneNumber: phoneNumber ?? this.phoneNumber,
      accountType: accountType ?? this.accountType,
      isEmailVerified: isEmailVerified ?? this.isEmailVerified,
      isOnboarded: isOnboarded ?? this.isOnboarded,
      city: city ?? this.city,
      state: state ?? this.state,
      avatarUrl: avatarUrl ?? this.avatarUrl,
      shopName: shopName ?? this.shopName,
      artisanType: artisanType ?? this.artisanType,
      bio: bio ?? this.bio,
      sellerLocation: sellerLocation ?? this.sellerLocation,
    );
  }
}

/// Data collected on the buyer onboarding screen.
class BuyerProfileData {
  final String name;
  final List<String> preferredCraftCategories;
  final List<String> interests;
  final String location;
  final String preferredLanguage;
  final String? phone;

  const BuyerProfileData({
    required this.name,
    required this.preferredCraftCategories,
    required this.interests,
    required this.location,
    required this.preferredLanguage,
    this.phone,
  });
}

/// Data collected on the artisan onboarding screen.
class ArtisanProfileData {
  final String artisanName;
  final String storefrontName;
  final String craftCategory;
  final String villageLocation;
  final String bio;
  final List<String> rawMaterials;
  final List<String> languages;
  final String? profileImageUrl;
  final String? phone;

  const ArtisanProfileData({
    required this.artisanName,
    required this.storefrontName,
    required this.craftCategory,
    required this.villageLocation,
    required this.bio,
    required this.rawMaterials,
    required this.languages,
    this.profileImageUrl,
    this.phone,
  });
}

/// Splits a free-text "City, State" location into its two parts.
({String? city, String? state}) splitLocation(String raw) {
  final parts = raw.split(',').map((p) => p.trim()).where((p) => p.isNotEmpty).toList();
  if (parts.isEmpty) return (city: null, state: null);
  if (parts.length == 1) return (city: parts.first, state: null);
  return (city: parts.first, state: parts.last);
}
