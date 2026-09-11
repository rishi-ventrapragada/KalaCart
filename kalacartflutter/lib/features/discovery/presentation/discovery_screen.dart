import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_radius.dart';
import '../../../core/constants/app_spacing.dart';
import '../../../core/utils/currency_formatter.dart';
import '../../../core/widgets/app_chip.dart';
import '../../../shared/models/buyer_models.dart';

// State Provider for discovery feed
final discoveryFeedProvider = StateNotifierProvider<DiscoveryFeedNotifier, List<DiscoveryItem>>((ref) {
  return DiscoveryFeedNotifier();
});

class DiscoveryFeedNotifier extends StateNotifier<List<DiscoveryItem>> {
  DiscoveryFeedNotifier()
      : super([
          const DiscoveryItem(
            id: 'disc-01',
            type: 'story',
            title: '400-Year Kadwa Weaving Tradition',
            subtitle: 'Mohd Rafiq demonstrates the intricate gold-silver zari kadwa brocade technique in Varanasi.',
            artisanName: 'Mohd. Rafiq Ansari',
            location: 'Varanasi, Uttar Pradesh',
            craftCategory: 'Handloom & Textiles',
            likesCount: 1420,
            savesCount: 380,
            artisanId: 'art-001',
            productId: 'prod-002',
          ),
          const DiscoveryItem(
            id: 'disc-02',
            type: 'live',
            title: 'Live Workshop: Throwing Makrana Quartz Pottery',
            subtitle: 'Join Master Artisan Dr. Kripal in Jaipur shaping a 24-inch cobalt blue jar in real-time.',
            artisanName: 'Dr. Kripal Kumbh Studio',
            location: 'Jaipur, Rajasthan',
            craftCategory: 'Pottery & Terracotta',
            likesCount: 890,
            savesCount: 210,
            artisanId: 'art-002',
            liveSessionId: 'live-01',
          ),
          const DiscoveryItem(
            id: 'disc-03',
            type: 'product',
            title: 'Lost-Wax Cast Dhokra Tribal Nandi',
            subtitle: 'Direct from Kondagaon bell metal guild. 36 hours of handcrafting using wild beeswax and river clay.',
            artisanName: 'Bastar Bell Metal Guild',
            location: 'Kondagaon, Chhattisgarh',
            craftCategory: 'Brass & Metal Craft',
            price: 3200,
            likesCount: 654,
            savesCount: 195,
            artisanId: 'art-003',
            productId: 'prod-003',
          ),
          const DiscoveryItem(
            id: 'disc-04',
            type: 'collection',
            title: 'Mithila Ritual Art Heritage Collection',
            subtitle: 'Curated by Ranti village women artists using natural twig pigments and sacred folk geometry.',
            artisanName: 'Mithila Mahila Kala Kendra',
            location: 'Madhubani, Bihar',
            craftCategory: 'Paintings & Madhubani',
            price: 4800,
            likesCount: 1120,
            savesCount: 440,
            artisanId: 'art-005',
            productId: 'prod-004',
          ),
          const DiscoveryItem(
            id: 'disc-05',
            type: 'nearby',
            title: 'Kalamkari Natural Indigo Dye Vats',
            subtitle: 'Hyperlocal Craft Cluster: Explore 15 master dyers within 50km of Krishna River canal.',
            artisanName: 'Pedana Heritage Kalamkari Collective',
            location: 'Pedana, Machilipatnam',
            craftCategory: 'Handloom & Textiles',
            likesCount: 780,
            savesCount: 310,
            artisanId: 'art-004',
            productId: 'prod-002',
          ),
        ]);

  void toggleLike(String id) {
    state = state.map((item) {
      if (item.id == id) {
        final isLiked = !item.isLiked;
        return item.copyWith(
          isLiked: isLiked,
          likesCount: isLiked ? item.likesCount + 1 : item.likesCount - 1,
        );
      }
      return item;
    }).toList();
  }

  void toggleSave(String id) {
    state = state.map((item) {
      if (item.id == id) {
        final isSaved = !item.isSaved;
        return item.copyWith(
          isSaved: isSaved,
          savesCount: isSaved ? item.savesCount + 1 : item.savesCount - 1,
        );
      }
      return item;
    }).toList();
  }

