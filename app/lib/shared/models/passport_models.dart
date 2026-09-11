enum PassportVerificationStatus {
  verified,
  pending,
  unregistered,
}

class DigitalCraftPassportRecord {
  final String passportId;
  final String productTitle;
  final String category;
  final String artisanName;
  final String guildName;
  final String village;
  final String district;
  final String state;
  final String geoCoordinates;
  final String materialComposition;
  final String craftTechnique;
  final String giRegistrationNumber;
  final String giCertificateStatus;
  final String certificateUrlPlaceholder;
  final String handcraftDuration;
  final String sustainabilityGrade;
  final String verificationDate;
  final PassportVerificationStatus status;
  final String qrCodeData;
  final String rawMaterialProvenance;

  const DigitalCraftPassportRecord({
    required this.passportId,
    required this.productTitle,
    required this.category,
    required this.artisanName,
    required this.guildName,
    required this.village,
    required this.district,
    required this.state,
    required this.geoCoordinates,
    required this.materialComposition,
    required this.craftTechnique,
    required this.giRegistrationNumber,
    this.giCertificateStatus = 'Registered Geographical Indication (Govt. of India)',
    this.certificateUrlPlaceholder = 'https://kalacart.in/passport/cert/GI-IN-2026-BP-0941.pdf',
    required this.handcraftDuration,
    this.sustainabilityGrade = 'A+ (100% Eco-Friendly Non-Clay Ceramic)',
    required this.verificationDate,
    this.status = PassportVerificationStatus.verified,
    required this.qrCodeData,
    required this.rawMaterialProvenance,
  });
}
