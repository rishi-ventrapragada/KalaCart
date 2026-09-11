enum LiveStreamStatus {
  scheduled,
  live,
  ended,
  replaying,
}

class LiveProductItem {
  final String id;
  final String title;
  final double price;
  final double? wholesalePrice;
  final String imageUrl;
  final String craftType;
  final bool isPinned;

  const LiveProductItem({
    required this.id,
    required this.title,
    required this.price,
    this.wholesalePrice,
    required this.imageUrl,
    required this.craftType,
    this.isPinned = false,
  });

  LiveProductItem copyWith({
    String? id,
    String? title,
    double? price,
    double? wholesalePrice,
    String? imageUrl,
    String? craftType,
    bool? isPinned,
  }) {
    return LiveProductItem(
      id: id ?? this.id,
      title: title ?? this.title,
      price: price ?? this.price,
      wholesalePrice: wholesalePrice ?? this.wholesalePrice,
      imageUrl: imageUrl ?? this.imageUrl,
      craftType: craftType ?? this.craftType,
      isPinned: isPinned ?? this.isPinned,
    );
  }
}

class LiveComment {
  final String id;
  final String userName;
  final String userAvatar;
  final String text;
  final DateTime timestamp;
  final bool isArtisan;
  final bool isSystem;

  const LiveComment({
    required this.id,
    required this.userName,
    required this.userAvatar,
    required this.text,
    required this.timestamp,
    this.isArtisan = false,
    this.isSystem = false,
  });
}

enum LiveReactionType {
  heart,
  fire,
  clap,
  namaste,
  star,
}

class LiveReaction {
  final String id;
  final LiveReactionType type;
  final double xOffset; // For floating animations
  final DateTime timestamp;

  const LiveReaction({
    required this.id,
    required this.type,
    required this.xOffset,
    required this.timestamp,
  });
}

class LiveSessionModel {
  final String id;
  final String artisanId;
  final String artisanName;
  final String artisanAvatar;
  final String craftCluster;
  final String region;
  final String title;
  final String description;
  final String coverImageUrl;
  final DateTime? scheduledAt;
  final LiveStreamStatus status;
  final int viewerCount;
  final int likesCount;
  final List<LiveProductItem> products;
  final String? pinnedProductId;
  final String videoStreamUrl;
  final String? replayUrl;
  final int durationSeconds;

  const LiveSessionModel({
    required this.id,
    required this.artisanId,
    required this.artisanName,
    required this.artisanAvatar,
    required this.craftCluster,
    required this.region,
    required this.title,
    required this.description,
    required this.coverImageUrl,
    this.scheduledAt,
    this.status = LiveStreamStatus.live,
    this.viewerCount = 1,
    this.likesCount = 0,
    this.products = const [],
    this.pinnedProductId,
    this.videoStreamUrl = 'mock://livekit/room-kalacart',
    this.replayUrl,
    this.durationSeconds = 0,
  });

  LiveProductItem? get pinnedProduct {
    if (pinnedProductId == null) return null;
    try {
      return products.firstWhere((p) => p.id == pinnedProductId);
    } catch (_) {
      return products.isNotEmpty ? products.first : null;
    }
  }

  LiveSessionModel copyWith({
    String? id,
    String? artisanId,
    String? artisanName,
    String? artisanAvatar,
    String? craftCluster,
    String? region,
    String? title,
    String? description,
    String? coverImageUrl,
    DateTime? scheduledAt,
    LiveStreamStatus? status,
    int? viewerCount,
    int? likesCount,
    List<LiveProductItem>? products,
    String? pinnedProductId,
    String? videoStreamUrl,
    String? replayUrl,
    int? durationSeconds,
  }) {
    return LiveSessionModel(
      id: id ?? this.id,
      artisanId: artisanId ?? this.artisanId,
      artisanName: artisanName ?? this.artisanName,
      artisanAvatar: artisanAvatar ?? this.artisanAvatar,
      craftCluster: craftCluster ?? this.craftCluster,
      region: region ?? this.region,
      title: title ?? this.title,
      description: description ?? this.description,
      coverImageUrl: coverImageUrl ?? this.coverImageUrl,
      scheduledAt: scheduledAt ?? this.scheduledAt,
      status: status ?? this.status,
      viewerCount: viewerCount ?? this.viewerCount,
      likesCount: likesCount ?? this.likesCount,
      products: products ?? this.products,
      pinnedProductId: pinnedProductId ?? this.pinnedProductId,
      videoStreamUrl: videoStreamUrl ?? this.videoStreamUrl,
      replayUrl: replayUrl ?? this.replayUrl,
      durationSeconds: durationSeconds ?? this.durationSeconds,
    );
  }
}
