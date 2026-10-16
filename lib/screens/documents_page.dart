import 'dart:convert';
import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import '../services/api_service.dart';

class DocumentsPage extends StatefulWidget {
  final VoidCallback? onSessionExpired;

  const DocumentsPage({super.key, this.onSessionExpired});

  @override
  State<DocumentsPage> createState() => _DocumentsPageState();
}

class _DocumentsPageState extends State<DocumentsPage> {
  static const _baseUrl = 'https://trippie-auto-ai.vercel.app';

  String? _token;
  Map<String, dynamic>? _user;
  Map<String, dynamic>? _document;
  Uint8List? _selectedBytes;
  String? _selectedFilename;
  bool _loading = true;
  bool _busy = false;
  String? _error;
  String? _notice;

  @override
  void initState() {
    super.initState();
    _restoreSession();
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
    try {
      final restored = await ApiService.restoreSession();
      if (!restored) {
        if (mounted) {
          setState(() {
            _loading = false;
            _token = null;
            _error = 'Your shared account session is unavailable. Sign in from the app entry screen to continue.';
          });
        }
        return;
      }
      _token = await ApiService.getAccessToken();
      _user = await ApiService.getCurrentUser();
      await _loadDocument();
    } catch (e) {
      _error = e.toString().replaceFirst('Exception: ', '');
    }
    if (mounted) setState(() => _loading = false);
  }

  Future<http.Response> _authorizedRequest(String method, String path) =>
      ApiService.authorizedRequest(method, path);

  Future<void> _handleExpiredSession() async {
    await ApiService.clearSession();
    if (!mounted) return;
    setState(() {
      _token = null;
      _user = null;
      _document = null;
      _error = 'Your shared session expired. Sign in again to access private documents.';
      _notice = null;
    });
    widget.onSessionExpired?.call();
  }

  Future<void> _loadDocument() async {
    final response = await _authorizedRequest('GET', '/api/documents/cv');

    if (response.statusCode == 401 || response.statusCode == 403) {
      await _handleExpiredSession();
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

  Future<http.Response> _sendCvUpload(
    Uint8List bytes,
    String filename,
    String token,
  ) async {
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$_baseUrl/api/documents/cv'),
    );
    request.headers['Authorization'] = 'Bearer $token';
    request.files.add(
      http.MultipartFile.fromBytes('file', bytes, filename: filename),
    );
    return http.Response.fromStream(await request.send());
  }

  Future<void> _uploadCv() async {
    final bytes = _selectedBytes;
    final filename = _selectedFilename;
    if (bytes == null || filename == null) return;

    setState(() {
      _busy = true;
      _error = null;
      _notice = null;
    });

    try {
      var token = await ApiService.getAccessToken();
      if (token == null || token.isEmpty) {
        await _handleExpiredSession();
        return;
      }
      var response = await _sendCvUpload(bytes, filename, token);
      if (response.statusCode == 401 && await ApiService.refreshAccessToken()) {
        token = (await ApiService.getAccessToken()) ?? '';
        if (token.isNotEmpty) {
          response = await _sendCvUpload(bytes, filename, token);
        }
      }
      if (response.statusCode == 401 || response.statusCode == 403) {
        await _handleExpiredSession();
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

      if (response.statusCode == 401 || response.statusCode == 403) {
        await _handleExpiredSession();
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
      if (response.statusCode == 401 || response.statusCode == 403) {
        await _handleExpiredSession();
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

  String _formatSize(dynamic value) {
    final bytes = value is num ? value.toInt() : 0;
    if (bytes < 1024) return '$bytes B';
    return '${(bytes / 1024).toStringAsFixed(1)} KB';
  }

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(title: const Text('Private Documents')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _token == null
          ? _buildSessionRequired(colors)
          : _buildDocuments(colors),
    );
  }

  Widget _buildSessionRequired(ColorScheme colors) {
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        Icon(Icons.lock_person_rounded, size: 54, color: colors.primary),
        const SizedBox(height: 16),
        Text(
          'Private documents need your shared account session',
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: 8),
        const Text(
          'Documents no longer has a separate sign-in. Sign in once at the app entry screen, then return here.',
          textAlign: TextAlign.center,
        ),
        if (_error != null) ...[
          const SizedBox(height: 16),
          _messageBox(_error!, colors.error),
        ],
        const SizedBox(height: 16),
        OutlinedButton.icon(
          onPressed: widget.onSessionExpired,
          icon: const Icon(Icons.login_rounded),
          label: const Text('Return to shared sign-in'),
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
