import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../features/auth/data/supabase_auth_repository.dart';

/// Base URL of the deployed FastAPI backend.
///
/// Render's free tier stops the instance after ~15 minutes idle, so the first
/// request of a session pays a cold start. Measured 2026-09-12: 43.9 s.
const String kApiBaseUrl = 'https://kalacart-api.onrender.com';

/// Long enough to absorb a cold start (~44 s measured) plus the slowest live
/// call (/image/enhance, 6-8 s warm). Anything shorter turns a sleeping server
/// into a spurious error on the first tap.
const Duration kApiReceiveTimeout = Duration(seconds: 120);

/// True while the very first backend call of this app session is in flight.
///
/// Screens watch this to show "Waking the server…" instead of a bare spinner,
/// so a 44 s cold start reads as progress rather than as a hang.
final backendWakingProvider = StateProvider<bool>((ref) => false);

/// Set once the first response of the session arrives; after that the instance
/// is warm and calls return in well under a second.
final _backendWarm = _WarmFlag();

class _WarmFlag {
  bool value = false;
}

/// Attaches the caller's Supabase access token to every backend request.
///
/// The backend verifies these against the project JWKS (ES256) and resolves the
/// user through `profiles.auth_user_id`, so the token must be the live one from
/// the current session rather than a cached copy.
class _AuthInterceptor extends Interceptor {
  _AuthInterceptor(this._ref);

  final Ref _ref;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final session = _ref.read(supabaseClientProvider).auth.currentSession;
    final token = session?.accessToken;
    if (token != null && token.isNotEmpty) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    if (!_backendWarm.value) {
      // Flip the banner on for the first call only.
      Future<void>.microtask(
        () => _ref.read(backendWakingProvider.notifier).state = true,
      );
    }
    handler.next(options);
  }

  @override
  void onResponse(Response<dynamic> response, ResponseInterceptorHandler handler) {
    _markWarm();
    handler.next(response);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    _markWarm();
    handler.next(err);
  }

  void _markWarm() {
    _backendWarm.value = true;
    Future<void>.microtask(
      () => _ref.read(backendWakingProvider.notifier).state = false,
    );
  }
}

/// The single configured Dio instance for backend calls.
final apiClientProvider = Provider<Dio>((ref) {
  final dio = Dio(
    BaseOptions(
      baseUrl: kApiBaseUrl,
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: kApiReceiveTimeout,
      sendTimeout: kApiReceiveTimeout,
      // Let Dio throw on any non-2xx so one path handles failure. The body is
      // still attached to the DioException, so `apiErrorMessage` can read the
      // server's own `detail`/`message` out of it.
      validateStatus: (status) => status != null && status >= 200 && status < 300,
    ),
  );
  dio.interceptors.add(_AuthInterceptor(ref));
  return dio;
});

/// Turns any backend failure into a sentence suitable for a SnackBar.
///
/// Mirrors `authErrorMessage` in the auth layer: one formatter, used everywhere,
/// rather than each screen re-deriving its own wording.
String apiErrorMessage(Object error) {
  if (error is DioException) {
    if (error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.receiveTimeout ||
        error.type == DioExceptionType.sendTimeout) {
      return 'The server is waking up and took too long. Please try again.';
    }
    if (error.type == DioExceptionType.connectionError) {
      return 'No internet connection. Please check your network and try again.';
    }
    final data = error.response?.data;
    final code = error.response?.statusCode;
    // FastAPI puts the reason in `detail`; our own envelope uses `message`.
    // Surface whichever is present with the status attached — a bare "service
    // unavailable" hides which of validation, auth or the upstream model failed.
    if (data is Map && data['message'] is String) return '${data['message']} (HTTP $code)';
    if (data is Map && data['detail'] is String) return '${data['detail']} (HTTP $code)';
    if (data is Map && data['detail'] is List) {
      // 422 from Pydantic: a list of per-field errors.
      final first = (data['detail'] as List).firstOrNull;
      if (first is Map && first['msg'] is String) return '${first['msg']} (HTTP 422)';
    }
    if (code == 401) return 'Please sign in again to continue.';
    if (code == 429) return 'Too many requests. Please wait a moment and try again.';
    if (code == 413) return 'That image is too large. Please choose a smaller photo.';
    return 'The service is unavailable right now (HTTP $code). Please try again.';
  }
  return 'Something went wrong. Please try again.';
}

/// Reads the `{success, message, ...}` envelope the backend returns and raises
/// the server's own message when `success` is false.
Map<String, dynamic> unwrapResponse(Response<dynamic> response) {
  final data = response.data;
  if (data is! Map<String, dynamic>) {
    throw DioException(
      requestOptions: response.requestOptions,
      response: response,
      message: 'Unexpected response from the server.',
    );
  }
  if (data['success'] == false) {
    throw DioException(
      requestOptions: response.requestOptions,
      response: response,
      message: (data['message'] as String?) ?? 'The request failed.',
    );
  }
  return data;
}
