import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiService {
  static const String baseUrl = 'https://trippie-auto-ai.vercel.app';
  static const String _tokenKey = 'trippie_backend_access_token';
  static const String _refreshTokenKey = 'trippie_backend_refresh_token';
  static const FlutterSecureStorage _secureStorage = FlutterSecureStorage();
  static Future<bool>? _refreshInFlight;

  static Future<String?> getAccessToken() =>
      _secureStorage.read(key: _tokenKey);

  static Future<void> clearSession() async {
    await _secureStorage.delete(key: _tokenKey);
    await _secureStorage.delete(key: _refreshTokenKey);
  }

  static Future<Map<String, dynamic>> authenticate({
    required String email,
    required String password,
    String? fullName,
    bool register = false,
  }) async {
    final payload = <String, dynamic>{
      'email': email.trim(),
      'password': password,
    };
    if (register) payload['full_name'] = (fullName ?? '').trim();

    final response = await http.post(
      Uri.parse(baseUrl + '/api/auth/' + (register ? 'register' : 'login')),
      headers: const {'Content-Type': 'application/json'},
      body: jsonEncode(payload),
    );
    final decoded = _decodeResponse(response);
    if (response.statusCode != 200 && response.statusCode != 201) {
      final detail = decoded is Map ? decoded['detail']?.toString() : null;
      throw Exception(detail ?? 'Sign-in failed (' + response.statusCode.toString() + ').');
    }
    if (decoded is! Map) {
      throw Exception('The server returned an invalid sign-in response.');
    }

    final accessToken = decoded['access_token']?.toString();
    final refreshToken = decoded['refresh_token']?.toString();
    final user = decoded['user'];
    if (accessToken == null || accessToken.isEmpty || user is! Map) {
      throw Exception('The server returned an incomplete sign-in response.');
    }

    await _secureStorage.write(key: _tokenKey, value: accessToken);
    if (refreshToken != null && refreshToken.isNotEmpty) {
      await _secureStorage.write(key: _refreshTokenKey, value: refreshToken);
    } else {
      await _secureStorage.delete(key: _refreshTokenKey);
    }
    return Map<String, dynamic>.from(user);
  }

  static dynamic _decodeResponse(http.Response response) {
    try {
      return jsonDecode(response.body);
    } catch (_) {
      return null;
    }
  }

  static Future<bool> restoreSession() async {
    final access = await _secureStorage.read(key: _tokenKey);
    final refresh = await _secureStorage.read(key: _refreshTokenKey);
    if ((access == null || access.isEmpty) &&
        (refresh == null || refresh.isEmpty)) {
      return false;
    }
    if (access == null || access.isEmpty) {
      if (!await refreshAccessToken()) return false;
    }
    try {
      final response = await _get(Uri.parse(baseUrl + '/api/auth/me'));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  static Future<bool> refreshAccessToken() {
    final existing = _refreshInFlight;
    if (existing != null) return existing;
    final pending = _performRefreshAccessToken();
    _refreshInFlight = pending;
    return pending.whenComplete(() {
      if (identical(_refreshInFlight, pending)) _refreshInFlight = null;
    });
  }

  static Future<bool> _performRefreshAccessToken() async {
    final refreshToken = await _secureStorage.read(key: _refreshTokenKey);
    if (refreshToken == null || refreshToken.isEmpty) return false;
    try {
      final response = await http.post(
        Uri.parse(baseUrl + '/api/auth/refresh'),
        headers: const {'Content-Type': 'application/json'},
        body: jsonEncode({'refresh_token': refreshToken}),
      );
      if (response.statusCode == 401 || response.statusCode == 403) {
        await clearSession();
        return false;
      }
      if (response.statusCode != 200) return false;
      final decoded = _decodeResponse(response);
      if (decoded is! Map) return false;
      final access = decoded['access_token']?.toString();
      final rotatedRefresh = decoded['refresh_token']?.toString();
      if (access == null || access.isEmpty ||
          rotatedRefresh == null || rotatedRefresh.isEmpty) {
        return false;
      }
      await _secureStorage.write(key: _tokenKey, value: access);
      await _secureStorage.write(key: _refreshTokenKey, value: rotatedRefresh);
      return true;
    } catch (_) {
      return false;
    }
  }

  static Future<void> signOut() async {
    final refreshToken = await _secureStorage.read(key: _refreshTokenKey);
    if (refreshToken != null && refreshToken.isNotEmpty) {
      try {
        await http.post(
          Uri.parse(baseUrl + '/api/auth/logout'),
          headers: const {'Content-Type': 'application/json'},
          body: jsonEncode({'refresh_token': refreshToken}),
        );
      } catch (_) {
        // Local sign-out must still complete if the network is unavailable.
      }
    }
    await clearSession();
  }

  static Future<Map<String, String>> _requestHeaders(
    Map<String, String>? supplied,
  ) async {
    final token = await _secureStorage.read(key: _tokenKey);
    return <String, String>{
      if (token != null && token.isNotEmpty) 'Authorization': 'Bearer ' + token,
      ...?supplied,
    };
  }

  static Future<http.Response> authorizedRequest(
    String method,
    String path, {
    Map<String, String>? headers,
    Object? body,
    Encoding? encoding,
  }) async {
    final uri = Uri.parse(baseUrl + path);
    switch (method.toUpperCase()) {
      case 'GET':
        return _get(uri, headers: headers);
      case 'POST':
        return _post(uri, headers: headers, body: body, encoding: encoding);
      case 'PUT':
        return _put(uri, headers: headers, body: body, encoding: encoding);
      case 'PATCH':
        return _patch(uri, headers: headers, body: body, encoding: encoding);
      case 'DELETE':
        return _sendWithRefresh(
          uri,
          headers,
          (requestHeaders) => http.delete(uri, headers: requestHeaders),
        );
      default:
        throw ArgumentError.value(method, 'method', 'Unsupported HTTP method');
    }
  }

  static bool _isAuthEndpoint(Uri uri) =>
      uri.path.endsWith('/api/auth/login') ||
      uri.path.endsWith('/api/auth/register') ||
      uri.path.endsWith('/api/auth/refresh') ||
      uri.path.endsWith('/api/auth/logout');

  static Future<http.Response> _sendWithRefresh(
    Uri uri,
    Map<String, String>? headers,
    Future<http.Response> Function(Map<String, String>) send,
  ) async {
    var requestHeaders = await _requestHeaders(headers);
    var response = await send(requestHeaders);
    if (response.statusCode == 401 &&
        !_isAuthEndpoint(uri) &&
        await refreshAccessToken()) {
      requestHeaders = await _requestHeaders(headers);
      response = await send(requestHeaders);
    }
    return response;
  }

  static Future<Map<String, dynamic>> getCurrentUser() async {
    final response = await _get(Uri.parse(baseUrl + '/api/auth/me'));
    if (response.statusCode == 401 || response.statusCode == 403) {
      throw Exception('Your session has expired. Please sign in again.');
    }
    if (response.statusCode != 200) {
      throw Exception('Unable to verify your account (' + response.statusCode.toString() + ').');
    }
    final decoded = jsonDecode(response.body);
    if (decoded is! Map) {
      throw Exception('Invalid account response from the server.');
    }
    final user = Map<String, dynamic>.from(decoded);
    if (user['id'] is! num) {
      throw Exception('The server did not return a valid user ID.');
    }
    return user;
  }

  static Future<int> getCurrentUserId() async {
    final user = await getCurrentUser();
    return (user['id'] as num).toInt();
  }

  static Future<http.Response> _get(
    Uri uri, {
    Map<String, String>? headers,
  }) => _sendWithRefresh(
    uri, headers, (requestHeaders) => http.get(uri, headers: requestHeaders));

  static Future<http.Response> _post(
    Uri uri, {
    Map<String, String>? headers,
    Object? body,
    Encoding? encoding,
  }) => _sendWithRefresh(
    uri, headers, (requestHeaders) => http.post(
      uri, headers: requestHeaders, body: body, encoding: encoding));

  static Future<http.Response> _put(
    Uri uri, {
    Map<String, String>? headers,
    Object? body,
    Encoding? encoding,
  }) => _sendWithRefresh(
    uri, headers, (requestHeaders) => http.put(
      uri, headers: requestHeaders, body: body, encoding: encoding));

  static Future<http.Response> _patch(
    Uri uri, {
    Map<String, String>? headers,
    Object? body,
    Encoding? encoding,
  }) => _sendWithRefresh(
    uri, headers, (requestHeaders) => http.patch(
      uri, headers: requestHeaders, body: body, encoding: encoding));

  static Future<Map<String, dynamic>> prepareApplication(
    int userId,
    int jobId,
  ) async {
    final response = await _post(
      Uri.parse('$baseUrl/api/applications/$userId/prepare/$jobId'),
    );

    final body = jsonDecode(response.body);

    if (response.statusCode != 200 && response.statusCode != 201) {
      final detail = body is Map<String, dynamic>
          ? body['detail']?.toString()
          : null;

      if (response.statusCode == 409) {
        throw Exception(
          detail ?? 'An application already exists for this job.',
        );
      }

      throw Exception(
        detail ?? 'Failed to prepare application: ${response.statusCode}',
      );
    }

    return body as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> getJobs() async {
    final response = await _get(Uri.parse('$baseUrl/api/jobs'));

    if (response.statusCode != 200) {
      throw Exception('Failed to load jobs: ${response.statusCode}');
    }

    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> getApplications(int userId) async {
    final response = await _get(Uri.parse('$baseUrl/api/applications/$userId'));

    if (response.statusCode != 200) {
      throw Exception('Failed to load applications: ${response.statusCode}');
    }

    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> updateApplicationStatus(
    int applicationId,
    String status,
  ) async {
    final response = await _put(
      Uri.parse('$baseUrl/api/applications/$applicationId/status'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'status': status}),
    );

    final body = jsonDecode(response.body);

    if (response.statusCode != 200) {
      final detail = body is Map<String, dynamic>
          ? body['detail']?.toString()
          : null;

      throw Exception(
        detail ?? 'Failed to update application status: ${response.statusCode}',
      );
    }

    return body as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> syncGmail(int userId) async {
    final response = await _post(Uri.parse('$baseUrl/api/gmail/sync/$userId'));

    final body = jsonDecode(response.body);

    if (response.statusCode != 200) {
      final detail = body is Map<String, dynamic>
          ? body['detail']?.toString()
          : null;

      throw Exception(detail ?? 'Failed to sync Gmail: ${response.statusCode}');
    }

    return body as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> getEmails(int userId) async {
    final response = await _get(Uri.parse('$baseUrl/api/emails/$userId'));

    if (response.statusCode != 200) {
      throw Exception('Failed to load emails: ${response.statusCode}');
    }

    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> getPendingReplies(int userId) async {
    final response = await _get(
      Uri.parse('$baseUrl/api/gmail/replies/$userId'),
    );

    final body = jsonDecode(response.body);

    if (response.statusCode != 200) {
      final detail = body is Map<String, dynamic>
          ? body['detail']?.toString()
          : null;

      throw Exception(
        detail ?? 'Failed to load pending replies: ${response.statusCode}',
      );
    }

    return body as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> generateAiReply(
    int userId,
    int emailId,
  ) async {
    final response = await _post(
      Uri.parse('$baseUrl/api/gmail/reply/generate/$userId/$emailId'),
    );

    final body = jsonDecode(response.body);

    if (response.statusCode != 200) {
      final detail = body is Map<String, dynamic>
          ? body['detail']?.toString()
          : null;

      throw Exception(
        detail ?? 'Failed to generate AI reply: ${response.statusCode}',
      );
    }

    return body as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> updateReplyDraft(
    int userId,
    int replyId,
    String body,
  ) async {
    final response = await _patch(
      Uri.parse('$baseUrl/api/gmail/reply/$userId/$replyId'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'body': body}),
    );

    final responseBody = jsonDecode(response.body);

    if (response.statusCode != 200) {
      final detail = responseBody is Map<String, dynamic>
          ? responseBody['detail']?.toString()
          : null;

      throw Exception(
        detail ?? 'Failed to update reply draft: ${response.statusCode}',
      );
    }

    return responseBody as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> approveAndSendReply(
    int userId,
    int replyId,
  ) async {
    final response = await _post(
      Uri.parse('$baseUrl/api/gmail/reply/approve/$userId/$replyId'),
    );

    final body = jsonDecode(response.body);

    if (response.statusCode != 200) {
      final detail = body is Map<String, dynamic>
          ? body['detail']?.toString()
          : null;

      throw Exception(
        detail ?? 'Failed to approve and send reply: ${response.statusCode}',
      );
    }

    return body as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> rejectReply(
    int userId,
    int replyId,
  ) async {
    final response = await _post(
      Uri.parse('$baseUrl/api/gmail/reply/reject/$userId/$replyId'),
    );

    final body = jsonDecode(response.body);

    if (response.statusCode != 200) {
      final detail = body is Map<String, dynamic>
          ? body['detail']?.toString()
          : null;

      throw Exception(
        detail ?? 'Failed to reject reply: ${response.statusCode}',
      );
    }

    return body as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> getAgentStatus(int userId) async {
    final response = await _get(Uri.parse('$baseUrl/api/agent/$userId'));

    final body = jsonDecode(response.body);

    if (response.statusCode != 200) {
      final detail = body is Map<String, dynamic>
          ? body['detail']?.toString()
          : null;

      throw Exception(
        detail ?? 'Failed to load AI Agent status: ${response.statusCode}',
      );
    }

    return body as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> runAgent(int userId) async {
    final response = await _post(Uri.parse('$baseUrl/api/agent/$userId/run'));

    final body = jsonDecode(response.body);

    if (response.statusCode != 200 && response.statusCode != 202) {
      final detail = body is Map<String, dynamic>
          ? body['detail']?.toString()
          : null;

      throw Exception(
        detail ?? 'Failed to start AI Agent: ${response.statusCode}',
      );
    }

    return body as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> stopAgent(int userId) async {
    final response = await _post(Uri.parse('$baseUrl/api/agent/$userId/stop'));

    final body = jsonDecode(response.body);

    if (response.statusCode != 200) {
      final detail = body is Map<String, dynamic>
          ? body['detail']?.toString()
          : null;

      throw Exception(
        detail ?? 'Failed to stop AI Agent: ${response.statusCode}',
      );
    }

    return body as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> getDashboard(int userId) async {
    final response = await _get(Uri.parse('$baseUrl/api/dashboard/$userId'));

    if (response.statusCode != 200) {
      throw Exception('Failed to load dashboard: ${response.statusCode}');
    }

    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> getSettings(int userId) async {
    final response = await _get(Uri.parse('$baseUrl/api/settings/$userId'));

    final body = jsonDecode(response.body);

    if (response.statusCode != 200) {
      final detail = body is Map<String, dynamic>
          ? body['detail']?.toString()
          : null;

      throw Exception(
        detail ?? 'Failed to load settings: ${response.statusCode}',
      );
    }

    return body as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> updateSettings(
    int userId,
    Map<String, dynamic> updates,
  ) async {
    final response = await _patch(
      Uri.parse('$baseUrl/api/settings/$userId'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(updates),
    );

    final body = jsonDecode(response.body);

    if (response.statusCode != 200) {
      final detail = body is Map<String, dynamic>
          ? body['detail']?.toString()
          : null;

      throw Exception(
        detail ?? 'Failed to update settings: ${response.statusCode}',
      );
    }

    return body as Map<String, dynamic>;
  }
}
