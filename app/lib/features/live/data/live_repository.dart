import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../domain/live_session_model.dart';
import '../domain/live_streaming_service.dart';
import 'mock_live_streaming_service.dart';

/// Simulated live-streaming transport (no real video/LiveKit yet).
///
/// Deliberately NOT autoDispose: the screens obtain it with `ref.read` and hold
/// stream subscriptions on it, so an autoDispose provider would be torn down
/// (closing every stream) right after the read. Screens call `disconnect()`
/// when they leave, which stops the simulation timers.
final liveStreamingServiceProvider = Provider<LiveStreamingService>((ref) {
  final service = MockLiveStreamingService();
  ref.onDispose(() => service.dispose());
  return service;
});

final mockLiveSessionsDatabase = <LiveSessionModel>[
  const LiveSessionModel(
    id: 'live-01',
    artisanId: 'art-002',
    artisanName: 'Dr. Kripal Kumbh Studio',
    artisanAvatar: 'https://images.unsplash.com/photo-1544717305-2782549b5136',
    craftCluster: 'Jaipur Blue Pottery Guild',
    region: 'Jaipur, Rajasthan',
    title: 'Live Workshop: Throwing Makrana Quartz Pottery',
    description: 'Watch 4th-generation master potters shape cobalt blue quartz clay with Egyptian frit glaze live from Jaipur.',
    coverImageUrl: 'https://images.unsplash.com/photo-1578749556568-bc2c40e68b61',
    status: LiveStreamStatus.live,
    viewerCount: 248,
    likesCount: 1840,
    pinnedProductId: 'prod-001',
    products: [
      LiveProductItem(
        id: 'prod-001',
        title: 'GI Hand-Painted Blue Pottery 12" Floral Royal Urn Vase',
        price: 2850,
        wholesalePrice: 1950,
        imageUrl: 'https://images.unsplash.com/photo-1578749556568-bc2c40e68b61',
        craftType: 'Blue Pottery',
        isPinned: true,
      ),
      LiveProductItem(
        id: 'prod-004',
        title: 'Jaipur Blue Ceramic Coaster Set (Pack of 6)',
        price: 950,
        wholesalePrice: 650,
        imageUrl: 'https://images.unsplash.com/photo-1615529182904-14819c35db37',
        craftType: 'Blue Pottery',
      ),
    ],
  ),
  const LiveSessionModel(
    id: 'live-02',
    artisanId: 'art-001',
    artisanName: 'Mohd. Rafiq Ansari',
    artisanAvatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d',
    craftCluster: 'Varanasi Handloom Guild',
    region: 'Varanasi, Uttar Pradesh',
    title: 'Live Zari Gold Loom: Real-Time Kadwa Brocade Weaving',
    description: 'Detailed showcase of pure mulberry silk with real gold & silver tested zari yarn on Jacquard pit looms.',
    coverImageUrl: 'https://images.unsplash.com/photo-1610030469983-98e550d6193c',
    status: LiveStreamStatus.live,
    viewerCount: 395,
    likesCount: 3240,
    pinnedProductId: 'prod-002',
    products: [
      LiveProductItem(
        id: 'prod-002',
        title: 'Pure Katan Silk Banarasi Saree with Real Gold Zari',
        price: 18500,
        wholesalePrice: 14200,
        imageUrl: 'https://images.unsplash.com/photo-1610030469983-98e550d6193c',
        craftType: 'Banarasi Brocade',
        isPinned: true,
      ),
    ],
  ),
  const LiveSessionModel(
    id: 'live-03',
    artisanId: 'art-003',
    artisanName: 'Bastar Bell Metal Guild',
    artisanAvatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e',
    craftCluster: 'Kondagaon Dhokra Guild',
    region: 'Kondagaon, Chhattisgarh',
    title: 'Molten Bell Metal Casting: Lost-Wax Dhokra Demo',
    description: 'Pouring 1100°C molten brass into natural beeswax and terracotta molds.',
    coverImageUrl: 'https://images.unsplash.com/photo-1567653418876-5bb0e566e1c2',
    status: LiveStreamStatus.replaying,
    viewerCount: 1120,
    likesCount: 5400,
    replayUrl: 'mock://replays/live-03-dhokra.mp4',
    products: [
      LiveProductItem(
        id: 'prod-003',
        title: 'Lost-Wax Cast Dhokra Tribal Nandi Sculpture',
        price: 3200,
        wholesalePrice: 2200,
        imageUrl: 'https://images.unsplash.com/photo-1567653418876-5bb0e566e1c2',
        craftType: 'Dhokra Metal Craft',
      ),
    ],
  ),
  LiveSessionModel(
    id: 'live-04',
    artisanId: 'art-004',
    artisanName: 'Kutch Rogan Collective',
    artisanAvatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e',
    craftCluster: 'Nirona Craft Village',
    region: 'Kutch, Gujarat',
    title: 'Freehand Castor Oil Rogan Painting on Ahimsa Silk',
    description: 'Upcoming live workshop demonstrating the 300-year stylus craft using natural stone minerals.',
    coverImageUrl: 'https://images.unsplash.com/photo-1606744824163-985d376605aa',
    status: LiveStreamStatus.scheduled,
    scheduledAt: DateTime.now().add(const Duration(hours: 4, minutes: 30)),
    viewerCount: 84,
    likesCount: 420,
    products: const [
      LiveProductItem(
        id: 'prod-005',
        title: 'Tree of Life Rogan Painted Silk Tapestry',
        price: 6400,
        wholesalePrice: 4800,
        imageUrl: 'https://images.unsplash.com/photo-1606744824163-985d376605aa',
        craftType: 'Rogan Art',
      ),
    ],
  ),
];

class LiveSessionsNotifier extends StateNotifier<List<LiveSessionModel>> {
  LiveSessionsNotifier() : super(mockLiveSessionsDatabase);

  void addSession(LiveSessionModel session) {
    state = [session, ...state];
  }

  void updateSessionStatus(String sessionId, LiveStreamStatus newStatus) {
    state = state.map((s) {
      if (s.id == sessionId) {
        return s.copyWith(status: newStatus);
      }
      return s;
    }).toList();
  }

  void updatePinnedProduct(String sessionId, String? productId) {
    state = state.map((s) {
      if (s.id == sessionId) {
        final updatedProducts = s.products.map((p) {
          return p.copyWith(isPinned: p.id == productId);
        }).toList();
        return s.copyWith(
          pinnedProductId: productId,
          products: updatedProducts,
        );
      }
      return s;
    }).toList();
  }

  void incrementLikes(String sessionId) {
    state = state.map((s) {
      if (s.id == sessionId) {
        return s.copyWith(likesCount: s.likesCount + 1);
      }
      return s;
    }).toList();
  }
}

final liveSessionsProvider = StateNotifierProvider<LiveSessionsNotifier, List<LiveSessionModel>>((ref) {
  return LiveSessionsNotifier();
});

final singleLiveSessionProvider = Provider.family<LiveSessionModel?, String>((ref, sessionId) {
  final sessions = ref.watch(liveSessionsProvider);
  try {
    return sessions.firstWhere((s) => s.id == sessionId);
  } catch (_) {
    return null;
  }
});
