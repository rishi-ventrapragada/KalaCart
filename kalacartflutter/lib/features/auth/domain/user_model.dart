enum UserAccountType {
  buyer,
  artisan,
}

class UserModel {
  final String id;
  final String email;
  final String fullName;
  final String? phoneNumber;
  final UserAccountType accountType;
  final bool isEmailVerified;
  final bool isOnboarded;
  final BuyerProfileData? buyerProfile;
  final ArtisanProfileData? artisanProfile;

  const UserModel({
    required this.id,
    required this.email,
    required this.fullName,
    this.phoneNumber,
    required this.accountType,
    this.isEmailVerified = false,
    this.isOnboarded = false,
    this.buyerProfile,
    this.artisanProfile,
  });

  UserModel copyWith({
    String? id,
    String? email,
    String? fullName,
    String? phoneNumber,
    UserAccountType? accountType,
    bool? isEmailVerified,
    bool? isOnboarded,
    BuyerProfileData? buyerProfile,
    ArtisanProfileData? artisanProfile,
  }) {
    return UserModel(
      id: id ?? this.id,
      email: email ?? this.email,
      fullName: fullName ?? this.fullName,
      phoneNumber: phoneNumber ?? this.phoneNumber,
      accountType: accountType ?? this.accountType,
      isEmailVerified: isEmailVerified ?? this.isEmailVerified,
      isOnboarded: isOnboarded ?? this.isOnboarded,
      buyerProfile: buyerProfile ?? this.buyerProfile,
      artisanProfile: artisanProfile ?? this.artisanProfile,
    );
  }
}

class BuyerProfileData {
  final String name;
  final List<String> preferredCraftCategories;
  final List<String> interests;
  final String location;
  final String preferredLanguage;

  const BuyerProfileData({
    required this.name,
    required this.preferredCraftCategories,
    required this.interests,
    required this.location,
    required this.preferredLanguage,
  });
}

class ArtisanProfileData {
  final String artisanName;
  final String storefrontName;
  final String craftCategory;
  final String villageLocation;
  final String bio;
  final List<String> rawMaterials;
  final List<String> languages;
  final String? profileImageUrl;

  const ArtisanProfileData({
    required this.artisanName,
    required this.storefrontName,
    required this.craftCategory,
    required this.villageLocation,
    required this.bio,
    required this.rawMaterials,
    required this.languages,
    this.profileImageUrl,
  });
}
