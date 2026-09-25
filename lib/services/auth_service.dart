import 'dart:convert';
import 'dart:math';

import 'package:crypto/crypto.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:local_auth/local_auth.dart';

class AuthService {
  static const String _pinHashKey = 'trippie_auth_pin_hash';
  static const String _pinSaltKey = 'trippie_auth_pin_salt';

  static const String _passwordHashKey =
      'trippie_auth_password_hash';
  static const String _passwordSaltKey =
      'trippie_auth_password_salt';

  static const int _iterations = 120000;
  static const int _saltLength = 32;
  static const int _derivedKeyLength = 32;

  final FlutterSecureStorage _storage = const FlutterSecureStorage(
    aOptions: AndroidOptions(),
  );

  final LocalAuthentication _localAuth = LocalAuthentication();

  Future<bool> hasPin() async {
    final hash = await _storage.read(key: _pinHashKey);
    final salt = await _storage.read(key: _pinSaltKey);

    return hash != null &&
        hash.isNotEmpty &&
        salt != null &&
        salt.isNotEmpty;
  }

  Future<bool> hasPassword() async {
    final hash = await _storage.read(key: _passwordHashKey);
    final salt = await _storage.read(key: _passwordSaltKey);

    return hash != null &&
        hash.isNotEmpty &&
        salt != null &&
        salt.isNotEmpty;
  }

  Future<void> savePin(String pin) async {
    if (!RegExp(r'^\d{4,8}$').hasMatch(pin)) {
      throw ArgumentError(
        'PIN must contain 4 to 8 digits.',
      );
    }

    final salt = _generateSalt();

    final hash = _deriveKey(
      secret: pin,
      salt: salt,
    );

    await _storage.write(
      key: _pinSaltKey,
      value: base64UrlEncode(salt),
    );

    await _storage.write(
      key: _pinHashKey,
      value: base64UrlEncode(hash),
    );
  }

  Future<void> savePassword(String password) async {
    if (password.length < 8) {
      throw ArgumentError(
        'Password must contain at least 8 characters.',
      );
    }

    final salt = _generateSalt();

    final hash = _deriveKey(
      secret: password,
      salt: salt,
    );

    await _storage.write(
      key: _passwordSaltKey,
      value: base64UrlEncode(salt),
    );

    await _storage.write(
      key: _passwordHashKey,
      value: base64UrlEncode(hash),
    );
  }

  Future<bool> verifyPin(String pin) async {
    return _verify(
      secret: pin,
      hashKey: _pinHashKey,
      saltKey: _pinSaltKey,
    );
  }

  Future<bool> verifyPassword(String password) async {
    return _verify(
      secret: password,
      hashKey: _passwordHashKey,
      saltKey: _passwordSaltKey,
    );
  }

  Future<bool> _verify({
    required String secret,
    required String hashKey,
    required String saltKey,
  }) async {
    final storedHash = await _storage.read(key: hashKey);
    final storedSalt = await _storage.read(key: saltKey);

    if (storedHash == null ||
        storedHash.isEmpty ||
        storedSalt == null ||
        storedSalt.isEmpty) {
      return false;
    }

    try {
      final salt = base64Url.decode(storedSalt);
      final expectedHash = base64Url.decode(storedHash);

      final actualHash = _deriveKey(
        secret: secret,
        salt: salt,
      );

      return _constantTimeEquals(
        actualHash,
        expectedHash,
      );
    } catch (_) {
      return false;
    }
  }

  List<int> _generateSalt() {
    final random = Random.secure();

    return List<int>.generate(
      _saltLength,
      (_) => random.nextInt(256),
    );
  }

  List<int> _deriveKey({
    required String secret,
    required List<int> salt,
  }) {
    final passwordBytes = utf8.encode(secret);

    var block = <int>[
      ...salt,
      0,
      0,
      0,
      1,
    ];

    var u = Hmac(
      sha256,
      passwordBytes,
    ).convert(block).bytes;

    var result = List<int>.from(u);

    for (var i = 1; i < _iterations; i++) {
      u = Hmac(
        sha256,
        passwordBytes,
      ).convert(u).bytes;

      for (var j = 0; j < result.length; j++) {
        result[j] ^= u[j];
      }
    }

    return result.sublist(
      0,
      _derivedKeyLength,
    );
  }

  bool _constantTimeEquals(
    List<int> a,
    List<int> b,
  ) {
    if (a.length != b.length) {
      return false;
    }

    var difference = 0;

    for (var i = 0; i < a.length; i++) {
      difference |= a[i] ^ b[i];
    }

    return difference == 0;
  }

  Future<bool> canUseBiometrics() async {
    try {
      final supported = await _localAuth.isDeviceSupported();
      final canCheck = await _localAuth.canCheckBiometrics;

      return supported && canCheck;
    } catch (_) {
      return false;
    }
  }

  Future<bool> hasEnrolledBiometrics() async {
    try {
      final available =
          await _localAuth.getAvailableBiometrics();

      return available.isNotEmpty;
    } catch (_) {
      return false;
    }
  }

  Future<bool> authenticateWithBiometrics() async {
    try {
      final available =
          await _localAuth.getAvailableBiometrics();

      if (available.isEmpty) {
        return false;
      }

      return await _localAuth.authenticate(
        localizedReason:
            'Authenticate to unlock TrippieAutoAI',
        biometricOnly: true,
        persistAcrossBackgrounding: true,
      );
    } on LocalAuthException {
      return false;
    } catch (_) {
      return false;
    }
  }

  Future<void> clearCredentials() async {
    await _storage.delete(key: _pinHashKey);
    await _storage.delete(key: _pinSaltKey);
    await _storage.delete(key: _passwordHashKey);
    await _storage.delete(key: _passwordSaltKey);
  }
}
