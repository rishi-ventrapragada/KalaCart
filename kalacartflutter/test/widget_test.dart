import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:kalacart/core/constants/app_constants.dart';
import 'package:kalacart/main.dart';

void main() {
  testWidgets('KalaCart App smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: KalaCartApp(),
      ),
    );

    // Initial frame on /splash screen
    await tester.pump();
    expect(find.text(AppConstants.appName), findsOneWidget);
    expect(find.text(AppConstants.appTagline), findsOneWidget);
  });
}
