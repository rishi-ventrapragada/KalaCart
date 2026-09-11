class AppException implements Exception {
  final String message;
  final int? code;
  final dynamic details;

  const AppException(this.message, [this.code, this.details]);

  @override
  String toString() => 'AppException: $message (code: $code)';
}

class NetworkException extends AppException {
  const NetworkException([super.message = 'Network connectivity error', super.details]);
}

class ServerException extends AppException {
  const ServerException([super.message = 'Server communication error', super.code, super.details]);
}
