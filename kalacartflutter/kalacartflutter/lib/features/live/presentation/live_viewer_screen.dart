import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../shared/widgets/social_share_sheet.dart';
import '../data/live_repository.dart';
import '../domain/live_session_model.dart';
import 'widgets/instant_checkout_bottom_sheet.dart';
import 'widgets/live_chat_overlay.dart';
import 'widgets/live_products_sheet.dart';
import 'widgets/live_reactions_overlay.dart';
import 'widgets/pinned_product_card.dart';

class LiveViewerScreen extends ConsumerStatefulWidget {
  final String sessionId;

  const LiveViewerScreen({
    super.key,
    required this.sessionId,
  });

  @override
  ConsumerState<LiveViewerScreen> createState() => _LiveViewerScreenState();
}

class _LiveViewerScreenState extends ConsumerState<LiveViewerScreen> {
  final TextEditingController _commentInputController = TextEditingController();
  final ScrollController _chatScrollController = ScrollController();
  final List<LiveComment> _comments = [];
  final List<LiveReaction> _reactions = [];

  StreamSubscription<LiveComment>? _commentSub;
  StreamSubscription<LiveReaction>? _reactionSub;
  StreamSubscription<int>? _viewerCountSub;
  StreamSubscription<LiveProductItem?>? _pinnedProductSub;
  StreamSubscription<LiveStreamStatus>? _statusSub;

