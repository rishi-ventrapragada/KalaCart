import 'package:flutter/material.dart';
import '../constants/app_radius.dart';

class CachedDataBadge extends StatelessWidget {
  final DateTime? cachedAt;
  final VoidCallback? onRefresh;

  const CachedDataBadge({
    super.key,
    this.cachedAt,
    this.onRefresh,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.amber.shade100,
        borderRadius: AppRadius.borderSm,
        border: Border.all(color: Colors.amber.shade400, width: 1),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.offline_pin_outlined, size: 13, color: Colors.amber.shade900),
          const SizedBox(width: 4),
          Text(
            'Offline Cache',
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.bold,
              color: Colors.amber.shade900,
            ),
          ),
          if (onRefresh != null) ...[
            const SizedBox(width: 4),
            InkWell(
              onTap: onRefresh,
              child: Icon(Icons.refresh, size: 12, color: Colors.amber.shade900),
            ),
          ],
        ],
      ),
    );
  }
}
