import 'dart:async';
import 'dart:math';
import '../domain/live_session_model.dart';
import '../domain/live_streaming_service.dart';

class MockLiveStreamingService implements LiveStreamingService {
  final _statusController = StreamController<LiveStreamStatus>.broadcast();
  final _commentsController = StreamController<LiveComment>.broadcast();
  final _reactionsController = StreamController<LiveReaction>.broadcast();
  final _viewerCountController = StreamController<int>.broadcast();
  final _pinnedProductController = StreamController<LiveProductItem?>.broadcast();

  Timer? _viewerSimTimer;
  Timer? _commentSimTimer;
  Timer? _reactionSimTimer;
  int _currentViewers = 142;
  final Random _random = Random();

  @override
  Stream<LiveStreamStatus> get streamStatusStream => _statusController.stream;

  @override
  Stream<LiveComment> get commentsStream => _commentsController.stream;

  @override
  Stream<LiveReaction> get reactionsStream => _reactionsController.stream;

  @override
  Stream<int> get viewerCountStream => _viewerCountController.stream;

  @override
  Stream<LiveProductItem?> get pinnedProductStream => _pinnedProductController.stream;

  @override
  Future<void> connectToRoom({
    required String roomId,
    required String participantName,
    required bool isBroadcaster,
    String? token,
  }) async {
    _statusController.add(LiveStreamStatus.live);
    _viewerCountController.add(_currentViewers);

    // Initial system greeting
    _commentsController.add(
      LiveComment(
        id: 'sys-${DateTime.now().millisecondsSinceEpoch}',
        userName: 'KalaCart Live Hub',
        userAvatar: 'https://images.unsplash.com/photo-1544717305-2782549b5136',
        text: isBroadcaster
            ? 'You are now LIVE. Viewers can see your craft studio and ask questions in real-time.'
            : 'Welcome to the live craft workshop! You can chat with the artisan and purchase pinned crafts.',
        timestamp: DateTime.now(),
        isSystem: true,
      ),
    );

    _startSimulations();
  }

  void _startSimulations() {
    // Viewer fluctuation simulation
    _viewerSimTimer = Timer.periodic(const Duration(seconds: 4), (timer) {
      final delta = _random.nextInt(7) - 3;
      _currentViewers = max(12, _currentViewers + delta);
      if (!_viewerCountController.isClosed) {
        _viewerCountController.add(_currentViewers);
      }
    });

    // Incoming simulated comments from buyers/visitors
    final mockViewerComments = [
      ('Ananya Verma', 'https://images.unsplash.com/photo-1494790108377-be9c29b29330', 'Is this pure brass or bronze alloy?'),
      ('Vikram Singhal', 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d', 'The glaze texture on the vase is stunning! ❤️'),
      ('Rohit Mehta', 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e', 'Do you ship bulk wholesale orders to Delhi NCR?'),
      ('Pooja Patel', 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80', 'Can you please show the reverse embroidery work?'),
      ('Sanjay Rao', 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e', 'Just placed an order for 2 pieces! Excited for the craft passport.'),
      ('Deepika Sharma', 'https://images.unsplash.com/photo-1534528741775-53994a69daeb', 'How many days did this piece take to handcraft?'),
    ];

    _commentSimTimer = Timer.periodic(const Duration(seconds: 6), (timer) {
      if (!_commentsController.isClosed) {
        final commentData = mockViewerComments[_random.nextInt(mockViewerComments.length)];
        _commentsController.add(
          LiveComment(
            id: 'c-${DateTime.now().millisecondsSinceEpoch}',
            userName: commentData.$1,
            userAvatar: commentData.$2,
            text: commentData.$3,
            timestamp: DateTime.now(),
          ),
        );
      }
    });

    // Spontaneous hearts/reactions
    _reactionSimTimer = Timer.periodic(const Duration(seconds: 2), (timer) {
      if (!_reactionsController.isClosed) {
        const types = LiveReactionType.values;
        _reactionsController.add(
          LiveReaction(
            id: 'r-${DateTime.now().millisecondsSinceEpoch}',
            type: types[_random.nextInt(types.length)],
            xOffset: (_random.nextDouble() * 120) - 60,
            timestamp: DateTime.now(),
          ),
        );
      }
    });
  }

  @override
  Future<void> setPinnedProduct(LiveProductItem? product) async {
    if (!_pinnedProductController.isClosed) {
      _pinnedProductController.add(product);
    }
  }

  @override
  Future<void> sendComment(String text, {required String userName, required String userAvatar, bool isArtisan = false}) async {
    if (!_commentsController.isClosed) {
      _commentsController.add(
        LiveComment(
          id: 'user-${DateTime.now().millisecondsSinceEpoch}',
          userName: userName,
          userAvatar: userAvatar,
          text: text,
          timestamp: DateTime.now(),
          isArtisan: isArtisan,
        ),
      );
    }
  }

  @override
  Future<void> sendReaction(LiveReactionType type) async {
    if (!_reactionsController.isClosed) {
      _reactionsController.add(
        LiveReaction(
          id: 'usr-r-${DateTime.now().millisecondsSinceEpoch}',
          type: type,
          xOffset: (_random.nextDouble() * 100) - 50,
          timestamp: DateTime.now(),
        ),
      );
    }
  }

  @override
  Future<void> toggleCamera(bool enabled) async {}

  @override
  Future<void> toggleMicrophone(bool enabled) async {}

  @override
  Future<void> switchCamera() async {}

  @override
  Future<void> disconnect() async {
    _statusController.add(LiveStreamStatus.ended);
    _viewerSimTimer?.cancel();
    _commentSimTimer?.cancel();
    _reactionSimTimer?.cancel();
  }

  @override
  void dispose() {
    _viewerSimTimer?.cancel();
    _commentSimTimer?.cancel();
    _reactionSimTimer?.cancel();
    _statusController.close();
    _commentsController.close();
    _reactionsController.close();
    _viewerCountController.close();
    _pinnedProductController.close();
  }
}
