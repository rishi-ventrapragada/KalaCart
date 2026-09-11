import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../network/connectivity_service.dart';
import '../sync/sync_manager.dart';

class OfflineStatusBar extends ConsumerWidget {
  const OfflineStatusBar({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final netStatus = ref.watch(networkStatusProvider).value ?? NetworkStatus.online;
    final pendingCount = ref.watch(syncManagerProvider).length;

    if (netStatus == NetworkStatus.online && pendingCount == 0) {
      return const SizedBox.shrink();
    }

    final isOffline = netStatus == NetworkStatus.offline;
    final is2G = netStatus == NetworkStatus.lowBandwidth2G;

    final bgColor = isOffline
        ? const Color(0xFFC62828)
        : (is2G ? const Color(0xFFE65100) : const Color(0xFF1565C0));

    final icon = isOffline
        ? Icons.cloud_off
        : (is2G ? Icons.network_check : Icons.sync);

    final text = isOffline
        ? 'Offline Mode · Browsing cached crafts (${pendingCount > 0 ? '$pendingCount pending sync' : 'Read-only'})'
        : (is2G
            ? 'Low 2G Network · Lite images & offline sync active'
            : 'Syncing $pendingCount pending craft actions...');

    return Container(
      width: double.infinity,
      color: bgColor,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      child: Row(
        children: [
          Icon(icon, color: Colors.white, size: 14),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold),
            ),
          ),
          if (isOffline)
            InkWell(
              onTap: () {
                ref.read(connectivityServiceProvider).setNetworkStatus(NetworkStatus.online);
              },
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: const Text(
                  'Reconnect',
                  style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