  int _liveViewerCount = 0;
  LiveProductItem? _pinnedProduct;
  bool _isFollowing = false;
  LiveStreamStatus _streamStatus = LiveStreamStatus.live;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _initLiveConnection();
    });
  }

  void _initLiveConnection() {
    final streamService = ref.read(liveStreamingServiceProvider);
    final session = ref.read(singleLiveSessionProvider(widget.sessionId));

    _liveViewerCount = session?.viewerCount ?? 120;
    _pinnedProduct = session?.pinnedProduct;
    _streamStatus = session?.status ?? LiveStreamStatus.live;

    streamService.connectToRoom(
      roomId: widget.sessionId,
      participantName: 'Buyer Guest',
      isBroadcaster: false,
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

    _statusSub = streamService.streamStatusStream.listen((status) {
      if (mounted) {
        setState(() => _streamStatus = status);
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

  @override
  void dispose() {
    _commentSub?.cancel();
    _reactionSub?.cancel();
    _viewerCountSub?.cancel();
    _pinnedProductSub?.cancel();
    _statusSub?.cancel();
    _commentInputController.dispose();
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
          // Simulated Video Background Stream (Placeholder for LiveKit VideoTrackRenderer)
          _buildSimulatedVideoBackground(session),

          // Top Header Overlay (Artisan info, Viewer count, Close button)
          Positioned(
            top: MediaQuery.of(context).padding.top + 8,
            left: 12,
            right: 12,
            child: _buildTopHeaderOverlay(session),
          ),

          // Middle-Right Action Strip (Reactions, Showcase Crafts, Share)
          Positioned(
            right: 12,
            bottom: 110,
            child: _buildRightActionStrip(session),
          ),

          // Floating Animated Reactions
          Positioned.fill(
            child: LiveReactionsOverlay(reactions: _reactions),
          ),

          // Bottom Chat Stream & Pinned Product Overlay
          Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Real-time Chat
                SizedBox(
                  height: 170,
                  child: LiveChatOverlay(
                    comments: _comments,
                    scrollController: _chatScrollController,
                  ),
                ),

                // Pinned Product Banner (if any)
                if (_pinnedProduct != null) ...[
                  AppSpacing.gapV8,
                  PinnedProductCard(
                    product: _pinnedProduct!,
                    isBroadcaster: false,
                    onTap: () {
                      context.push('/products/${_pinnedProduct!.id}');
                    },
                    onBuyNow: () {
                      _openInstantCheckout(session, _pinnedProduct!);
                    },
                  ),
                ],

                // Input Bar (Comment Box + Quick Hearts)
                _buildBottomInputBar(session),
              ],
            ),
          ),

          // Replay or Ended Banner (if stream status is ended or replaying)
          if (_streamStatus == LiveStreamStatus.ended || session.status == LiveStreamStatus.replaying)
            Positioned(
              top: MediaQuery.of(context).padding.top + 60,
              left: 16,
              right: 16,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                decoration: BoxDecoration(
                  color: Colors.black87,
                  borderRadius: AppRadius.borderMd,
                  border: Border.all(color: AppColors.secondary, width: 1),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.replay_circle_filled, color: AppColors.secondary, size: 18),
                    AppSpacing.gapH8,
                    Expanded(
                      child: Text(
                        session.status == LiveStreamStatus.replaying
                            ? 'Streaming recorded replay from ${session.artisanName}'
                            : 'This live craft broadcast has ended.',
                        style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold),
                      ),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildSimulatedVideoBackground(LiveSessionModel session) {
    return Container(
      color: const Color(0xFF141414),
      child: Stack(
        fit: StackFit.expand,
        children: [
          Image.network(
            session.coverImageUrl,
            fit: BoxFit.cover,
            errorBuilder: (_, __, ___) => const Center(
              child: Icon(Icons.live_tv, size: 72, color: Colors.white24),
            ),
          ),
          Container(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  Colors.black.withValues(alpha: 0.65),
                  Colors.transparent,
                  Colors.black.withValues(alpha: 0.85),
                ],
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                stops: const [0.0, 0.45, 0.9],
              ),
            ),
          ),
          // LiveKit stream simulator watermark
          Positioned(
            top: MediaQuery.of(context).padding.top + 65,
            left: 14,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.black.withValues(alpha: 0.5),
                borderRadius: AppRadius.borderSm,
              ),
              child: const Row(
                children: [
                  Icon(Icons.videocam_outlined, size: 12, color: Colors.white70),
                  SizedBox(width: 4),
                  Text('LiveKit 1080p HD Stream', style: TextStyle(color: Colors.white70, fontSize: 9)),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTopHeaderOverlay(LiveSessionModel session) {
    return Row(
      children: [
        // Artisan Profile Capsule
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: Colors.black.withValues(alpha: 0.6),
            borderRadius: AppRadius.borderPill,
          ),
          child: Row(
            children: [
              GestureDetector(
                onTap: () => context.push('/artisan/${session.artisanId}'),
                child: CircleAvatar(
                  radius: 16,
                  backgroundImage: NetworkImage(session.artisanAvatar),
                ),
              ),
              AppSpacing.gapH8,
              GestureDetector(
                onTap: () => context.push('/artisan/${session.artisanId}'),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Row(
                      children: [
                        Text(
                          session.artisanName,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(width: 4),
                        const Icon(Icons.verified, size: 12, color: AppColors.secondary),
                      ],
                    ),
                    Text(
                      session.region,
                      style: const TextStyle(
                        color: Colors.white70,
                        fontSize: 9,
                      ),
                    ),
                  ],
                ),
              ),
              AppSpacing.gapH8,
              // Follow Button
              ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: _isFollowing ? Colors.white24 : AppColors.primary,
                  foregroundColor: Colors.white,
                  elevation: 0,
                  shape: AppRadius.shapePill,
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  minimumSize: Size.zero,
                  tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                ),
                onPressed: () {
                  setState(() => _isFollowing = !_isFollowing);
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text(_isFollowing ? 'Following ${session.artisanName}' : 'Unfollowed'),
                      duration: const Duration(seconds: 1),
                    ),
                  );
                },
                child: Text(
                  _isFollowing ? 'Following' : 'Follow',
                  style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold),
                ),
              ),
            ],
          ),
        ),
        const Spacer(),

        // Live Badge & Viewers
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: const BoxDecoration(
            color: Color(0xFFD32F2F),
            borderRadius: AppRadius.borderPill,
          ),
          child: Row(
            children: [
              Container(
                width: 6,
                height: 6,
                decoration: const BoxDecoration(
                  color: Colors.white,
                  shape: BoxShape.circle,
                ),
              ),
              const SizedBox(width: 4),
              const Text('LIVE', style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold)),
            ],
          ),
        ),
        AppSpacing.gapH6,
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: Colors.black.withValues(alpha: 0.6),
            borderRadius: AppRadius.borderPill,
          ),
          child: Row(
            children: [
              const Icon(Icons.remove_red_eye_outlined, size: 12, color: Colors.white),
              const SizedBox(width: 4),
              Text('$_liveViewerCount', style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold)),
            ],
          ),
        ),
        AppSpacing.gapH8,

        // Close Screen Button
        IconButton(
          icon: const Icon(Icons.close, color: Colors.white, size: 22),
          style: IconButton.styleFrom(
            backgroundColor: Colors.black.withValues(alpha: 0.5),
            padding: const EdgeInsets.all(6),
          ),
          onPressed: () {
            if (context.canPop()) {
              context.pop();
            } else {
              context.go('/');
            }
          },
        ),
      ],
    );
  }

  Widget _buildRightActionStrip(LiveSessionModel session) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Showcase Products List Button
        _buildActionCircle(
          icon: Icons.shopping_bag_outlined,
          badge: '${session.products.length}',
          label: 'Crafts',
          onTap: () {
            LiveProductsSheet.show(
              context,
              products: session.products,
              currentPinnedId: _pinnedProduct?.id,
              isBroadcaster: false,
              onSelectProduct: (p) => context.push('/products/${p.id}'),
              onInstantCheckout: (p) => _openInstantCheckout(session, p),
            );
          },
        ),
        AppSpacing.gapV16,

        // Share Button
        _buildActionCircle(
          icon: Icons.share_outlined,
          label: 'Share',
          onTap: () {
            SocialShareSheet.show(
              context,
              title: 'Live Craft Workshop: ${session.title}',
              subtitle: 'Watching ${session.artisanName} live on KalaCart',
              deepLink: 'https://kalacart.in/live/${session.id}',
              entityType: 'live',
            );
          },
        ),
        AppSpacing.gapV16,

        // Like / Heart Button
        _buildActionCircle(
          icon: Icons.favorite,
          iconColor: const Color(0xFFFF2D55),
          label: '${session.likesCount}',
          onTap: () {
            ref.read(liveStreamingServiceProvider).sendReaction(LiveReactionType.heart);
            ref.read(liveSessionsProvider.notifier).incrementLikes(session.id);
          },
        ),
      ],
    );
  }

  Widget _buildActionCircle({
    required IconData icon,
    Color? iconColor,
    String? badge,
    required String label,
    required VoidCallback onTap,
  }) {
    return Column(
      children: [
        Stack(
          clipBehavior: Clip.none,
          children: [
            InkWell(
              onTap: onTap,
              borderRadius: BorderRadius.circular(24),
              child: Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: Colors.black.withValues(alpha: 0.5),
                  shape: BoxShape.circle,
                  border: Border.all(color: Colors.white24, width: 1),
                ),
                child: Icon(icon, color: iconColor ?? Colors.white, size: 22),
              ),
            ),
            if (badge != null)
              Positioned(
                top: -2,
                right: -2,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
                  decoration: const BoxDecoration(
                    color: AppColors.primary,
                    shape: BoxShape.circle,
                  ),
                  child: Text(
                    badge,
                    style: const TextStyle(color: Colors.white, fontSize: 9, fontWeight: FontWeight.bold),
                  ),
                ),
              ),
          ],
        ),
        AppSpacing.gapV4,
        Text(
          label,
          style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.w600),
        ),
      ],
    );
  }

  Widget _buildBottomInputBar(LiveSessionModel session) {
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
                controller: _commentInputController,
                style: const TextStyle(color: Colors.white, fontSize: 13),
                decoration: const InputDecoration(
                  hintText: 'Ask the artisan a question...',
                  hintStyle: TextStyle(color: Colors.white54, fontSize: 12),
                  border: InputBorder.none,
                  isDense: true,
                  contentPadding: EdgeInsets.symmetric(vertical: 10),
                ),
                onSubmitted: (text) => _submitComment(),
              ),
            ),
          ),
          AppSpacing.gapH8,
          IconButton(
            style: IconButton.styleFrom(
              backgroundColor: AppColors.primary,
              foregroundColor: Colors.white,
            ),
            icon: const Icon(Icons.send_rounded, size: 18),
            onPressed: _submitComment,
          ),
          AppSpacing.gapH6,
          // Quick Reaction Button (Namaste / Clap / Fire)
          InkWell(
            onTap: () {
              ref.read(liveStreamingServiceProvider).sendReaction(LiveReactionType.fire);
            },
            borderRadius: BorderRadius.circular(20),
            child: Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.black.withValues(alpha: 0.6),
                shape: BoxShape.circle,
                border: Border.all(color: Colors.white24),
              ),
              child: const Icon(Icons.local_fire_department, color: Color(0xFFFF9500), size: 20),
            ),
          ),
        ],
      ),
    );
  }

  void _submitComment() {
    final text = _commentInputController.text.trim();
    if (text.isEmpty) return;
    ref.read(liveStreamingServiceProvider).sendComment(
      text,
      userName: 'You',
      userAvatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde',
    );
    _commentInputController.clear();
  }

  void _openInstantCheckout(LiveSessionModel session, LiveProductItem product) {
    InstantCheckoutBottomSheet.show(
      context,
      product: product,
      artisanName: session.artisanName,
      onOrderCompleted: () {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            backgroundColor: AppColors.success,
            content: Row(
              children: [
                const Icon(Icons.check_circle, color: Colors.white),
                AppSpacing.gapH8,
                Expanded(child: Text('Live order placed for "${product.title}"! Digital passport generated.')),
              ],
            ),
            behavior: SnackBarBehavior.floating,
          ),
        );
      },
    );
  }
}
