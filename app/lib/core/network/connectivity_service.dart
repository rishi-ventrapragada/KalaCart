import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';

enum NetworkStatus {
  online,
  lowBandwidth2G,
  offline,
}

class ConnectivityService {
  final _statusController = StreamController<NetworkStatus>.broadcast();
  NetworkStatus _currentStatus = NetworkStatus.online;

  ConnectivityService() {
    _statusController.add(_currentStatus);
  }

  NetworkStatus get currentStatus => _currentStatus;
  Stream<NetworkStatus> get onStatusChanged => _statusController.stream;

  bool get isOnline => _currentStatus != NetworkStatus.offline;
  bool get isLowBandwidth => _currentStatus == NetworkStatus.lowBandwidth2G;

  /// Simulate changing connection status (e.g. going into rural craft village without 4G)
  void setNetworkStatus(NetworkStatus status) {
    if (_currentStatus != status) {
      _currentStatus = status;
      _statusController.add(status);
    }
  }

  void toggleOfflineMode() {
    if (_currentStatus == NetworkStatus.offline) {
      setNetworkStatus(NetworkStatus.online);
    } else {
      setNetworkStatus(NetworkStatus.offline);
    }
  }

  void dispose() {
    _statusController.close();
  }
}

final connectivityServiceProvider = Provider<ConnectivityService>((ref) {
  final service = ConnectivityService();
  ref.onDispose(() => service.dispose());
  return service;
});

final networkStatusProvider = StreamProvider<NetworkStatus>((ref) {
  final service = ref.watch(connectivityServiceProvider);
  return service.onStatusChanged;
});

final isOnlineProvider = Provider<bool>((ref) {
  final status = ref.watch(networkStatusProvider).value ?? NetworkStatus.online;
  return status != NetworkStatus.offline;
});
