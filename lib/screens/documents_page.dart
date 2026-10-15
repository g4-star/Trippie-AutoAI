import 'dart:convert';
import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

class DocumentsPage extends StatefulWidget {
  const DocumentsPage({super.key});

  @override
  State<DocumentsPage> createState() => _DocumentsPageState();
}

class _DocumentsPageState extends State<DocumentsPage> {
  static const _baseUrl = 'https://trippie-auto-ai.vercel.app';
  static const _tokenKey = 'trippie_backend_access_token';
  static const _storage = FlutterSecureStorage();

  final _email = TextEditingController();
  final _password = TextEditingController();
  final _name = TextEditingController();

  String? _token;
  Map<String, dynamic>? _user;
  Map<String, dynamic>? _document;
  Uint8List? _selectedBytes;
  String? _selectedFilename;
  bool _registerMode = false;
  bool _loading = true;
  bool _busy = false;
  String? _error;
  String? _notice;

  @override
  void initState() {
    super.initState();
    _restoreSession();
  }

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    _name.dispose();
    super.dispose();
  }

  Map<String, dynamic> _decodeMap(String body) {
    final decoded = jsonDecode(body);
    return decoded is Map<String, dynamic> ? decoded : {};
  }

  String _message(http.Response response) {
    try {
      final body = _decodeMap(response.body);
      return body['detail']?.toString() ??
          'Request failed (${response.statusCode}).';
    } catch (_) {
      return 'Request failed (${response.statusCode}).';
    }
  }

  Future<void> _restoreSession() async {
    final token = await _storage.read(key: _tokenKey);
    if (token == null || token.isEmpty) {
      if (mounted) setState(() => _loading = false);
      return;
    }

    _token = token;
    try {
      final response = await http.get(
        Uri.parse('$_baseUrl/api/auth/me'),
        headers: {'Authorization': 'Bearer $token'},
      );
      if (response.statusCode == 200) {
        _user = _decodeMap(response.body);
        await _loadDocument();
      } else {
        await _storage.delete(key: _tokenKey);
        _token = null;
        _error = 'Your session expired. Please sign in again.';
      }
    } catch (_) {
      _error = 'Could not connect to the service. Check your internet.';
    }

    if (mounted) setState(() => _loading = false);
  }

  Future<void> _authenticate() async {
    FocusScope.of(context).unfocus();
    setState(() {
      _busy = true;
      _error = null;
      _notice = null;
    });

    try {
      final endpoint = _registerMode ? 'register' : 'login';
      final payload = <String, dynamic>{
        'email': _email.text.trim(),
        'password': _password.text,
      };
      if (_registerMode) payload['full_name'] = _name.text.trim();

      final response = await http.post(
        Uri.parse('$_baseUrl/api/auth/$endpoint'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(payload),
      );

      if (response.statusCode != 200 && response.statusCode != 201) {
        throw Exception(_message(response));
      }

      final result = _decodeMap(response.body);
      final token = result['access_token']?.toString();
      final user = result['user'];

      if (token == null || token.isEmpty || user is! Map<String, dynamic>) {
        throw Exception('The server returned an invalid login response.');
      }

      await _storage.write(key: _tokenKey, value: token);
      _token = token;
      _user = user;
      _password.clear();

      await _loadDocument();
    } catch (e) {
      _error = e.toString().replaceFirst('Exception: ', '');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<http.Response> _authorizedRequest(String method, String path) async {
    final token = _token;
    if (token == null) throw Exception('Please sign in again.');

    final uri = Uri.parse('$_baseUrl$path');
    final headers = {'Authorization': 'Bearer $token'};

    switch (method) {
      case 'GET':
        return http.get(uri, headers: headers);
      case 'DELETE':
        return http.delete(uri, headers: headers);
      default:
        throw Exception('Unsupported request.');
    }
  }

  Future<void> _loadDocument() async {
    final response = await _authorizedRequest('GET', '/api/documents/cv');

    if (response.statusCode == 401) {
      await _signOut(message: 'Your session expired. Sign in again.');
      return;
    }
    if (response.statusCode != 200) throw Exception(_message(response));

    final body = _decodeMap(response.body);
    _document = body['document'] is Map<String, dynamic>
        ? body['document'] as Map<String, dynamic>
        : null;
  }

  Future<void> _pickCv() async {
    setState(() {
      _error = null;
      _notice = null;
    });

    try {
      final file = await FilePicker.pickFile(
        dialogTitle: 'Choose your CV (PDF)',
        type: FileType.custom,
        allowedExtensions: ['pdf'],
      );

      if (file == null) return;

      if (!file.name.toLowerCase().endsWith('.pdf')) {
        throw Exception('Please select a PDF file.');
      }

      final size = await file.length();
      if (size == null) {
        throw Exception(
          'Could not determine the file size. Please select it again.',
        );
      }
      if (size > 4 * 1024 * 1024) {
        throw Exception('The CV must be 4 MB or smaller.');
      }

      final bytes = await file.readAsBytes();
      if (bytes.isEmpty) {
        throw Exception('The selected file is empty.');
      }
      if (bytes.length > 4 * 1024 * 1024) {
        throw Exception('The CV must be 4 MB or smaller.');
      }

      setState(() {
        _selectedBytes = bytes;
        _selectedFilename = file.name;
      });
    } catch (e) {
      setState(() => _error = e.toString().replaceFirst('Exception: ', ''));
    }
  }

  Future<void> _uploadCv() async {
    final bytes = _selectedBytes;
    final filename = _selectedFilename;
    final token = _token;

    if (bytes == null || filename == null || token == null) return;

    setState(() {
      _busy = true;
      _error = null;
      _notice = null;
    });

    try {
      final request = http.MultipartRequest(
        'POST',
        Uri.parse('$_baseUrl/api/documents/cv'),
      );
      request.headers['Authorization'] = 'Bearer $token';
      request.files.add(
        http.MultipartFile.fromBytes('file', bytes, filename: filename),
      );

      final streamed = await request.send();
      final response = await http.Response.fromStream(streamed);

      if (response.statusCode == 401) {
        await _signOut(message: 'Your session expired. Sign in again.');
        return;
      }
      if (response.statusCode != 200 && response.statusCode != 201) {
        throw Exception(_message(response));
      }

      final body = _decodeMap(response.body);
      _document = body['document'] as Map<String, dynamic>?;
      _selectedBytes = null;
      _selectedFilename = null;
      _notice = 'Your CV was uploaded successfully.';
    } catch (e) {
      _error = e.toString().replaceFirst('Exception: ', '');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _downloadCv() async {
    setState(() {
      _busy = true;
      _error = null;
      _notice = null;
    });

    try {
      final response = await _authorizedRequest(
        'GET',
        '/api/documents/cv/download',
      );

      if (response.statusCode == 401) {
        await _signOut(message: 'Your session expired. Sign in again.');
        return;
      }
      if (response.statusCode != 200) throw Exception(_message(response));

      final name = _document?['filename']?.toString() ?? 'cv.pdf';
      final savedPath = await FilePicker.saveFile(
        dialogTitle: 'Save your private CV',
        fileName: name.toLowerCase().endsWith('.pdf') ? name : 'cv.pdf',
        type: FileType.custom,
        allowedExtensions: ['pdf'],
        bytes: response.bodyBytes,
      );

      if (savedPath != null) _notice = 'CV saved to your chosen location.';
    } catch (e) {
      _error = e.toString().replaceFirst('Exception: ', '');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _deleteCv() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete CV?'),
        content: const Text(
          'This permanently removes your stored CV. This action cannot be undone.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Delete CV'),
          ),
        ],
      ),
    );

    if (confirmed != true || !mounted) return;

    setState(() {
      _busy = true;
      _error = null;
      _notice = null;
    });

    try {
      final response = await _authorizedRequest('DELETE', '/api/documents/cv');
      if (response.statusCode == 401) {
        await _signOut(message: 'Your session expired. Sign in again.');
        return;
      }
      if (response.statusCode != 204 && response.statusCode != 200) {
        throw Exception(_message(response));
      }

      _document = null;
      _notice = 'Your CV was deleted.';
    } catch (e) {
      _error = e.toString().replaceFirst('Exception: ', '');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _signOut({String? message}) async {
    await _storage.delete(key: _tokenKey);
    _token = null;
    _user = null;
    _document = null;
    _selectedBytes = null;
    _selectedFilename = null;
    if (!mounted) return;
    setState(() {
      _error = message;
      _notice = null;
    });
  }

  String _formatSize(dynamic value) {
    final bytes = value is num ? value.toInt() : 0;
    if (bytes < 1024) return '$bytes B';
    return '${(bytes / 1024).toStringAsFixed(1)} KB';
  }

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Private Documents'),
        actions: [
          if (_token != null)
            IconButton(
              tooltip: 'Sign out of document storage',
              onPressed: _busy ? null : () => _signOut(),
              icon: const Icon(Icons.logout_rounded),
            ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _token == null
          ? _buildAuth(colors)
          : _buildDocuments(colors),
    );
  }

  Widget _buildAuth(ColorScheme colors) {
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        const Icon(Icons.lock_person_rounded, size: 58),
        const SizedBox(height: 16),
        Text(
          _registerMode ? 'Create your account' : 'Sign in to Documents',
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.headlineSmall,
        ),
        const SizedBox(height: 8),
        const Text(
          'Your documents are tied to your authenticated backend account. '
          'Your app PIN does not sign you in here.',
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 24),
        if (_registerMode) ...[
          TextField(
            controller: _name,
            textCapitalization: TextCapitalization.words,
            decoration: const InputDecoration(
              labelText: 'Full name',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 12),
        ],
        TextField(
          controller: _email,
          keyboardType: TextInputType.emailAddress,
          autofillHints: const [AutofillHints.username, AutofillHints.email],
          decoration: const InputDecoration(
            labelText: 'Email',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _password,
          obscureText: true,
          autofillHints: [
            _registerMode ? AutofillHints.newPassword : AutofillHints.password,
          ],
          decoration: InputDecoration(
            labelText: 'Password',
            helperText: _registerMode ? 'At least 8 characters' : null,
            border: const OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 16),
        if (_error != null) _messageBox(_error!, colors.error),
        FilledButton(
          onPressed: _busy ? null : _authenticate,
          child: _busy
              ? const SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : Text(_registerMode ? 'Create account' : 'Sign in'),
        ),
        TextButton(
          onPressed: _busy
              ? null
              : () => setState(() {
                  _registerMode = !_registerMode;
                  _error = null;
                }),
          child: Text(
            _registerMode
                ? 'Already have an account? Sign in'
                : 'New backend account? Create one',
          ),
        ),
        if (_registerMode)
          const Text(
            'If your email already belongs to an existing job profile, '
            'registration will be rejected. Do not create another account '
            'to bypass that check.',
            textAlign: TextAlign.center,
          ),
      ],
    );
  }

  Widget _buildDocuments(ColorScheme colors) {
    final filename = _document?['filename']?.toString();
    final size = _document?['size_bytes'];
    final displayName = _user?['full_name']?.toString() ?? 'Account';

    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        Card(
          child: ListTile(
            leading: CircleAvatar(
              backgroundColor: colors.primaryContainer,
              child: Icon(Icons.verified_user_rounded, color: colors.primary),
            ),
            title: Text(displayName),
            subtitle: Text(_user?['email']?.toString() ?? ''),
            trailing: const Icon(Icons.lock_rounded),
          ),
        ),
        const SizedBox(height: 20),
        Text('Curriculum Vitae', style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 8),
        const Text(
          'PDF only · maximum 4 MB · stored against your signed-in account.',
        ),
        const SizedBox(height: 12),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: _document == null
                ? const ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: Icon(Icons.description_outlined, size: 36),
                    title: Text('No CV uploaded'),
                    subtitle: Text('Choose a PDF to get started.'),
                  )
                : ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: const Icon(Icons.picture_as_pdf_rounded, size: 36),
                    title: Text(filename ?? 'Your CV'),
                    subtitle: Text(
                      '${_formatSize(size)} · '
                      'Updated ${_document?['updated_at'] ?? 'recently'}',
                    ),
                    trailing: const Icon(Icons.lock_outline_rounded),
                  ),
          ),
        ),
        if (_selectedFilename != null) ...[
          const SizedBox(height: 8),
          ListTile(
            leading: const Icon(Icons.attach_file_rounded),
            title: Text(_selectedFilename!),
            subtitle: Text(_formatSize(_selectedBytes?.length ?? 0)),
            trailing: IconButton(
              tooltip: 'Remove selected file',
              onPressed: _busy
                  ? null
                  : () => setState(() {
                      _selectedBytes = null;
                      _selectedFilename = null;
                    }),
              icon: const Icon(Icons.close_rounded),
            ),
          ),
        ],
        const SizedBox(height: 12),
        OutlinedButton.icon(
          onPressed: _busy ? null : _pickCv,
          icon: const Icon(Icons.upload_file_rounded),
          label: Text(
            _document == null ? 'Choose CV PDF' : 'Choose replacement',
          ),
        ),
        const SizedBox(height: 8),
        FilledButton.icon(
          onPressed: _busy || _selectedBytes == null ? null : _uploadCv,
          icon: const Icon(Icons.cloud_upload_rounded),
          label: const Text('Upload CV securely'),
        ),
        if (_document != null) ...[
          const SizedBox(height: 8),
          OutlinedButton.icon(
            onPressed: _busy ? null : _downloadCv,
            icon: const Icon(Icons.download_rounded),
            label: const Text('Download CV'),
          ),
          TextButton.icon(
            onPressed: _busy ? null : _deleteCv,
            icon: const Icon(Icons.delete_outline_rounded),
            label: const Text('Delete CV'),
          ),
        ],
        if (_busy) ...[
          const SizedBox(height: 12),
          const LinearProgressIndicator(),
        ],
        if (_error != null) ...[
          const SizedBox(height: 12),
          _messageBox(_error!, colors.error),
        ],
        if (_notice != null) ...[
          const SizedBox(height: 12),
          _messageBox(_notice!, colors.primary),
        ],
        const SizedBox(height: 20),
        const Text(
          'Privacy: filenames and file size are shown here. The extracted '
          'CV text and private storage location are not displayed.',
          textAlign: TextAlign.center,
        ),
      ],
    );
  }

  Widget _messageBox(String message, Color color) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(message, style: TextStyle(color: color)),
    );
  }
}
