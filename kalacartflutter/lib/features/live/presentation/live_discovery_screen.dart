import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../shared/services/user_role_service.dart';
import '../data/live_repository.dart';
import '../domain/live_session_model.dart';

class LiveDiscoveryScreen extends ConsumerStatefulWidget {
  const LiveDiscoveryScreen({super.key});

  @override
  ConsumerState<LiveDiscoveryScreen> createState() => _LiveDiscoveryScreenState();
}

class _LiveDiscoveryScreenState extends ConsumerState<LiveDiscoveryScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final userRole = ref.watch(userRoleProvider);
    final sessions = ref.watch(liveSessionsProvider);

    final liveNowSessions = sessions.where((s) => s.status == LiveStreamStatus.live).toList();
    final upcomingSessions = sessions.where((s) => s.status == LiveStreamStatus.scheduled).toList();
    final replaySessions = sessions.where((s) => s.status == LiveStreamStatus.replaying || s.status == LiveStreamStatus.ended).toList();

    return Scaffold(
      appBar: AppBar(
        title: const Row(
          children: [
            Icon(Icons.sensors, color: Color(0xFFD32F2F), size: 22),
            AppSpacing.gapH8,
            Text('Live Craft Workshops'),
          ],
        ),
        bottom: TabBar(
          controller: _tabController,
          labelColor: AppColors.primary,
          indicatorColor: AppColors.primary,
          tabs: [
            Tab(text: 'Live Now (${liveNowSessions.length})'),
            Tab(text: 'Upcoming (${upcomingSessions.length})'),
            Tab(text: 'Replays (${replaySessions.length})'),
          ],
        ),
        actions: [
          if (userRole.isArtisanSeller)
            IconButton(
              icon: const Icon(Icons.add_to_queue_rounded),
              tooltip: 'Schedule Live',
              onPressed: () => context.push('/seller/live/schedule'),
            ),
        ],
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildLiveNowList(liveNowSessions),
          _buildUpcomingList(upcomingSessions),
          _buildReplaysList(replaySessions),
        ],
      ),
      floatingActionButton: userRole.isArtisanSeller
          ? FloatingActionButton.extended(
              backgroundColor: const Color(0xFFD32F2F),
              foregroundColor: Colors.white,
              icon: const Icon(Icons.videocam),
              label: const Text('Host Live Workshop'),
              onPressed: () => context.push('/seller/live/schedule'),
            )
          : null,
    );
  }

  Widget _buildLiveNowList(List<LiveSessionModel> sessions) {
    if (sessions.isEmpty) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.live_tv_outlined, size: 54, color: Colors.grey),
            AppSpacing.gapV12,
            Text('No artisans live right now', style: TextStyle(fontWeight: FontWeight.bold)),
            AppSpacing.gapV4,
            Text('Check upcoming schedules or explore recorded replays.', style: TextStyle(color: Colors.grey)),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: AppSpacing.paddingAllBase,
      itemCount: sessions.length,
      itemBuilder: (context, index) {
        final session = sessions[index];
        return _LiveSessionCard(session: session, isLiveNow: true);
      },
    );
  }

  Widget _buildUpcomingList(List<LiveSessionModel> sessions) {
    if (sessions.isEmpty) {
      return const Center(
        child: Text('No upcoming live streams scheduled yet.'),
      );
    }

    return ListView.builder(
      padding: AppSpacing.paddingAllBase,
      itemCount: sessions.length,
      itemBuilder: (context, index) {
        final session = sessions[index];
        return _LiveSessionCard(session: session, isUpcoming: true);
      },
    );
  }

  Widget _buildReplaysList(List<LiveSessionModel> sessions) {
    if (sessions.isEmpty) {
      return const Center(
        child: Text('No recorded workshops available yet.'),
      );
    }

    return ListView.builder(
      padding: AppSpacing.paddingAllBase,
      itemCount: sessions.length,
      itemBuilder: (context, index) {
        final session = sessions[index];
        return _LiveSessionCard(session: session, isReplay: true);
      },
    );
  }
}

class _LiveSessionCard extends StatelessWidget {
  final LiveSessionModel session;
  final bool isLiveNow;
  final bool isUpcoming;
  final bool isReplay;