  void toggleFollow(String id) {
    state = state.map((item) {
      if (item.id == id) {
        return item.copyWith(isFollowing: !item.isFollowing);
      }
      return item;
    }).toList();
  }
}

class DiscoveryScreen extends ConsumerStatefulWidget {
  const DiscoveryScreen({super.key});

  @override
  ConsumerState<DiscoveryScreen> createState() => _DiscoveryScreenState();
}

class _DiscoveryScreenState extends ConsumerState<DiscoveryScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final List<String> _tabs = ['All Feeds', 'Stories', 'Live Workshops', 'GI Clusters', 'New Drops'];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: _tabs.length, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final items = ref.watch(discoveryFeedProvider);

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            const Icon(Icons.explore_rounded, color: AppColors.primary),
            AppSpacing.gapH8,
            Text(
              'Artisan Discovery Feed',
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.search_rounded),
            tooltip: 'Search Crafts & Clusters',
            onPressed: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Search filter active across 140+ craft clusters.'),
                  behavior: SnackBarBehavior.floating,
                ),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.tune_rounded),
            tooltip: 'Filter by Region / GI Tag',
            onPressed: () => _showFilterBottomSheet(context),
          ),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(48),
          child: Container(
            alignment: Alignment.centerLeft,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
            child: TabBar(
              controller: _tabController,
              isScrollable: true,
              tabAlignment: TabAlignment.start,
              indicatorSize: TabBarIndicatorSize.tab,
              indicator: const BoxDecoration(
                color: AppColors.primary,
                borderRadius: AppRadius.borderPill,
              ),
              labelColor: Colors.white,
              unselectedLabelColor: isDark ? AppColors.textSecondaryDark : AppColors.textSecondaryLight,
              labelStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
              tabs: _tabs.map((t) => Tab(text: t)).toList(),
            ),
          ),
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildFeedList(items),
          _buildFeedList(items.where((i) => i.type == 'story').toList()),
          _buildFeedList(items.where((i) => i.type == 'live').toList()),
          _buildFeedList(items.where((i) => i.type == 'nearby' || i.type == 'collection').toList()),
          _buildFeedList(items.where((i) => i.type == 'product').toList()),
        ],
      ),
    );
  }

  Widget _buildFeedList(List<DiscoveryItem> items) {
    if (items.isEmpty) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.auto_awesome_motion_outlined, size: 48, color: AppColors.primary),
            AppSpacing.gapV12,
            Text('No stories found in this section', style: TextStyle(fontWeight: FontWeight.w600)),
            AppSpacing.gapV4,
            Text('Check back soon for new artisan broadcasts!', style: TextStyle(color: Colors.grey)),
          ],
        ),
      );
    }

    return ListView.separated(
      padding: AppSpacing.paddingAllBase,
      itemCount: items.length,
      separatorBuilder: (_, __) => AppSpacing.gapV20,
      itemBuilder: (context, index) {
        final item = items[index];
        return _DiscoveryCard(item: item);
      },
    );
  }

  void _showFilterBottomSheet(BuildContext context) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return Padding(
          padding: AppSpacing.paddingAllLg,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'Filter Discovery Feed',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close),
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
              AppSpacing.gapV12,
              const Text('Craft Specialization', style: TextStyle(fontWeight: FontWeight.w600)),
              AppSpacing.gapV8,
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  AppChip(label: 'All Crafts', isSelected: true, onSelected: (_) {}),
                  AppChip(label: 'GI Tagged Only', isSelected: false, onSelected: (_) {}),
                  AppChip(label: 'National Awardees', isSelected: false, onSelected: (_) {}),
                  AppChip(label: 'Live Streaming', isSelected: false, onSelected: (_) {}),
                  AppChip(label: 'Wholesale Ready', isSelected: false, onSelected: (_) {}),
                ],
              ),
              AppSpacing.gapV16,
              const Text('State / Region', style: TextStyle(fontWeight: FontWeight.w600)),
              AppSpacing.gapV8,
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  AppChip(label: 'Rajasthan', isSelected: false, onSelected: (_) {}),
                  AppChip(label: 'Uttar Pradesh', isSelected: false, onSelected: (_) {}),
                  AppChip(label: 'Andhra Pradesh', isSelected: false, onSelected: (_) {}),
                  AppChip(label: 'Bihar', isSelected: false, onSelected: (_) {}),
                  AppChip(label: 'Chhattisgarh', isSelected: false, onSelected: (_) {}),
                ],
              ),
              AppSpacing.gapV24,
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primary,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: AppRadius.shapeMd,
                  ),
                  onPressed: () => Navigator.pop(context),
                  child: const Text('Apply Filters', style: TextStyle(fontWeight: FontWeight.bold)),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _DiscoveryCard extends ConsumerWidget {
  final DiscoveryItem item;

  const _DiscoveryCard({required this.item});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    Color badgeColor;
    IconData badgeIcon;
    String badgeText;

    switch (item.type) {
      case 'live':
        badgeColor = const Color(0xFFD32F2F);
        badgeIcon = Icons.sensors_rounded;
        badgeText = 'LIVE NOW';
        break;
      case 'story':
        badgeColor = AppColors.secondary;
        badgeIcon = Icons.auto_stories_rounded;
        badgeText = 'ARTISAN STORY';
        break;
      case 'nearby':
        badgeColor = const Color(0xFF00796B);
        badgeIcon = Icons.near_me_rounded;
        badgeText = 'CRAFT CLUSTER';
        break;
      case 'collection':
        badgeColor = const Color(0xFFE65100);
        badgeIcon = Icons.collections_bookmark_rounded;
        badgeText = 'CURATED GUILD';
        break;
      case 'product':
      default:
        badgeColor = AppColors.primary;
        badgeIcon = Icons.verified_rounded;
        badgeText = 'GI HANDMADE';
        break;
    }

    return Container(
      decoration: BoxDecoration(
        color: isDark ? AppColors.surfaceDark : AppColors.surfaceLight,
        borderRadius: AppRadius.borderLg,
        border: Border.all(
          color: isDark ? AppColors.borderDark : AppColors.borderLight,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: isDark ? 0.2 : 0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header: Artisan Info & Follow Button
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                CircleAvatar(
                  radius: 20,
                  backgroundColor: AppColors.primaryContainer,
                  child: Text(
                    item.artisanName.isNotEmpty ? item.artisanName[0] : 'A',
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      color: AppColors.primary,
                    ),
                  ),
                ),
                AppSpacing.gapH10,
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      GestureDetector(
                        onTap: () {
                          if (item.artisanId != null) {
                            context.push('/artisan/${item.artisanId}');
                          }
                        },
                        child: Text(
                          item.artisanName,
                          style: theme.textTheme.titleSmall?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      Row(
                        children: [
                          const Icon(Icons.location_on_outlined, size: 12, color: AppColors.textTertiaryLight),
                          const SizedBox(width: 2),
                          Expanded(
                            child: Text(
                              item.location,
                              style: theme.textTheme.bodySmall?.copyWith(
                                color: isDark ? AppColors.textTertiaryDark : AppColors.textSecondaryLight,
                                fontSize: 11,
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                AppSpacing.gapH8,
                SizedBox(
                  height: 32,
                  child: OutlinedButton(
                    style: OutlinedButton.styleFrom(
                      foregroundColor: item.isFollowing ? Colors.grey : AppColors.primary,
                      side: BorderSide(
                        color: item.isFollowing ? Colors.grey.shade400 : AppColors.primary,
                        width: 1.2,
                      ),
                      padding: const EdgeInsets.symmetric(horizontal: 10),
                      shape: AppRadius.shapePill,
                    ),
                    onPressed: () {
                      ref.read(discoveryFeedProvider.notifier).toggleFollow(item.id);
                    },
                    child: Text(
                      item.isFollowing ? 'Following' : '+ Follow',
                      style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
                    ),
                  ),
                ),
              ],
            ),
          ),

          // Visual Media Canvas / Interactive Stage
          Stack(
            children: [
              Container(
                height: 220,
                width: double.infinity,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      badgeColor.withValues(alpha: 0.8),
                      badgeColor.withValues(alpha: 0.4),
                    ],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                ),
                child: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(badgeIcon, size: 54, color: Colors.white.withValues(alpha: 0.85)),
                      AppSpacing.gapV8,
                      Text(
                        item.craftCategory ?? 'Indian Handicraft',
                        style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 16,
                          letterSpacing: 0.4,
                        ),
                      ),
                      if (item.type == 'live') ...[
                        AppSpacing.gapV8,
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: Colors.black.withValues(alpha: 0.4),
                            borderRadius: AppRadius.borderPill,
                          ),
                          child: const Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(Icons.remove_red_eye_outlined, size: 12, color: Colors.white),
                              SizedBox(width: 4),
                              Text('380 Viewers Watching', style: TextStyle(color: Colors.white, fontSize: 11)),
                            ],
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
              Positioned(
                top: 12,
                left: 12,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: badgeColor,
                    borderRadius: AppRadius.borderSm,
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withValues(alpha: 0.2),
                        blurRadius: 4,
                      ),
                    ],
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(badgeIcon, size: 12, color: Colors.white),
                      const SizedBox(width: 4),
                      Text(
                        badgeText,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 0.5,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              if (item.price != null)
                Positioned(
                  bottom: 12,
                  right: 12,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                    decoration: BoxDecoration(
                      color: Colors.black.withValues(alpha: 0.75),
                      borderRadius: AppRadius.borderMd,
                    ),
                    child: Text(
                      CurrencyFormatter.formatINR(item.price!),
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                        fontSize: 14,
                      ),
                    ),
                  ),
                ),
            ],
          ),

          // Action Toolbar (Like, Save, Share, Open)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            child: Row(
              children: [
                IconButton(
                  icon: Icon(
                    item.isLiked ? Icons.favorite_rounded : Icons.favorite_border_rounded,
                    color: item.isLiked ? const Color(0xFFE53935) : null,
                  ),
                  tooltip: 'Like',
                  onPressed: () {
                    ref.read(discoveryFeedProvider.notifier).toggleLike(item.id);
                  },
                ),
                Text(
                  '${item.likesCount}',
                  style: theme.textTheme.bodySmall?.copyWith(fontWeight: FontWeight.w600),
                ),
                AppSpacing.gapH8,
                IconButton(
                  icon: Icon(
                    item.isSaved ? Icons.bookmark_rounded : Icons.bookmark_border_rounded,
                    color: item.isSaved ? AppColors.secondary : null,
                  ),
                  tooltip: 'Save to Board',
                  onPressed: () {
                    ref.read(discoveryFeedProvider.notifier).toggleSave(item.id);
                  },
                ),
                Text(
                  '${item.savesCount}',
                  style: theme.textTheme.bodySmall?.copyWith(fontWeight: FontWeight.w600),
                ),
                AppSpacing.gapH8,
                IconButton(
                  icon: const Icon(Icons.share_outlined),
                  tooltip: 'Share Handicraft',
                  onPressed: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text('Sharing link for "${item.title}" with craft heritage badge!'),
                        behavior: SnackBarBehavior.floating,
                      ),
                    );
                  },
                ),
                const Spacer(),
                if (item.productId != null)
                  ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      foregroundColor: Colors.white,
                      shape: AppRadius.shapePill,
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                    ),
                    icon: const Icon(Icons.shopping_bag_outlined, size: 14),
                    label: const Text('View Craft', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                    onPressed: () {
                      context.push('/products/${item.productId}');
                    },
                  )
                else if (item.type == 'live')
                  ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFFD32F2F),
                      foregroundColor: Colors.white,
                      shape: AppRadius.shapePill,
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                    ),
                    icon: const Icon(Icons.play_circle_outline, size: 14),
                    label: const Text('Join Live', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                    onPressed: () {
                      final sessionId = item.liveSessionId ?? 'live-01';
                      context.push('/live/$sessionId');
                    },
                  )
                else
                  OutlinedButton(
                    style: OutlinedButton.styleFrom(
                      shape: AppRadius.shapePill,
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    ),
                    child: const Text('Explore Cluster', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                    onPressed: () {
                      if (item.artisanId != null) {
                        context.push('/artisan/${item.artisanId}');
                      }
                    },
                  ),
              ],
            ),
          ),

          // Content Description
          Padding(
            padding: const EdgeInsets.fromLTRB(14, 0, 14, 14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item.title,
                  style: theme.textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                AppSpacing.gapV4,
                Text(
                  item.subtitle,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: isDark ? AppColors.textSecondaryDark : AppColors.textSecondaryLight,
                    height: 1.35,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

