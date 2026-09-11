import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class LocalDataStore {
  final Map<String, dynamic> _memoryCache = {};
  final Map<String, DateTime> _cacheTimestamps = {};

  Future<void> put(String key, dynamic value) async {
    _memoryCache[key] = value;
    _cacheTimestamps[key] = DateTime.now();
  }

  T? get<T>(String key) {
    final value = _memoryCache[key];
    if (value is T) return value;
    return null;
  }

  bool hasKey(String key) => _memoryCache.containsKey(key);

  DateTime? getTimestamp(String key) => _cacheTimestamps[key];

  Future<void> remove(String key) async {
    _memoryCache.remove(key);
    _cacheTimestamps.remove(key);
  }

  Future<void> clearAll() async {
    _memoryCache.clear();
    _cacheTimestamps.clear();
  }
}

final localDataStoreProvider = Provider<LocalDataStore>((ref) {
  return LocalDataStore();
});