  const _LiveSessionCard({
    required this.session,
    this.isLiveNow = false,
    this.isUpcoming = false,
    this.isReplay = false,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      elevation: 2,
      margin: const EdgeInsets.only(bottom: 16),
      shape: const RoundedRectangleBorder(borderRadius: AppRadius.borderLg),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: () {
          if (isLiveNow || isReplay) {
            context.push('/live/${session.id}');
          } else {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text('Reminder set for "${session.title}"! We will notify you when it starts.'),
                behavior: SnackBarBehavior.floating,
              ),
            );
          }
        },
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Thumbnail with badge & overlay
            Stack(
              children: [
                AspectRatio(
                  aspectRatio: 16 / 9,
                  child: Image.network(
                    session.coverImageUrl,
                    fit: BoxFit.cover,
                    errorBuilder: (_, __, ___) => Container(
                      color: Colors.grey.shade900,
                      child: const Center(child: Icon(Icons.image, color: Colors.white54)),
                    ),
                  ),
                ),
                Container(
                  height: 180,
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [Colors.black.withValues(alpha: 0.6), Colors.transparent, Colors.black.withValues(alpha: 0.7)],
                      begin: Alignment.topCenter,
                      end: Alignment.bottomCenter,
                    ),
                  ),
                ),
                // Status Badge
                Positioned(
                  top: 12,
                  left: 12,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: isLiveNow
                          ? const Color(0xFFD32F2F)
                          : (isUpcoming ? AppColors.primary : Colors.black87),
                      borderRadius: AppRadius.borderSm,
                    ),
                    child: Row(
                      children: [
                        Icon(
                          isLiveNow ? Icons.sensors : (isUpcoming ? Icons.alarm : Icons.replay),
                          color: Colors.white,
                          size: 12,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          isLiveNow ? 'LIVE' : (isUpcoming ? 'UPCOMING' : 'RECORDED REPLAY'),
                          style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                  ),
                ),
                // Viewers / Likes
                Positioned(
                  top: 12,
                  right: 12,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: Colors.black.withValues(alpha: 0.6),
                      borderRadius: AppRadius.borderPill,
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.remove_red_eye_outlined, color: Colors.white, size: 12),
                        const SizedBox(width: 4),
                        Text('${session.viewerCount}', style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold)),
                      ],
                    ),
                  ),
                ),
                // Attached products count badge
                if (session.products.isNotEmpty)
                  Positioned(
                    bottom: 12,
                    right: 12,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.black.withValues(alpha: 0.75),
                        borderRadius: AppRadius.borderMd,
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.shopping_bag_outlined, color: Colors.white, size: 12),
                          const SizedBox(width: 4),
                          Text('${session.products.length} Crafts', style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold)),
                        ],
                      ),
                    ),
                  ),
              ],
            ),

            // Card Body
            Padding(
              padding: AppSpacing.paddingAllBase,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      CircleAvatar(
                        radius: 14,
                        backgroundImage: NetworkImage(session.artisanAvatar),
                      ),
                      AppSpacing.gapH8,
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(session.artisanName, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                            Text('${session.craftCluster} · ${session.region}', style: TextStyle(fontSize: 10, color: Colors.grey.shade600)),
                          ],
                        ),
                      ),
                      if (isUpcoming)
                        OutlinedButton.icon(
                          style: OutlinedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                            minimumSize: Size.zero,
                            tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                          ),
                          icon: const Icon(Icons.notifications_active_outlined, size: 12),
                          label: const Text('Remind Me', style: TextStyle(fontSize: 10)),
                          onPressed: () {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(content: Text('Reminder set!')),
                            );
                          },
                        )
                      else
                        ElevatedButton.icon(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: isLiveNow ? const Color(0xFFD32F2F) : AppColors.primary,
                            foregroundColor: Colors.white,
                            shape: AppRadius.shapePill,
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                            minimumSize: Size.zero,
                            tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                          ),
                          icon: Icon(isLiveNow ? Icons.play_arrow : Icons.replay, size: 14),
                          label: Text(isLiveNow ? 'Join Live' : 'Watch Replay', style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                          onPressed: () => context.push('/live/${session.id}'),
                        ),
                    ],
                  ),
                  AppSpacing.gapV8,
                  Text(
                    session.title,
                    style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold),
                  ),
                  AppSpacing.gapV4,
                  Text(
                    session.description,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(fontSize: 12, color: Colors.grey.shade700, height: 1.3),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
