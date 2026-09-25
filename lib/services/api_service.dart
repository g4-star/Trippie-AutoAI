import 'dart:convert';

import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = 'http://192.168.1.197:8000';

  static Future<Map<String, dynamic>> prepareApplication(
    int userId,
    int jobId,
  ) async {
    final response = await http.post(
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
    final response = await http.get(Uri.parse('$baseUrl/api/jobs'));

    if (response.statusCode != 200) {
      throw Exception('Failed to load jobs: ${response.statusCode}');
    }

    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> getApplications(int userId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/applications/$userId'),
    );

    if (response.statusCode != 200) {
      throw Exception('Failed to load applications: ${response.statusCode}');
    }

    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> updateApplicationStatus(
    int applicationId,
    String status,
  ) async {
    final response = await http.put(
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
    final response = await http.post(
      Uri.parse('$baseUrl/api/gmail/sync/$userId'),
    );

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
    final response = await http.get(Uri.parse('$baseUrl/api/emails/$userId'));

    if (response.statusCode != 200) {
      throw Exception('Failed to load emails: ${response.statusCode}');
    }

    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> getPendingReplies(int userId) async {
    final response = await http.get(
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
    final response = await http.post(
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
    final response = await http.patch(
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
    final response = await http.post(
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
    final response = await http.post(
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
    final response = await http.get(Uri.parse('$baseUrl/api/agent/$userId'));

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
    final response = await http.post(
      Uri.parse('$baseUrl/api/agent/$userId/run'),
    );

    final body = jsonDecode(response.body);

    if (response.statusCode != 200) {
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
    final response = await http.post(
      Uri.parse('$baseUrl/api/agent/$userId/stop'),
    );

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
    final response = await http.get(
      Uri.parse('$baseUrl/api/dashboard/$userId'),
    );

    if (response.statusCode != 200) {
      throw Exception('Failed to load dashboard: ${response.statusCode}');
    }

    return jsonDecode(response.body) as Map<String, dynamic>;
  }


  static Future<Map<String, dynamic>> getSettings(
    int userId,
  ) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/settings/$userId'),
    );

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
    final response = await http.patch(
      Uri.parse('$baseUrl/api/settings/$userId'),
      headers: {
        'Content-Type': 'application/json',
      },
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
