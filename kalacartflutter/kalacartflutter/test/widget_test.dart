import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kalacart/core/constants/app_constants.dart';
import 'package:kalacart/features/auth/data/auth_repository.dart';
import 'package:kalacart/main.dart';

void main() {
  testWidgets('KalaCart App smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          // No Supabase in tests: run against the in-memory repository.
          authRepositoryProvider.overrideWithValue(MockAuthRepository()),
        ],
        child: const KalaCartApp(),
      ),
    );

    // Initial frame on /splash screen
    await tester.pump();
    expect(find.text(AppConstants.appName), findsOneWidget);
    expect(find.text(AppConstants.appTagline), findsOneWidget);

    // Let the splash animation finish and route to the welcome screen.
    await tester.pumpAndSettle(const Duration(seconds: 3));
    expect(find.text('Get Started'), findsOneWidget);
  });
}
