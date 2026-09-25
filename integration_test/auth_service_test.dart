import 'package:flutter_test/flutter_test.dart';
import 'package:trippie_auto_ai/services/auth_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets(
    'AuthService works with Android secure storage',
    (tester) async {
      final auth = AuthService();

      await auth.clearCredentials();

      expect(await auth.hasPin(), isFalse);
      expect(await auth.hasPassword(), isFalse);

      await auth.savePin('4827');

      expect(await auth.hasPin(), isTrue);
      expect(await auth.verifyPin('4827'), isTrue);
      expect(await auth.verifyPin('1234'), isFalse);

      await auth.savePassword('Trippie@2026');

      expect(await auth.hasPassword(), isTrue);
      expect(
        await auth.verifyPassword('Trippie@2026'),
        isTrue,
      );
      expect(
        await auth.verifyPassword('WrongPassword'),
        isFalse,
      );

      await auth.clearCredentials();

      expect(await auth.hasPin(), isFalse);
      expect(await auth.hasPassword(), isFalse);
    },
  );
}
