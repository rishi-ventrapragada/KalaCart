import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../network/connectivity_service.dart';

enum SyncActionType {
  createRfq,
  sendQuote,
  sendMessage,
  saveProductDraft,
  updateStorefront,
  placeOrder,
}

enum SyncStatus {
  pending,
  syncing,
  synced,
  failed,
}

class PendingSyncAction {
  final String id;
  final SyncActionType type;
  final Map<String, dynamic> payload;
  final DateTime createdAt;
  final int retryCount;
  final SyncStatus status;
  final String? errorMessage;

  const PendingSyncAction({
    required this.id,
    required this.type,
    required this.payload,
    required this.createdAt,
    this.retryCount = 0,
    this.status = SyncStatus.pending,
    this.errorMessage,
  });

  PendingSyncAction copyWith({
    int? retryCount,
    SyncStatus? status,
    String? errorMessage,
  }) {
    return PendingSyncAction(
      id: id,
      type: type,
      payload: payload,
      createdAt: createdAt,
      retryCount: retryCount ?? this.retryCount,
      status: status ?? this.status,
      errorMessage: errorMessage ?? this.errorMessage,
    );
  }
}

class SyncManager extends StateNotifier<List<PendingSyncAction>> {
  final ConnectivityService _connectivityService;
  StreamSubscription<NetworkStatus>? _connSubscription;
  bool _isSyncing = false;

  SyncManager(this._connectivityService) : super([]) {
    _connSubscription = _connectivityService.onStatusChanged.listen((status) {
      if (status != NetworkStatus.offline) {
        retryAllPending();
      }
    });
  }

  /// Queue a mutation when device is in low connectivity or offline
  void queueAction({
    required SyncActionType type,
    required Map<String, dynamic> payload,
  }) {
    final action = PendingSyncAction(
      id: 'sync-${DateTime.now().millisecondsSinceEpoch}-${state.length}',
      type: type,
      payload: payload,
      createdAt: DateTime.now(),
    );
    state = [...state, action];

    // If online, immediately attempt sync
    if (_connectivityService.isOnline) {
      _processAction(action);
    }
  }

  Future<void> retryAllPending() async {
    if (_isSyncing || state.isEmpty) return;
    _isSyncing = true;

    final pendingList = state.where((a) => a.status != SyncStatus.synced).toList();
    for (final action in pendingList) {
      await _processAction(action);
    }

    _isSyncing = false;
  }

  Future<void> _processAction(PendingSyncAction action) async {
    if (!_connectivityService.isOnline) return;

    // Mark syncing
    state = state.map((a) {
      if (a.id == action.id) {
        return a.copyWith(status: SyncStatus.syncing);
      }
      return a;
    }).toList();

    try {
      // Simulate backend sync delay and conflict detection
      await Future.delayed(const Duration(milliseconds: 600));

      // Mark synced / completed
      state = state.where((a) => a.id != action.id).toList();
    } catch (e) {
      // Retry policy
      state = state.map((a) {
        if (a.id == action.id) {
          final retries = a.retryCount + 1;
          return a.copyWith(
            retryCount: retries,
            status: retries >= 3 ? SyncStatus.failed : SyncStatus.pending,
            errorMessage: 'Sync error: $e',
          );
        }
        return a;
      }).toList();
    }
  }

  void removeAction(String id) {
    state = state.where((a) => a.id != id).toList();
  }

  @override
  void dispose() {
    _connSubscription?.cancel();
    super.dispose();
  }
}

final syncManagerProvider = StateNotifierProvider<SyncManager, List<PendingSyncAction>>((ref) {
  final connectivity = ref.watch(connectivityServiceProvider);
  return SyncManager(connectivity);
});

final hasPendingSyncProvider = Provider<bool>((ref) {
  final pending = ref.watch(syncManagerProvider);
  return pending.isNotEmpty;
});
