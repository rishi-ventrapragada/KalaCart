abstract class Failure {
  final String message;
  final int? statusCode;

  const Failure(this.message, [this.statusCode]);

  @override
  String toString() => '$runtimeType(message: $message, statusCode: $statusCode)';
}

class ServerFailure extends Failure {
  const ServerFailure([super.message = 'Server error occurred', super.statusCode]);
}

class NetworkFailure extends Failure {
  const NetworkFailure([super.message = 'Please check your internet connection']);
}

class CacheFailure extends Failure {
  const CacheFailure([super.message = 'Local cache error occurred']);
}

class ValidationFailure extends Failure {
  const ValidationFailure([super.message = 'Invalid data provided']);
}
