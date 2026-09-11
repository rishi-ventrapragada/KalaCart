import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../data/live_repository.dart';
import '../domain/live_session_model.dart';
import 'widgets/live_chat_overlay.dart';
import 'widgets/live_products_sheet.dart';
import 'widgets/live_reactions_overlay.dart';
import 'widgets/pinned_product_card.dart';

class SellerLiveDashboardScreen extends ConsumerStatefulWidget {
  final String sessionId;

  const SellerLiveDashboardScreen({
    super.key,
    required this.sessionId,
  });

  @override
  ConsumerState<SellerLiveDashboardScreen> createState() => _SellerLiveDashboardScreenState();
}

class _SellerLiveDashboardScreenState extends ConsumerState<SellerLiveDashboardScreen> {
  final TextEditingController _artisanMsgController = TextEditingController();
  final ScrollController _chatScrollController = ScrollController();
  final List<LiveComment> _comments = [];
  final List<LiveReaction> _reactions = [];

  StreamSubscription<LiveComment>? _commentSub;
  StreamSubscription<LiveReaction>? _reactionSub;
  StreamSubscription<int>? _viewerCountSub;
  StreamSubscription<LiveProductItem?>? _pinnedProductSub;

  int _liveViewerCount = 0;
  LiveProductItem? _pinnedProduct;
  bool _isMicMuted = false;
  bool _isCameraOff = false;
  int _streamDurationSecs = 0;
  Timer? _durationTimer;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _initBroadcaster();
    });
  }

  void _initBroadcaster() {
    final streamService = ref.read(liveStreamingServiceProvider);
    final session = ref.read(singleLiveSessionProvider(widget.sessionId));

    _liveViewerCount = session?.viewerCount ?? 14;
    _pinnedProduct = session?.pinnedProduct;

    streamService.connectToRoom(
      roomId: widget.sessionId,
      participantName: session?.artisanName ?? 'Master Artisan',
      isBroadcaster: true,
    );

    _commentSub = streamService.commentsStream.listen((comment) {
      if (mounted) {
        setState(() {
          _comments.add(comment);
          if (_comments.length > 50) _comments.removeAt(0);
        });
        _scrollToBottom();
      }
    });

    _reactionSub = streamService.reactionsStream.listen((reaction) {
      if (mounted) {
        setState(() {
          _reactions.add(reaction);
          if (_reactions.length > 30) _reactions.removeAt(0);
        });
      }
    });

    _viewerCountSub = streamService.viewerCountStream.listen((count) {
      if (mounted) {
        setState(() => _liveViewerCount = count);
      }
    });

    _pinnedProductSub = streamService.pinnedProductStream.listen((product) {
      if (mounted) {
        setState(() => _pinnedProduct = product);
      }
    });

    _durationTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (mounted) {
        setState(() => _streamDurationSecs++);
      }
    });
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_chatScrollController.hasClients) {
        _chatScrollController.animateTo(
          _chatScrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeOut,
        );
      }
    });
  }

  String _formatDuration(int seconds) {
    final m = seconds ~/ 60;
    final s = seconds % 60;
    return '${m.toString().padLeft(2, '0')}:${s.toString().padLeft(2, '0')}';
  }

  @override
  void dispose() {
    _durationTimer?.cancel();
    _commentSub?.cancel();
    _reactionSub?.cancel();
    _viewerCountSub?.cancel();
    _pinnedProductSub?.cancel();
    _artisanMsgController.dispose();
    _chatScrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final session = ref.watch(singleLiveSessionProvider(widget.sessionId)) ?? mockLiveSessionsDatabase.first;

    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        fit: StackFit.expand,
        children: [
          // Camera Studio Stream Preview
          _buildCameraPreview(session),

          // Broadcaster Top Stats Bar
          Positioned(
            top: MediaQuery.of(context).padding.top + 8,
            left: 12,
            right: 12,
            child: _buildBroadcasterTopBar(session),
          ),

          // Floating Reactions
          Positioned.fill(
            child: LiveReactionsOverlay(reactions: _reactions),
          ),

          // Broadcaster Side Controls (Flip Cam, Mute, Video toggle, Manage Products)
          Positioned(
            right: 12,
            bottom: 120,
            child: _buildBroadcasterSideTools(session),
          ),

          // Bottom Chat & Pinned Product Manager
          Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Live Chat
                SizedBox(
                  height: 160,
                  child: LiveChatOverlay(
                    comments: _comments,
                    scrollController: _chatScrollController,
                  ),
                ),

                // Active Pinned Product Banner
                if (_pinnedProduct != null) ...[
                  AppSpacing.gapV8,
                  PinnedProductCard(
                    product: _pinnedProduct!,
                    isBroadcaster: true,
                    onTap: () {
                      _showProductManagementSheet(session);
                    },
                    onBuyNow: () {},
                    onUnpin: () {
                      ref.read(liveStreamingServiceProvider).setPinnedProduct(null);
                      ref.read(liveSessionsProvider.notifier).updatePinnedProduct(session.id, null);
                    },
                  ),
                ],

                // Artisan Message Input
                _buildArtisanInputBar(session),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCameraPreview(LiveSessionModel session) {
    return Container(
      color: Colors.black,
      child: Stack(
        fit: StackFit.expand,
        children: [
          if (!_isCameraOff)
            Image.network(
              session.coverImageUrl,
              fit: BoxFit.cover,
              errorBuilder: (_, __, ___) => const Center(
                child: Icon(Icons.camera_alt, color: Colors.white24, size: 64),
              ),
            )
          else
            const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.videocam_off, color: Colors.white54, size: 64),
                  AppSpacing.gapV12,
                  Text('Camera is Paused', style: TextStyle(color: Colors.white70, fontSize: 16)),
                ],
              ),
            ),
          Container(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  Colors.black.withValues(alpha: 0.6),
                  Colors.transparent,
                  Colors.black.withValues(alpha: 0.85),
                ],
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                stops: const [0.0, 0.4, 0.85],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBroadcasterTopBar(LiveSessionModel session) {
    return Row(
      children: [
        // Live Badge + Timer
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
          decoration: const BoxDecoration(
            color: Color(0xFFD32F2F),
            borderRadius: AppRadius.borderPill,
          ),
          child: Row(
            children: [
              Container(
                width: 7,
                height: 7,
                decoration: const BoxDecoration(
                  color: Colors.white,
                  shape: BoxShape.circle,
                ),
              ),
              AppSpacing.gapH6,
              const Text('LIVE', style: TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold)),
              AppSpacing.gapH6,
              Text(
                _formatDuration(_streamDurationSecs),
                style: const TextStyle(color: Colors.white, fontSize: 11, fontFamily: 'monospace'),
              ),
            ],
          ),
        ),
        AppSpacing.gapH8,

        // Viewer Counter
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
          decoration: BoxDecoration(
            color: Colors.black.withValues(alpha: 0.6),
            borderRadius: AppRadius.borderPill,
          ),
          child: Row(
            children: [
              const Icon(Icons.remove_red_eye, size: 14, color: Colors.white70),
              AppSpacing.gapH6,
              Text('$_liveViewerCount', style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold)),
            ],
          ),
        ),
        const Spacer(),

        // End Live Stream CTA
        ElevatedButton.icon(
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFFD32F2F),
            foregroundColor: Colors.white,
            elevation: 0,
            shape: AppRadius.shapePill,
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            minimumSize: Size.zero,
            tapTargetSize: MaterialTapTargetSize.shrinkWrap,
          ),
          icon: const Icon(Icons.stop_circle_outlined, size: 16),
          label: const Text('End Live', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
          onPressed: () => _confirmEndLive(session),
        ),
      ],
    );
  }

  Widget _buildBroadcasterSideTools(LiveSessionModel session) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Pin Products Tool
        _buildCircleButton(
          icon: Icons.inventory_2_outlined,
          label: 'Pin Craft',
          onTap: () => _showProductManagementSheet(session),
        ),
        AppSpacing.gapV12,

        // Flip Camera
        _buildCircleButton(
          icon: Icons.flip_camera_ios_outlined,
          label: 'Flip',
          onTap: () {
            ref.read(liveStreamingServiceProvider).switchCamera();
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Switched between front/studio camera'), duration: Duration(milliseconds: 700)),
            );
          },
        ),
        AppSpacing.gapV12,

        // Mute Microphone
        _buildCircleButton(
          icon: _isMicMuted ? Icons.mic_off : Icons.mic,
          iconColor: _isMicMuted ? Colors.redAccent : Colors.white,
          label: _isMicMuted ? 'Unmute' : 'Mute',
          onTap: () {
            setState(() => _isMicMuted = !_isMicMuted);
            ref.read(liveStreamingServiceProvider).toggleMicrophone(!_isMicMuted);
          },
        ),
        AppSpacing.gapV12,

        // Pause Camera
        _buildCircleButton(
          icon: _isCameraOff ? Icons.videocam_off : Icons.videocam,
          iconColor: _isCameraOff ? Colors.redAccent : Colors.white,
          label: _isCameraOff ? 'Resume' : 'Camera',
          onTap: () {
            setState(() => _isCameraOff = !_isCameraOff);
            ref.read(liveStreamingServiceProvider).toggleCamera(!_isCameraOff);
          },
        ),
      ],
    );
  }

  Widget _buildCircleButton({
    required IconData icon,
    Color? iconColor,
    required String label,
    required VoidCallback onTap,
  }) {
    return Column(
      children: [
        InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(24),
          child: Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: Colors.black.withValues(alpha: 0.6),
              shape: BoxShape.circle,
              border: Border.all(color: Colors.white24),
            ),
            child: Icon(icon, color: iconColor ?? Colors.white, size: 20),
          ),
        ),
        AppSpacing.gapV4,
        Text(label, style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.w600)),
      ],
    );
  }

  Widget _buildArtisanInputBar(LiveSessionModel session) {
    return Container(
      padding: EdgeInsets.fromLTRB(12, 8, 12, MediaQuery.of(context).padding.bottom + 8),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.transparent, Colors.black.withValues(alpha: 0.9)],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
      ),
      child: Row(
        children: [
          Expanded(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14),
              decoration: BoxDecoration(
                color: Colors.black.withValues(alpha: 0.6),
                borderRadius: AppRadius.borderPill,
                border: Border.all(color: Colors.white24),
              ),
              child: TextField(
                controller: _artisanMsgController,
                style: const TextStyle(color: Colors.white, fontSize: 13),
                decoration: const InputDecoration(
                  hintText: 'Answer buyers as Artisan...',
                  hintStyle: TextStyle(color: Colors.white54, fontSize: 12),
                  border: InputBorder.none,
                  isDense: true,
                  contentPadding: EdgeInsets.symmetric(vertical: 10),
                ),
                onSubmitted: (text) => _submitArtisanMessage(session),
              ),
            ),
          ),
          AppSpacing.gapH8,
          IconButton(
            style: IconButton.styleFrom(
              backgroundColor: AppColors.secondary,
              foregroundColor: Colors.black,
            ),
            icon: const Icon(Icons.send_rounded, size: 18),
            onPressed: () => _submitArtisanMessage(session),
          ),
        ],
      ),
    );
  }

  void _submitArtisanMessage(LiveSessionModel session) {
    final text = _artisanMsgController.text.trim();
    if (text.isEmpty) return;
    ref.read(liveStreamingServiceProvider).sendComment(
      text,
      userName: session.artisanName,
      userAvatar: session.artisanAvatar,
      isArtisan: true,
    );
    _artisanMsgController.clear();
  }

  void _showProductManagementSheet(LiveSessionModel session) {
    LiveProductsSheet.show(
      context,
      products: session.products,
      currentPinnedId: _pinnedProduct?.id,
      isBroadcaster: true,
      onSelectProduct: (p) {},
      onPinProduct: (p) {
        ref.read(liveStreamingServiceProvider).setPinnedProduct(p);
        ref.read(liveSessionsProvider.notifier).updatePinnedProduct(session.id, p.id);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Pinned "${p.title}" to all viewers!'),
            behavior: SnackBarBehavior.floating,
          ),
        );
      },
    );
  }

  void _confirmEndLive(LiveSessionModel session) {
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('End Live Broadcast?'),
          content: const Text('Ending this session will save the workshop recording for buyers as a replay.'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Keep Live'),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFFD32F2F), foregroundColor: Colors.white),
              onPressed: () {
                Navigator.pop(context);
                ref.read(liveStreamingServiceProvider).disconnect();
                ref.read(liveSessionsProvider.notifier).updateSessionStatus(session.id, LiveStreamStatus.replaying);
                _showSummaryDialog(session);
              },
              child: const Text('End Stream'),
            ),
          ],
        );
      },
    );
  }

  void _showSummaryDialog(LiveSessionModel session) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) {
        return AlertDialog(
          title: const Row(
            children: [
              Icon(Icons.check_circle, color: AppColors.success),
              AppSpacing.gapH8,
              Text('Broadcast Finished!'),
            ],
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Live Summary for ${session.title}:', style: const TextStyle(fontWeight: FontWeight.bold)),
              AppSpacing.gapV12,
              _summaryRow('Stream Duration', _formatDuration(_streamDurationSecs)),
              _summaryRow('Peak Viewers', '$_liveViewerCount'),
              _summaryRow('Buyer Questions Answered', '${_comments.length}'),
              _summaryRow('Replay Availability', 'Saved to Storefront Replays'),
            ],
          ),
          actions: [
            ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: AppColors.primary, foregroundColor: Colors.white),
              onPressed: () {
                Navigator.pop(context);
                context.pop();
              },
              child: const Text('Back to Dashboard'),
            ),
          ],
        );
      },
    );
  }

  Widget _summaryRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey)),
          Text(value, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }
}
