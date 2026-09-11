import 'dart:async';
import '../domain/live_session_model.dart';

abstract class LiveStreamingService {
  /// Stream of connection / streaming state
  Stream<LiveStreamStatus> get streamStatusStream;

  /// Stream of incoming real-time comments
  Stream<LiveComment> get commentsStream;

  /// Stream of incoming real-time viewer reactions
  Stream<LiveReaction> get reactionsStream;

  /// Stream of real-time viewer count updates
  Stream<int> get viewerCountStream;

  /// Stream of the active pinned product
  Stream<LiveProductItem?> get pinnedProductStream;

  /// Initialize and connect to a live room (compatible with LiveKit Room connection token)
  Future<void> connectToRoom({
    required String roomId,
    required String participantName,
    required bool isBroadcaster,
    String? token,
  });

  /// Disconnect from the room
  Future<void> disconnect();

  /// Broadcaster: Pin or unpin a showcase product in real-time
  Future<void> setPinnedProduct(LiveProductItem? product);

  /// Send a chat comment
  Future<void> sendComment(String text, {required String userName, required String userAvatar, bool isArtisan = false});

  /// Send a quick reaction (heart, fire, etc.)
  Future<void> sendReaction(LiveReactionType type);

  /// Toggle camera (Broadcaster)
  Future<void> toggleCamera(bool enabled);

  /// Toggle microphone (Broadcaster)
  Future<void> toggleMicrophone(bool enabled);

  /// Flip front/back camera (Broadcaster)
  Future<void> switchCamera();

  /// Dispose service resources
  void dispose();
}
