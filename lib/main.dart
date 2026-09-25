import 'package:flutter/material.dart';

import 'services/api_service.dart';

void main() {
  runApp(const TrippieAutoAI());
}

class TrippieAutoAI extends StatefulWidget {
  const TrippieAutoAI({super.key});

  @override
  State<TrippieAutoAI> createState() => _TrippieAutoAIState();
}

class _TrippieAutoAIState extends State<TrippieAutoAI> {
  ThemeMode _themeMode = ThemeMode.dark;

  void _setTheme(ThemeMode mode) {
    setState(() {
      _themeMode = mode;
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'TrippieAutoAI',
      themeMode: _themeMode,
      theme: ThemeData(
        brightness: Brightness.light,
        useMaterial3: true,
        scaffoldBackgroundColor: const Color(0xFFF5F6FA),
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.deepPurple,
          brightness: Brightness.light,
        ),
      ),
      darkTheme: ThemeData(
        brightness: Brightness.dark,
        useMaterial3: true,
        scaffoldBackgroundColor: const Color(0xFF080B12),
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.deepPurple,
          brightness: Brightness.dark,
        ),
      ),
      home: LockScreen(onThemeChanged: _setTheme, currentTheme: _themeMode),
    );
  }
}

class LockScreen extends StatefulWidget {
  final void Function(ThemeMode) onThemeChanged;
  final ThemeMode currentTheme;

  const LockScreen({
    super.key,
    required this.onThemeChanged,
    required this.currentTheme,
  });

  @override
  State<LockScreen> createState() => _LockScreenState();
}

class _LockScreenState extends State<LockScreen> {
  final TextEditingController _pinController = TextEditingController();
  String? _error;

  void _unlock() {
    if (_pinController.text.isEmpty) {
      setState(() {
        _error = 'Enter your PIN to continue';
      });
      return;
    }

    Navigator.of(context).pushReplacement(
      MaterialPageRoute(
        builder: (_) => MainShell(
          onThemeChanged: widget.onThemeChanged,
          currentTheme: widget.currentTheme,
        ),
      ),
    );
  }

  @override
  void dispose() {
    _pinController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(28),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: Column(
                children: [
                  Container(
                    width: 86,
                    height: 86,
                    decoration: BoxDecoration(
                      color: Colors.deepPurple.withValues(alpha: 0.16),
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: Colors.deepPurple.withValues(alpha: 0.35),
                      ),
                    ),
                    child: const Icon(
                      Icons.smart_toy_rounded,
                      size: 44,
                      color: Colors.deepPurpleAccent,
                    ),
                  ),
                  const SizedBox(height: 24),
                  const Text(
                    'TrippieAutoAI',
                    style: TextStyle(fontSize: 30, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Your personal AI job agent',
                    style: TextStyle(
                      color: Colors.white.withValues(alpha: 0.55),
                      fontSize: 15,
                    ),
                  ),
                  const SizedBox(height: 52),
                  const Align(
                    alignment: Alignment.centerLeft,
                    child: Text(
                      'Welcome back',
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Align(
                    alignment: Alignment.centerLeft,
                    child: Text(
                      'Unlock TrippieAutoAI to continue.',
                      style: TextStyle(
                        color: Colors.white.withValues(alpha: 0.55),
                      ),
                    ),
                  ),
                  const SizedBox(height: 28),
                  TextField(
                    controller: _pinController,
                    obscureText: true,
                    keyboardType: TextInputType.number,
                    maxLength: 8,
                    decoration: InputDecoration(
                      labelText: 'PIN',
                      hintText: 'Enter your PIN',
                      prefixIcon: const Icon(Icons.lock_outline_rounded),
                      errorText: _error,
                      counterText: '',
                      filled: true,
                      fillColor: const Color(0xFF11151F),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(18),
                        borderSide: BorderSide.none,
                      ),
                    ),
                    onSubmitted: (_) => _unlock(),
                  ),
                  const SizedBox(height: 14),
                  SizedBox(
                    width: double.infinity,
                    height: 54,
                    child: FilledButton(
                      onPressed: _unlock,
                      child: const Text(
                        'Unlock',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 14),
                  SizedBox(
                    width: double.infinity,
                    height: 54,
                    child: OutlinedButton.icon(
                      onPressed: () {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text(
                              'Biometric authentication will be connected next.',
                            ),
                          ),
                        );
                      },
                      icon: const Icon(Icons.fingerprint),
                      label: const Text('Use fingerprint'),
                    ),
                  ),
                  const SizedBox(height: 22),
                  TextButton(
                    onPressed: () {},
                    child: const Text('Forgot PIN?'),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class MainShell extends StatefulWidget {
  final void Function(ThemeMode) onThemeChanged;
  final ThemeMode currentTheme;

  const MainShell({
    super.key,
    required this.onThemeChanged,
    required this.currentTheme,
  });

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int _currentIndex = 0;

  List<Widget> get _pages => [
    const DashboardPage(),
    const JobsPage(),
    const ApplicationsPage(),
    const EmailPage(),
    SettingsPage(
      onThemeChanged: widget.onThemeChanged,
      currentTheme: widget.currentTheme,
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(index: _currentIndex, children: _pages),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
        backgroundColor: const Color(0xFF0D1119),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.home_outlined),
            selectedIcon: Icon(Icons.home_rounded),
            label: 'Home',
          ),
          NavigationDestination(
            icon: Icon(Icons.work_outline_rounded),
            selectedIcon: Icon(Icons.work_rounded),
            label: 'Jobs',
          ),
          NavigationDestination(
            icon: Icon(Icons.description_outlined),
            selectedIcon: Icon(Icons.description_rounded),
            label: 'Applications',
          ),
          NavigationDestination(
            icon: Icon(Icons.mail_outline_rounded),
            selectedIcon: Icon(Icons.mail_rounded),
            label: 'Email',
          ),
          NavigationDestination(
            icon: Icon(Icons.settings_outlined),
            selectedIcon: Icon(Icons.settings_rounded),
            label: 'Settings',
          ),
        ],
      ),
    );
  }
}

class _AiAgentPanel extends StatelessWidget {
  final bool running;
  final bool loading;
  final String? error;

  final bool automaticJobDiscovery;
  final bool automaticApplication;
  final bool emailMonitoring;
  final bool autoReply;
  final bool requireApproval;

  final Future<void> Function() onRun;
  final Future<void> Function() onStop;

  const _AiAgentPanel({
    required this.running,
    required this.loading,
    required this.error,
    required this.automaticJobDiscovery,
    required this.automaticApplication,
    required this.emailMonitoring,
    required this.autoReply,
    required this.requireApproval,
    required this.onRun,
    required this.onStop,
  });

  Widget _settingRow(
    BuildContext context, {
    required IconData icon,
    required String title,
    required String subtitle,
    required bool enabled,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor.withValues(alpha: 0.55),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        children: [
          Icon(
            icon,
            size: 21,
            color: enabled ? Colors.deepPurpleAccent : Colors.grey,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 2),
                Text(
                  subtitle,
                  style: TextStyle(
                    fontSize: 12,
                    color: Theme.of(context).textTheme.bodySmall?.color
                        ?.withValues(alpha: 0.7),
                  ),
                ),
              ],
            ),
          ),
          Icon(
            enabled ? Icons.check_circle_rounded : Icons.cancel_outlined,
            size: 20,
            color: enabled ? Colors.greenAccent : Colors.grey,
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final bottomInset = MediaQuery.of(context).viewInsets.bottom;

    return SafeArea(
      child: Padding(
        padding: EdgeInsets.fromLTRB(20, 12, 20, 20 + bottomInset),
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 42,
                  height: 4,
                  decoration: BoxDecoration(
                    color: Colors.grey.withValues(alpha: 0.35),
                    borderRadius: BorderRadius.circular(10),
                  ),
                ),
              ),
              const SizedBox(height: 22),
              Row(
                children: [
                  Container(
                    width: 48,
                    height: 48,
                    decoration: BoxDecoration(
                      color: Colors.deepPurple.withValues(alpha: 0.18),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(
                      Icons.smart_toy_rounded,
                      color: Colors.deepPurpleAccent,
                      size: 26,
                    ),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'AI Agent',
                          style: TextStyle(
                            fontSize: 22,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Row(
                          children: [
                            Icon(
                              Icons.circle,
                              size: 9,
                              color: running ? Colors.greenAccent : Colors.grey,
                            ),
                            const SizedBox(width: 7),
                            Text(
                              running ? 'RUNNING' : 'STOPPED',
                              style: TextStyle(
                                color: running
                                    ? Colors.greenAccent
                                    : Colors.grey,
                                fontSize: 12,
                                fontWeight: FontWeight.bold,
                                letterSpacing: 0.8,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 22),
              Text(
                running
                    ? 'Your agent is monitoring enabled automation tasks in the background.'
                    : 'Automation is currently paused. Start the agent when you want background processing to resume.',
                style: TextStyle(
                  height: 1.45,
                  color: Theme.of(context).textTheme.bodyMedium?.color
                      ?.withValues(alpha: 0.75),
                ),
              ),
              if (error != null) ...[
                const SizedBox(height: 14),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.red.withValues(alpha: 0.10),
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(
                      color: Colors.red.withValues(alpha: 0.25),
                    ),
                  ),
                  child: Row(
                    children: [
                      const Icon(
                        Icons.error_outline_rounded,
                        color: Colors.redAccent,
                      ),
                      const SizedBox(width: 10),
                      Expanded(child: Text(error!)),
                    ],
                  ),
                ),
              ],
              const SizedBox(height: 22),
              Text(
                'AUTOMATION',
                style: TextStyle(
                  fontSize: 12,
                  letterSpacing: 1.5,
                  fontWeight: FontWeight.bold,
                  color: Theme.of(context).textTheme.bodySmall?.color
                      ?.withValues(alpha: 0.7),
                ),
              ),
              const SizedBox(height: 12),
              _settingRow(
                context,
                icon: Icons.search_rounded,
                title: 'Job discovery',
                subtitle: automaticJobDiscovery
                    ? 'Automatically discover jobs'
                    : 'Disabled',
                enabled: automaticJobDiscovery,
              ),
              _settingRow(
                context,
                icon: Icons.send_rounded,
                title: 'Automatic applications',
                subtitle: automaticApplication
                    ? 'Enabled'
                    : 'Currently disabled',
                enabled: automaticApplication,
              ),
              _settingRow(
                context,
                icon: Icons.mail_outline_rounded,
                title: 'Email monitoring',
                subtitle: emailMonitoring
                    ? 'Monitor Gmail automatically'
                    : 'Disabled',
                enabled: emailMonitoring,
              ),
              _settingRow(
                context,
                icon: Icons.auto_awesome_rounded,
                title: 'AI replies',
                subtitle: autoReply
                    ? 'Automatic replies enabled'
                    : 'Automatic replies disabled',
                enabled: autoReply,
              ),
              _settingRow(
                context,
                icon: Icons.verified_user_outlined,
                title: 'Approval required',
                subtitle: requireApproval
                    ? 'Sensitive replies require approval'
                    : 'Approval not required',
                enabled: requireApproval,
              ),
              const SizedBox(height: 14),
              SizedBox(
                width: double.infinity,
                height: 52,
                child: loading
                    ? const Center(child: CircularProgressIndicator())
                    : running
                    ? ElevatedButton.icon(
                        onPressed: onStop,
                        icon: const Icon(Icons.stop_circle_outlined),
                        label: const Text(
                          'Stop Agent',
                          style: TextStyle(fontWeight: FontWeight.bold),
                        ),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.red.withValues(alpha: 0.15),
                          foregroundColor: Colors.redAccent,
                        ),
                      )
                    : ElevatedButton.icon(
                        onPressed: onRun,
                        icon: const Icon(Icons.play_circle_outline_rounded),
                        label: const Text(
                          'Run Agent',
                          style: TextStyle(fontWeight: FontWeight.bold),
                        ),
                      ),
              ),
              const SizedBox(height: 10),
              Center(
                child: Text(
                  'The master agent switch controls background automation.',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 11,
                    color: Theme.of(context).textTheme.bodySmall?.color
                        ?.withValues(alpha: 0.55),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class DashboardPage extends StatefulWidget {
  const DashboardPage({super.key});

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  bool _loading = true;
  String? _error;

  bool _agentLoading = true;
  bool _agentRunning = false;
  String? _agentError;

  bool _automaticJobDiscovery = true;
  bool _automaticApplication = false;
  bool _emailMonitoring = true;
  bool _autoReply = false;
  bool _requireApproval = true;

  int _totalJobs = 0;
  int _matchingJobs = 0;
  int _applications = 0;
  int _successfullyApplied = 0;
  int _emailsReceived = 0;

  @override
  void initState() {
    super.initState();
    _loadDashboard();
    _loadAgentStatus();
  }

  Future<void> _loadAgentStatus() async {
    try {
      final data = await ApiService.getAgentStatus(1);

      if (!mounted) return;

      setState(() {
        _agentRunning = data['running'] == true;
        _automaticJobDiscovery = data['automatic_job_discovery'] == true;
        _automaticApplication = data['automatic_application'] == true;
        _emailMonitoring = data['email_monitoring'] == true;
        _autoReply = data['auto_reply'] == true;
        _requireApproval = data['require_approval'] == true;
        _agentLoading = false;
        _agentError = null;
      });
    } catch (_) {
      if (!mounted) return;

      setState(() {
        _agentLoading = false;
        _agentError = 'Unable to load AI Agent status.';
      });
    }
  }

  Future<void> _runAgent() async {
    final messenger = ScaffoldMessenger.of(context);

    setState(() {
      _agentLoading = true;
      _agentError = null;
    });

    try {
      final data = await ApiService.runAgent(1);

      if (!mounted) return;

      setState(() {
        _agentRunning = data['running'] == true;
        _agentLoading = false;
      });

      messenger.showSnackBar(
        const SnackBar(
          content: Text('AI Agent started. Automation is now running.'),
        ),
      );
    } catch (error) {
      if (!mounted) return;

      setState(() {
        _agentLoading = false;
        _agentError = 'Unable to start AI Agent.';
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Unable to start AI Agent: $error')),
      );
    }
  }

  Future<void> _stopAgent() async {
    final messenger = ScaffoldMessenger.of(context);

    setState(() {
      _agentLoading = true;
      _agentError = null;
    });

    try {
      final data = await ApiService.stopAgent(1);

      if (!mounted) return;

      setState(() {
        _agentRunning = data['running'] == true;
        _agentLoading = false;
      });

      messenger.showSnackBar(
        const SnackBar(
          content: Text('AI Agent stopped. Automation is paused.'),
        ),
      );
    } catch (error) {
      if (!mounted) return;

      setState(() {
        _agentLoading = false;
        _agentError = 'Unable to stop AI Agent.';
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Unable to stop AI Agent: $error')),
      );
    }
  }

  Future<void> _openAgentPanel() async {
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      builder: (sheetContext) {
        return _AiAgentPanel(
          running: _agentRunning,
          loading: _agentLoading,
          error: _agentError,
          automaticJobDiscovery: _automaticJobDiscovery,
          automaticApplication: _automaticApplication,
          emailMonitoring: _emailMonitoring,
          autoReply: _autoReply,
          requireApproval: _requireApproval,
          onRun: () async {
            final navigator = Navigator.of(sheetContext);
            await _runAgent();
            if (mounted && navigator.mounted) {
              navigator.pop();
            }
          },
          onStop: () async {
            final navigator = Navigator.of(sheetContext);
            await _stopAgent();
            if (mounted && navigator.mounted) {
              navigator.pop();
            }
          },
        );
      },
    );

    if (mounted) {
      await _loadAgentStatus();
    }
  }

  Future<void> _loadDashboard() async {
    try {
      final data = await ApiService.getDashboard(1);

      if (!mounted) return;

      setState(() {
        _totalJobs = (data['total_jobs'] as num?)?.toInt() ?? 0;
        _matchingJobs = (data['matching_jobs'] as num?)?.toInt() ?? 0;
        _applications = (data['applications'] as num?)?.toInt() ?? 0;
        _successfullyApplied =
            (data['successfully_applied'] as num?)?.toInt() ?? 0;
        _emailsReceived = (data['emails_received'] as num?)?.toInt() ?? 0;
        _loading = false;
        _error = null;
      });
    } catch (error) {
      if (!mounted) return;

      setState(() {
        _loading = false;
        _error = 'Unable to load dashboard data.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'TrippieAutoAI',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        actions: [
          IconButton(
            onPressed: () {},
            icon: const Icon(Icons.notifications_none_rounded),
          ),
        ],
      ),
      body: SafeArea(
        child: _loading
            ? const Center(child: CircularProgressIndicator())
            : _error != null
            ? Center(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.cloud_off_rounded, size: 48),
                      const SizedBox(height: 16),
                      Text(_error!, textAlign: TextAlign.center),
                      const SizedBox(height: 16),
                      ElevatedButton.icon(
                        onPressed: () {
                          setState(() {
                            _loading = true;
                            _error = null;
                          });
                          _loadDashboard();
                        },
                        icon: const Icon(Icons.refresh_rounded),
                        label: const Text('Retry'),
                      ),
                    ],
                  ),
                ),
              )
            : ListView(
                padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
                children: [
                  Text(
                    'GOOD EVENING',
                    style: TextStyle(
                      fontSize: 12,
                      letterSpacing: 1.8,
                      fontWeight: FontWeight.bold,
                      color: Colors.deepPurpleAccent.withValues(alpha: 0.9),
                    ),
                  ),
                  const SizedBox(height: 6),
                  const Text(
                    'Your job search,\nworking for you.',
                    style: TextStyle(
                      fontSize: 30,
                      height: 1.12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 22),
                  GestureDetector(
                    onTap: _agentLoading ? null : _openAgentPanel,
                    child: Container(
                      padding: const EdgeInsets.all(18),
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(22),
                        gradient: const LinearGradient(
                          colors: [Color(0xFF1A1429), Color(0xFF111722)],
                        ),
                        border: Border.all(
                          color: _agentRunning
                              ? Colors.greenAccent.withValues(alpha: 0.25)
                              : const Color(0xFF352B52),
                        ),
                      ),
                      child: Row(
                        children: [
                          Container(
                            width: 52,
                            height: 52,
                            decoration: BoxDecoration(
                              color: Colors.deepPurple.withValues(alpha: 0.18),
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(
                              Icons.smart_toy_rounded,
                              color: Colors.deepPurpleAccent,
                              size: 28,
                            ),
                          ),
                          const SizedBox(width: 14),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  'AI Agent',
                                  style: TextStyle(
                                    fontSize: 17,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                                const SizedBox(height: 5),
                                Row(
                                  children: [
                                    Icon(
                                      Icons.circle,
                                      size: 8,
                                      color: _agentRunning
                                          ? Colors.greenAccent
                                          : Colors.grey,
                                    ),
                                    const SizedBox(width: 6),
                                    Text(
                                      _agentLoading
                                          ? 'CHECKING...'
                                          : _agentRunning
                                          ? 'RUNNING'
                                          : 'STOPPED',
                                      style: TextStyle(
                                        color: _agentRunning
                                            ? Colors.greenAccent
                                            : Colors.grey,
                                        fontSize: 12,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                          Icon(
                            Icons.chevron_right_rounded,
                            color: Colors.white.withValues(alpha: 0.4),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),
                  const Text(
                    'OVERVIEW',
                    style: TextStyle(
                      fontSize: 12,
                      letterSpacing: 1.5,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: _StatCard(
                          icon: Icons.work_outline_rounded,
                          label: 'Total Jobs',
                          value: _loading ? '—' : '$_totalJobs',
                        ),
                      ),
                      SizedBox(width: 10),
                      Expanded(
                        child: _StatCard(
                          icon: Icons.auto_awesome_rounded,
                          label: 'Matching',
                          value: _loading ? '—' : '$_matchingJobs',
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      Expanded(
                        child: _StatCard(
                          icon: Icons.send_outlined,
                          label: 'Applied',
                          value: _loading ? '—' : '$_applications',
                        ),
                      ),
                      SizedBox(width: 10),
                      Expanded(
                        child: _StatCard(
                          icon: Icons.check_circle_outline_rounded,
                          label: 'Successful',
                          value: _loading ? '—' : '$_successfullyApplied',
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  _StatCard(
                    icon: Icons.mail_outline_rounded,
                    label: 'Emails Received',
                    value: _loading ? '—' : '$_emailsReceived',
                  ),
                  const SizedBox(height: 28),
                  const Text(
                    'AI ACTIVITY',
                    style: TextStyle(
                      fontSize: 12,
                      letterSpacing: 1.5,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 12),
                  _ActivityItem(
                    icon: Icons.search_rounded,
                    title: 'Job discovery',
                    subtitle: 'Waiting for agent',
                  ),
                  _ActivityItem(
                    icon: Icons.psychology_outlined,
                    title: 'AI matching',
                    subtitle: 'No jobs analyzed yet',
                  ),
                  _ActivityItem(
                    icon: Icons.description_outlined,
                    title: 'Applications',
                    subtitle: 'No applications yet',
                  ),
                  _ActivityItem(
                    icon: Icons.mail_outline_rounded,
                    title: 'Email monitoring',
                    subtitle: 'Email account not connected',
                  ),
                ],
              ),
      ),
    );
  }
}

class JobsPage extends StatefulWidget {
  const JobsPage({super.key});

  @override
  State<JobsPage> createState() => _JobsPageState();
}

class _JobsPageState extends State<JobsPage> {
  bool _loading = true;
  String? _error;
  List<Map<String, dynamic>> _jobs = [];
  Map<int, String> _applicationStatuses = {};

  @override
  void initState() {
    super.initState();
    _loadJobs();
  }

  Future<void> _loadJobs() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final results = await Future.wait([
        ApiService.getJobs(),
        ApiService.getApplications(1),
      ]);

      if (!mounted) return;

      final jobsData = results[0];
      final applicationsData = results[1];

      final jobs = (jobsData['jobs'] as List<dynamic>? ?? [])
          .whereType<Map<String, dynamic>>()
          .toList();

      final applications =
          (applicationsData['applications'] as List<dynamic>? ?? [])
              .whereType<Map<String, dynamic>>()
              .toList();

      final applicationStatuses = <int, String>{};

      for (final application in applications) {
        final jobId = (application['job_id'] as num?)?.toInt();

        if (jobId != null) {
          applicationStatuses[jobId] =
              application['status']?.toString() ?? 'prepared';
        }
      }

      setState(() {
        _jobs = jobs;
        _applicationStatuses = applicationStatuses;
        _loading = false;
      });
    } catch (error) {
      if (!mounted) return;

      setState(() {
        _loading = false;
        _error = 'Unable to load jobs. Check your connection.';
      });
    }
  }

  String _formatDate(dynamic value) {
    if (value == null || value.toString().isEmpty) {
      return '';
    }

    final date = DateTime.tryParse(value.toString());

    if (date == null) {
      return '';
    }

    final now = DateTime.now();
    final difference = now.difference(date);

    if (difference.inDays == 0) {
      return 'Today';
    }

    if (difference.inDays == 1) {
      return 'Yesterday';
    }

    if (difference.inDays < 30) {
      return '${difference.inDays} days ago';
    }

    return '${date.day}/${date.month}/${date.year}';
  }

  Color _scoreColor(int score) {
    if (score >= 70) {
      return Colors.greenAccent;
    }

    if (score >= 50) {
      return Colors.orangeAccent;
    }

    return Colors.redAccent;
  }

  void _openJob(Map<String, dynamic> job) {
    Navigator.of(context)
        .push(MaterialPageRoute(builder: (_) => JobDetailsPage(job: job)));
  }

  String _formatApplicationStatus(String status) {
    const labels = {
      'prepared': 'Prepared',
      'submitted': 'Submitted',
      'under_review': 'Under Review',
      'interview': 'Interview',
      'assessment': 'Assessment',
      'offer': 'Offer',
      'accepted': 'Accepted',
      'rejected': 'Rejected',
      'withdrawn': 'Withdrawn',
      'follow_up_required': 'Follow-up Required',
      'manual_action_required': 'Manual Action Required',
      'submission_failed': 'Submission Failed',
    };

    return labels[status] ?? status.replaceAll('_', ' ');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Jobs',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        actions: [
          IconButton(
            tooltip: 'Refresh jobs',
            onPressed: _loading ? null : _loadJobs,
            icon: const Icon(Icons.refresh_rounded),
          ),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_loading && _jobs.isEmpty) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_error != null && _jobs.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(
                Icons.cloud_off_rounded,
                size: 56,
                color: Colors.white54,
              ),
              const SizedBox(height: 16),
              Text(
                _error!,
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.white70, fontSize: 16),
              ),
              const SizedBox(height: 20),
              FilledButton.icon(
                onPressed: _loadJobs,
                icon: const Icon(Icons.refresh_rounded),
                label: const Text('Retry'),
              ),
            ],
          ),
        ),
      );
    }

    if (_jobs.isEmpty) {
      return RefreshIndicator(
        onRefresh: _loadJobs,
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          children: const [
            SizedBox(height: 180),
            Icon(Icons.work_off_rounded, size: 60, color: Colors.white38),
            SizedBox(height: 16),
            Center(
              child: Text(
                'No jobs available yet.',
                style: TextStyle(color: Colors.white70, fontSize: 17),
              ),
            ),
            SizedBox(height: 8),
            Center(
              child: Text(
                'Pull down to refresh.',
                style: TextStyle(color: Colors.white38),
              ),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadJobs,
      child: ListView.builder(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
        itemCount: _jobs.length,
        itemBuilder: (context, index) {
          final job = _jobs[index];

          final title = job['title']?.toString() ?? 'Untitled Job';
          final company = job['company']?.toString() ?? 'Unknown Company';
          final location =
              job['location']?.toString() ?? 'Location not specified';
          final salary = job['salary']?.toString();
          final source = job['source']?.toString();
          final employmentType = job['employment_type']?.toString();
          final score = (job['match_score'] as num?)?.toInt() ?? 0;
          final date = _formatDate(job['discovered_at']);
          final jobId = (job['id'] as num?)?.toInt();
          final applicationStatus = jobId == null
              ? null
              : _applicationStatuses[jobId];

          return Padding(
            padding: const EdgeInsets.only(bottom: 14),
            child: Material(
              color: const Color(0xFF11151F),
              borderRadius: BorderRadius.circular(20),
              clipBehavior: Clip.antiAlias,
              child: InkWell(
                onTap: () => _openJob(job),
                child: Padding(
                  padding: const EdgeInsets.all(18),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Expanded(
                            child: Text(
                              title,
                              style: const TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 10,
                              vertical: 7,
                            ),
                            decoration: BoxDecoration(
                              color: _scoreColor(score).withValues(alpha: 0.12),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Text(
                              '$score%',
                              style: TextStyle(
                                color: _scoreColor(score),
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 10),
                      Text(
                        company,
                        style: const TextStyle(
                          color: Colors.white70,
                          fontSize: 15,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 12),
                      Wrap(
                        spacing: 14,
                        runSpacing: 8,
                        children: [
                          _JobMeta(
                            icon: Icons.location_on_outlined,
                            text: location,
                          ),
                          if (employmentType != null &&
                              employmentType.isNotEmpty)
                            _JobMeta(
                              icon: Icons.schedule_outlined,
                              text: employmentType,
                            ),
                        ],
                      ),
                      if (salary != null && salary.isNotEmpty) ...[
                        const SizedBox(height: 10),
                        _JobMeta(icon: Icons.payments_outlined, text: salary),
                      ],
                      if (source != null && source.isNotEmpty) ...[
                        const SizedBox(height: 10),
                        _JobMeta(icon: Icons.public_outlined, text: source),
                      ],
                      if (applicationStatus != null) ...[
                        const SizedBox(height: 12),
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 10,
                            vertical: 6,
                          ),
                          decoration: BoxDecoration(
                            color: Colors.blueAccent.withValues(alpha: 0.12),
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(
                              color: Colors.blueAccent.withValues(alpha: 0.25),
                            ),
                          ),
                          child: Text(
                            _formatApplicationStatus(applicationStatus),
                            style: const TextStyle(
                              color: Colors.blueAccent,
                              fontSize: 12,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ),
                      ],
                      const SizedBox(height: 14),
                      Row(
                        children: [
                          if (date.isNotEmpty)
                            Expanded(
                              child: Text(
                                date,
                                style: const TextStyle(
                                  color: Colors.white38,
                                  fontSize: 12,
                                ),
                              ),
                            ),
                          const Icon(
                            Icons.arrow_forward_ios_rounded,
                            size: 15,
                            color: Colors.white38,
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

class _JobMeta extends StatelessWidget {
  final IconData icon;
  final String text;

  const _JobMeta({required this.icon, required this.text});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 16, color: Colors.white54),
        const SizedBox(width: 5),
        Flexible(
          child: Text(
            text,
            style: const TextStyle(color: Colors.white60, fontSize: 13),
          ),
        ),
      ],
    );
  }
}

class JobDetailsPage extends StatefulWidget {
  final Map<String, dynamic> job;

  const JobDetailsPage({super.key, required this.job});

  @override
  State<JobDetailsPage> createState() => _JobDetailsPageState();
}

class _JobDetailsPageState extends State<JobDetailsPage> {
  String? _applicationStatus;
  bool _loadingApplication = true;

  @override
  void initState() {
    super.initState();
    _loadApplicationStatus();
  }

  Future<void> _loadApplicationStatus() async {
    final jobId = (widget.job['id'] as num?)?.toInt();

    if (jobId == null) {
      if (mounted) {
        setState(() {
          _loadingApplication = false;
        });
      }
      return;
    }

    try {
      final data = await ApiService.getApplications(1);

      if (!mounted) return;

      final applications = (data['applications'] as List<dynamic>? ?? [])
          .whereType<Map<String, dynamic>>()
          .toList();

      String? status;

      for (final application in applications) {
        final applicationJobId = (application['job_id'] as num?)?.toInt();

        if (applicationJobId == jobId) {
          status = application['status']?.toString() ?? 'prepared';
          break;
        }
      }

      setState(() {
        _applicationStatus = status;
        _loadingApplication = false;
      });
    } catch (_) {
      if (!mounted) return;

      setState(() {
        _loadingApplication = false;
      });
    }
  }

  String _formatApplicationStatus(String status) {
    const labels = {
      'prepared': 'Prepared',
      'submitted': 'Submitted',
      'under_review': 'Under Review',
      'interview': 'Interview',
      'assessment': 'Assessment',
      'offer': 'Offer',
      'accepted': 'Accepted',
      'rejected': 'Rejected',
      'withdrawn': 'Withdrawn',
      'follow_up_required': 'Follow-up Required',
      'manual_action_required': 'Manual Action Required',
      'submission_failed': 'Submission Failed',
    };

    return labels[status] ?? status.replaceAll('_', ' ');
  }

  Color _applicationStatusColor(String status) {
    switch (status) {
      case 'accepted':
      case 'offer':
        return Colors.greenAccent;
      case 'rejected':
      case 'submission_failed':
        return Colors.redAccent;
      case 'interview':
      case 'assessment':
      case 'under_review':
        return Colors.orangeAccent;
      default:
        return Colors.blueAccent;
    }
  }

  @override
  Widget build(BuildContext context) {
    final job = widget.job;

    final title = job['title']?.toString() ?? 'Untitled Job';
    final company = job['company']?.toString() ?? 'Unknown Company';
    final location = job['location']?.toString() ?? 'Location not specified';
    final description = job['description']?.toString() ?? '';
    final requirements = job['requirements']?.toString() ?? '';
    final salary = job['salary']?.toString() ?? '';
    final source = job['source']?.toString() ?? '';
    final employmentType = job['employment_type']?.toString() ?? '';
    final url = job['job_url']?.toString() ?? '';
    final score = (job['match_score'] as num?)?.toInt() ?? 0;

    return Scaffold(
      appBar: AppBar(title: const Text('Job Details')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
        children: [
          Text(
            title,
            style: const TextStyle(fontSize: 25, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 10),
          Text(
            company,
            style: const TextStyle(
              fontSize: 17,
              color: Colors.white70,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: [
              _DetailChip(icon: Icons.location_on_outlined, text: location),
              if (employmentType.isNotEmpty)
                _DetailChip(
                  icon: Icons.schedule_outlined,
                  text: employmentType,
                ),
              if (salary.isNotEmpty)
                _DetailChip(icon: Icons.payments_outlined, text: salary),
              _DetailChip(
                icon: Icons.auto_awesome_outlined,
                text: '$score% match',
              ),
            ],
          ),
          if (description.isNotEmpty) ...[
            const SizedBox(height: 28),
            const Text(
              'Description',
              style: TextStyle(fontSize: 19, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 10),
            Text(
              description,
              style: const TextStyle(
                color: Colors.white70,
                height: 1.55,
                fontSize: 14,
              ),
            ),
          ],
          if (requirements.isNotEmpty) ...[
            const SizedBox(height: 28),
            const Text(
              'Requirements',
              style: TextStyle(fontSize: 19, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 10),
            Text(
              requirements,
              style: const TextStyle(
                color: Colors.white70,
                height: 1.55,
                fontSize: 14,
              ),
            ),
          ],
          const SizedBox(height: 30),
          SizedBox(
            height: 52,
            child: _loadingApplication
                ? const Center(child: CircularProgressIndicator())
                : _applicationStatus != null
                ? Container(
                    alignment: Alignment.center,
                    decoration: BoxDecoration(
                      color: _applicationStatusColor(_applicationStatus!)
                          .withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(
                        color: _applicationStatusColor(_applicationStatus!)
                            .withValues(alpha: 0.3),
                      ),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          Icons.check_circle_outline_rounded,
                          color: _applicationStatusColor(_applicationStatus!),
                        ),
                        const SizedBox(width: 10),
                        Text(
                          _formatApplicationStatus(_applicationStatus!),
                          style: TextStyle(
                            color: _applicationStatusColor(_applicationStatus!),
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  )
                : _PrepareApplicationButton(
                    jobId: (job['id'] as num?)?.toInt() ?? 0,
                  ),
          ),
          if (url.isNotEmpty || source.isNotEmpty) ...[
            const SizedBox(height: 12),
            Center(
              child: Text(
                source.isNotEmpty
                    ? 'Source: $source'
                    : 'Application link available',
                style: const TextStyle(color: Colors.white38, fontSize: 12),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _PrepareApplicationButton extends StatefulWidget {
  final int jobId;

  const _PrepareApplicationButton({required this.jobId});

  @override
  State<_PrepareApplicationButton> createState() =>
      _PrepareApplicationButtonState();
}

class _PrepareApplicationButtonState extends State<_PrepareApplicationButton> {
  bool _loading = false;

  Future<void> _prepare() async {
    if (widget.jobId <= 0 || _loading) {
      return;
    }

    setState(() {
      _loading = true;
    });

    try {
      final result = await ApiService.prepareApplication(1, widget.jobId);

      if (!mounted) return;

      final status = result['status']?.toString() ?? 'prepared';

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            status == 'prepared'
                ? 'Application prepared successfully.'
                : 'Application status: $status',
          ),
          behavior: SnackBarBehavior.floating,
        ),
      );
    } catch (error) {
      if (!mounted) return;

      final message = error.toString().replaceFirst('Exception: ', '');

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(message), behavior: SnackBarBehavior.floating),
      );
    } finally {
      if (mounted) {
        setState(() {
          _loading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return FilledButton.icon(
      onPressed: _loading ? null : _prepare,
      icon: _loading
          ? const SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(strokeWidth: 2),
            )
          : const Icon(Icons.auto_awesome_rounded),
      label: Text(
        _loading ? 'Preparing...' : 'Prepare Application',
        style: const TextStyle(fontWeight: FontWeight.bold),
      ),
    );
  }
}

class _DetailChip extends StatelessWidget {
  final IconData icon;
  final String text;

  const _DetailChip({required this.icon, required this.text});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
      decoration: BoxDecoration(
        color: const Color(0xFF11151F),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF222938)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: Colors.white54),
          const SizedBox(width: 6),
          Text(
            text,
            style: const TextStyle(color: Colors.white70, fontSize: 13),
          ),
        ],
      ),
    );
  }
}

class ApplicationsPage extends StatefulWidget {
  const ApplicationsPage({super.key});

  @override
  State<ApplicationsPage> createState() => _ApplicationsPageState();
}

class _ApplicationsPageState extends State<ApplicationsPage> {
  bool _loading = true;
  String? _error;
  List<Map<String, dynamic>> _applications = [];
  int? _updatingApplicationId;

  static const List<String> _statuses = [
    'prepared',
    'submitted',
    'under_review',
    'interview',
    'assessment',
    'offer',
    'accepted',
    'rejected',
    'withdrawn',
    'follow_up_required',
    'manual_action_required',
    'submission_failed',
  ];

  @override
  void initState() {
    super.initState();
    _loadApplications();
  }

  Future<void> _loadApplications() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final data = await ApiService.getApplications(1);
      final rawApplications = data['applications'];

      final applications = rawApplications is List
          ? rawApplications
                .whereType<Map>()
                .map((item) => Map<String, dynamic>.from(item))
                .toList()
          : <Map<String, dynamic>>[];

      if (!mounted) return;

      setState(() {
        _applications = applications;
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;

      setState(() {
        _loading = false;
        _error = 'Unable to load applications.';
      });
    }
  }

  Future<void> _updateStatus(int applicationId, String status) async {
    if (_updatingApplicationId != null) {
      return;
    }

    setState(() {
      _updatingApplicationId = applicationId;
    });

    try {
      await ApiService.updateApplicationStatus(applicationId, status);

      await _loadApplications();

      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Application status updated to ${_formatStatus(status)}.',
          ),
          behavior: SnackBarBehavior.floating,
        ),
      );
    } catch (error) {
      if (!mounted) return;

      final message = error.toString().replaceFirst('Exception: ', '');

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(message), behavior: SnackBarBehavior.floating),
      );
    } finally {
      if (mounted) {
        setState(() {
          _updatingApplicationId = null;
        });
      }
    }
  }

  Future<void> _showStatusSelector(
    int applicationId,
    String currentStatus,
  ) async {
    if (_updatingApplicationId != null) {
      return;
    }

    final selectedStatus = await showModalBottomSheet<String>(
      context: context,
      showDragHandle: true,
      builder: (sheetContext) {
        return SafeArea(
          child: ListView(
            shrinkWrap: true,
            padding: const EdgeInsets.fromLTRB(16, 4, 16, 20),
            children: [
              const Padding(
                padding: EdgeInsets.fromLTRB(8, 0, 8, 12),
                child: Text(
                  'Update Application Status',
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                ),
              ),
              for (final status in _statuses)
                ListTile(
                  leading: Icon(
                    status == currentStatus
                        ? Icons.radio_button_checked_rounded
                        : Icons.radio_button_off_rounded,
                  ),
                  title: Text(_formatStatus(status)),
                  selected: status == currentStatus,
                  onTap: () {
                    Navigator.of(sheetContext).pop(status);
                  },
                ),
            ],
          ),
        );
      },
    );

    if (selectedStatus == null || selectedStatus == currentStatus) {
      return;
    }

    await _updateStatus(applicationId, selectedStatus);
  }

  String _formatStatus(String status) {
    const labels = {
      'prepared': 'Prepared',
      'submitted': 'Submitted',
      'under_review': 'Under Review',
      'interview': 'Interview',
      'assessment': 'Assessment',
      'offer': 'Offer',
      'accepted': 'Accepted',
      'rejected': 'Rejected',
      'withdrawn': 'Withdrawn',
      'follow_up_required': 'Follow-up Required',
      'manual_action_required': 'Manual Action Required',
      'submission_failed': 'Submission Failed',
    };

    return labels[status] ?? status.replaceAll('_', ' ');
  }

  Color _statusColor(String status) {
    switch (status) {
      case 'accepted':
      case 'offer':
        return Colors.green;
      case 'interview':
      case 'assessment':
        return Colors.blue;
      case 'under_review':
        return Colors.orange;
      case 'rejected':
      case 'submission_failed':
        return Colors.red;
      case 'withdrawn':
        return Colors.grey;
      case 'manual_action_required':
        return Colors.deepOrange;
      case 'follow_up_required':
        return Colors.teal;
      default:
        return Colors.deepPurple;
    }
  }

  String _formatDate(dynamic value) {
    if (value == null) return 'Not submitted';

    final date = DateTime.tryParse(value.toString());
    if (date == null) return 'Not submitted';

    final local = date.toLocal();

    return '${local.day.toString().padLeft(2, '0')}/'
        '${local.month.toString().padLeft(2, '0')}/'
        '${local.year}';
  }

  @override
  Widget build(BuildContext context) {
    if (_loading && _applications.isEmpty) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_error != null && _applications.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.cloud_off_rounded, size: 48),
              const SizedBox(height: 16),
              Text(_error!, textAlign: TextAlign.center),
              const SizedBox(height: 16),
              FilledButton.icon(
                onPressed: _loadApplications,
                icon: const Icon(Icons.refresh_rounded),
                label: const Text('Retry'),
              ),
            ],
          ),
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadApplications,
      child: _applications.isEmpty
          ? ListView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.all(24),
              children: const [
                SizedBox(height: 100),
                Icon(Icons.work_outline_rounded, size: 64),
                SizedBox(height: 20),
                Text(
                  'No applications yet',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                ),
                SizedBox(height: 8),
                Text(
                  'Prepared and submitted applications will appear here.',
                  textAlign: TextAlign.center,
                ),
              ],
            )
          : ListView.builder(
              padding: const EdgeInsets.fromLTRB(16, 20, 16, 100),
              itemCount: _applications.length,
              itemBuilder: (context, index) {
                final application = _applications[index];
                final job = application['job'] is Map
                    ? Map<String, dynamic>.from(application['job'])
                    : <String, dynamic>{};

                final applicationId = (application['id'] as num?)?.toInt();

                final title = job['title']?.toString() ?? 'Unknown position';
                final company = job['company']?.toString() ?? 'Unknown company';
                final location =
                    job['location']?.toString() ?? 'Location not specified';
                final status = application['status']?.toString() ?? 'prepared';
                final matchScore = (application['match_score'] as num?)
                    ?.toInt();

                final statusColor = _statusColor(status);
                final isUpdating =
                    applicationId != null &&
                    _updatingApplicationId == applicationId;

                return Card(
                  margin: const EdgeInsets.only(bottom: 14),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Expanded(
                              child: Text(
                                title,
                                style: const TextStyle(
                                  fontSize: 17,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                            if (matchScore != null)
                              Text(
                                '$matchScore%',
                                style: const TextStyle(
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Text(
                          company,
                          style: TextStyle(
                            color: Theme.of(context).textTheme.bodyLarge?.color,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Row(
                          children: [
                            const Icon(Icons.location_on_outlined, size: 16),
                            const SizedBox(width: 4),
                            Expanded(child: Text(location)),
                          ],
                        ),
                        const SizedBox(height: 14),
                        Row(
                          children: [
                            InkWell(
                              borderRadius: BorderRadius.circular(20),
                              onTap: applicationId == null || isUpdating
                                  ? null
                                  : () => _showStatusSelector(
                                      applicationId,
                                      status,
                                    ),
                              child: Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 10,
                                  vertical: 6,
                                ),
                                decoration: BoxDecoration(
                                  color: statusColor.withValues(alpha: 0.14),
                                  borderRadius: BorderRadius.circular(20),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    if (isUpdating)
                                      const SizedBox(
                                        width: 14,
                                        height: 14,
                                        child: CircularProgressIndicator(
                                          strokeWidth: 2,
                                        ),
                                      )
                                    else
                                      Icon(
                                        Icons.edit_outlined,
                                        size: 14,
                                        color: statusColor,
                                      ),
                                    const SizedBox(width: 6),
                                    Text(
                                      _formatStatus(status),
                                      style: TextStyle(
                                        color: statusColor,
                                        fontWeight: FontWeight.w600,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                            const Spacer(),
                            Text(
                              _formatDate(application['submitted_at']),
                              style: Theme.of(context).textTheme.bodySmall,
                            ),
                          ],
                        ),
                        const SizedBox(height: 10),
                        const Text(
                          'Tap status to update',
                          style: TextStyle(color: Colors.white38, fontSize: 11),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
    );
  }
}

class EmailPage extends StatefulWidget {
  const EmailPage({super.key});

  @override
  State<EmailPage> createState() => _EmailPageState();
}

class _EmailPageState extends State<EmailPage> {
  bool _loading = true;
  String? _error;
  List<Map<String, dynamic>> _emails = [];

  bool _pendingRepliesLoading = false;
  String? _pendingRepliesError;
  List<Map<String, dynamic>> _pendingReplies = [];

  String _selectedCategory = 'Primary';
  String _selectedFolder = 'Inbox';
  bool _folderMode = false;

  final List<String> _categories = const [
    'Primary',
    'Updates',
    'Promotions',
    'Forums',
    'Social',
  ];

  @override
  void initState() {
    super.initState();
    _loadEmails();
    _loadPendingReplies();
  }

  Future<void> _loadEmails() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final data = await ApiService.getEmails(1);
      final rawEmails = data['emails'];

      final emails = rawEmails is List
          ? rawEmails
                .whereType<Map>()
                .map((item) => Map<String, dynamic>.from(item))
                .toList()
          : <Map<String, dynamic>>[];

      if (!mounted) return;

      setState(() {
        _emails = emails;
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;

      setState(() {
        _loading = false;
        _error = 'Unable to load emails.';
      });
    }
  }

  Future<void> _loadPendingReplies() async {
    setState(() {
      _pendingRepliesLoading = true;
      _pendingRepliesError = null;
    });

    try {
      final data = await ApiService.getPendingReplies(1);
      final rawReplies = data['replies'];

      final replies = rawReplies is List
          ? rawReplies
                .whereType<Map>()
                .map((item) => Map<String, dynamic>.from(item))
                .toList()
          : <Map<String, dynamic>>[];

      if (!mounted) return;

      setState(() {
        _pendingReplies = replies;
        _pendingRepliesLoading = false;
      });
    } catch (_) {
      if (!mounted) return;

      setState(() {
        _pendingRepliesLoading = false;
        _pendingRepliesError = 'Unable to load pending AI replies.';
      });
    }
  }

  Future<void> _syncAndLoadEmails() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      await ApiService.syncGmail(1);
      await _loadEmails();
    } catch (error) {
      if (!mounted) return;

      setState(() {
        _loading = false;
        _error = 'Unable to sync Gmail.';
      });

      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Gmail sync failed: $error')));
    }
  }

  String _senderName(String? sender) {
    if (sender == null || sender.trim().isEmpty) {
      return 'Unknown sender';
    }

    final value = sender.trim();

    if (value.contains('<')) {
      return value.split('<').first.trim().replaceAll('"', '');
    }

    if (value.contains('@')) {
      return value.split('@').first;
    }

    return value;
  }

  String _senderEmail(String? sender) {
    if (sender == null || sender.trim().isEmpty) {
      return '';
    }

    final value = sender.trim();

    if (value.contains('<') && value.contains('>')) {
      return value.substring(value.indexOf('<') + 1, value.indexOf('>')).trim();
    }

    if (value.contains('@')) {
      return value;
    }

    return '';
  }

  String _initials(String name) {
    final parts = name
        .trim()
        .split(RegExp(r'\s+'))
        .where((part) => part.isNotEmpty)
        .toList();

    if (parts.isEmpty) return '?';

    if (parts.length == 1) {
      return parts.first
          .substring(0, parts.first.length >= 2 ? 2 : 1)
          .toUpperCase();
    }

    return '${parts.first[0]}${parts.last[0]}'.toUpperCase();
  }

  String _formatDate(dynamic value) {
    if (value == null) return '';

    final date = DateTime.tryParse(value.toString());

    if (date == null) return '';

    final local = date.toLocal();
    final now = DateTime.now();

    if (local.year == now.year &&
        local.month == now.month &&
        local.day == now.day) {
      final hour = local.hour == 0
          ? 12
          : local.hour > 12
          ? local.hour - 12
          : local.hour;

      final minute = local.minute.toString().padLeft(2, '0');
      final period = local.hour >= 12 ? 'PM' : 'AM';

      return '$hour:$minute $period';
    }

    if (local.year == now.year) {
      return '${local.day}/${local.month}';
    }

    return '${local.day}/${local.month}/${local.year}';
  }

  String _categoryForEmail(Map<String, dynamic> email) {
    final labels = (email['gmail_labels']?.toString() ?? '')
        .split(',')
        .map((label) => label.trim())
        .where((label) => label.isNotEmpty)
        .toSet();

    if (labels.contains('CATEGORY_UPDATES')) {
      return 'Updates';
    }

    if (labels.contains('CATEGORY_PROMOTIONS')) {
      return 'Promotions';
    }

    if (labels.contains('CATEGORY_FORUMS')) {
      return 'Forums';
    }

    if (labels.contains('CATEGORY_SOCIAL')) {
      return 'Social';
    }

    return 'Primary';
  }

  List<Map<String, dynamic>> get _visibleEmails {
    return _emails.where((email) {
      final labels = (email['gmail_labels']?.toString() ?? '')
          .split(',')
          .map((label) => label.trim())
          .where((label) => label.isNotEmpty)
          .toSet();

      // Category navigation:
      // Primary, Updates, Promotions, Forums, Social
      if (!_folderMode) {
        return _categoryForEmail(email) == _selectedCategory;
      }

      // Folder navigation:
      // Inbox, Starred, Important, Sent, Drafts,
      // All Mail, Spam, Trash
      switch (_selectedFolder) {
        case 'Inbox':
          return labels.contains('INBOX');

        case 'Starred':
          return labels.contains('STARRED');

        case 'Important':
          return labels.contains('IMPORTANT');

        case 'Sent':
          return labels.contains('SENT');

        case 'Drafts':
          return labels.contains('DRAFT');

        case 'All Mail':
          return !labels.contains('SPAM') && !labels.contains('TRASH');

        case 'Spam':
          return labels.contains('SPAM');

        case 'Trash':
          return labels.contains('TRASH');

        default:
          return false;
      }
    }).toList();
  }

  void _selectEmailFolder(String folder, BuildContext sheetContext) {
    setState(() {
      _selectedFolder = folder;
      _folderMode = true;
    });

    Navigator.pop(sheetContext);
  }

  void _openDrawer() {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (sheetContext) {
        return Align(
          alignment: Alignment.centerLeft,
          child: Container(
            width: MediaQuery.of(context).size.width * 0.82,
            height: MediaQuery.of(context).size.height,
            decoration: const BoxDecoration(
              color: Color(0xFF0D1119),
              borderRadius: BorderRadius.only(
                topRight: Radius.circular(24),
                bottomRight: Radius.circular(24),
              ),
            ),
            child: Material(
              color: const Color(0xFF0D1119),
              borderRadius: const BorderRadius.only(
                topRight: Radius.circular(24),
                bottomRight: Radius.circular(24),
              ),
              clipBehavior: Clip.antiAlias,
              child: SafeArea(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Padding(
                      padding: EdgeInsets.fromLTRB(24, 24, 24, 20),
                      child: Row(
                        children: [
                          Icon(Icons.auto_awesome_rounded, size: 30),
                          SizedBox(width: 12),
                          Text(
                            'TrippieAutoAI',
                            style: TextStyle(
                              fontSize: 21,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const Divider(height: 1),
                    _EmailDrawerItem(
                      icon: Icons.inbox_rounded,
                      title: 'Inbox',
                      selected: _selectedFolder == 'Inbox',
                      onTap: () => _selectEmailFolder('Inbox', sheetContext),
                    ),
                    _EmailDrawerItem(
                      icon: Icons.star_outline_rounded,
                      title: 'Starred',
                      selected: _selectedFolder == 'Starred',
                      onTap: () => _selectEmailFolder('Starred', sheetContext),
                    ),
                    _EmailDrawerItem(
                      icon: Icons.label_important_outline_rounded,
                      title: 'Important',
                      selected: _selectedFolder == 'Important',
                      onTap: () =>
                          _selectEmailFolder('Important', sheetContext),
                    ),
                    _EmailDrawerItem(
                      icon: Icons.send_outlined,
                      title: 'Sent',
                      selected: _selectedFolder == 'Sent',
                      onTap: () => _selectEmailFolder('Sent', sheetContext),
                    ),
                    _EmailDrawerItem(
                      icon: Icons.drafts_outlined,
                      title: 'Drafts',
                      selected: _selectedFolder == 'Drafts',
                      onTap: () => _selectEmailFolder('Drafts', sheetContext),
                    ),
                    _EmailDrawerItem(
                      icon: Icons.all_inbox_outlined,
                      title: 'All Mail',
                      selected: _selectedFolder == 'All Mail',
                      onTap: () => _selectEmailFolder('All Mail', sheetContext),
                    ),
                    _EmailDrawerItem(
                      icon: Icons.report_gmailerrorred_outlined,
                      title: 'Spam',
                      selected: _selectedFolder == 'Spam',
                      onTap: () => _selectEmailFolder('Spam', sheetContext),
                    ),
                    _EmailDrawerItem(
                      icon: Icons.delete_outline_rounded,
                      title: 'Trash',
                      selected: _selectedFolder == 'Trash',
                      onTap: () => _selectEmailFolder('Trash', sheetContext),
                    ),
                    const Padding(
                      padding: EdgeInsets.fromLTRB(24, 24, 24, 10),
                      child: Text(
                        'JOB APPLICATIONS',
                        style: TextStyle(
                          fontSize: 11,
                          letterSpacing: 1.4,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    _EmailDrawerItem(
                      icon: Icons.groups_outlined,
                      title: 'Interviews',
                      onTap: () {
                        Navigator.pop(sheetContext);
                      },
                    ),
                    _EmailDrawerItem(
                      icon: Icons.assignment_outlined,
                      title: 'Assessments',
                      onTap: () {
                        Navigator.pop(sheetContext);
                      },
                    ),
                    _EmailDrawerItem(
                      icon: Icons.local_offer_outlined,
                      title: 'Offers',
                      onTap: () {
                        Navigator.pop(sheetContext);
                      },
                    ),
                    _EmailDrawerItem(
                      icon: Icons.close_rounded,
                      title: 'Rejections',
                      onTap: () {
                        Navigator.pop(sheetContext);
                      },
                    ),
                    _EmailDrawerItem(
                      icon: Icons.schedule_rounded,
                      title: 'Follow-ups',
                      onTap: () {
                        Navigator.pop(sheetContext);
                      },
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  Future<Map<String, dynamic>?> _generateAiReply(
    Map<String, dynamic> email,
  ) async {
    final emailId = (email['id'] as num?)?.toInt();

    if (emailId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('This email does not have a valid ID.')),
      );
      return null;
    }

    try {
      final result = await ApiService.generateAiReply(1, emailId);

      await _loadPendingReplies();

      return result;
    } catch (error) {
      if (!mounted) return null;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Unable to generate AI reply: $error')),
      );

      return null;
    }
  }

  Future<bool> _updateReplyDraft(int replyId, String body) async {
    try {
      await ApiService.updateReplyDraft(1, replyId, body);

      await _loadPendingReplies();

      return true;
    } catch (error) {
      if (!mounted) return false;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Unable to save reply draft: $error')),
      );

      return false;
    }
  }

  Future<bool> _rejectReply(int replyId) async {
    try {
      await ApiService.rejectReply(1, replyId);

      await _loadPendingReplies();

      if (!mounted) return false;

      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('AI reply rejected.')));

      return true;
    } catch (error) {
      if (!mounted) return false;

      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Unable to reject reply: $error')));

      return false;
    }
  }

  Future<bool> _approveAndSendReply(int replyId) async {
    try {
      await ApiService.approveAndSendReply(1, replyId);

      await _loadPendingReplies();

      if (!mounted) return false;

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Reply approved and sent through Gmail.')),
      );

      return true;
    } catch (error) {
      if (!mounted) return false;

      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Unable to send reply: $error')));

      return false;
    }
  }

  Future<void> _openAiReplyPanel(Map<String, dynamic> email) async {
    Map<String, dynamic>? replyData;

    final emailId = (email['id'] as num?)?.toInt();

    if (emailId != null) {
      for (final pending in _pendingReplies) {
        final pendingEmailId = (pending['email_id'] as num?)?.toInt();

        if (pendingEmailId == emailId) {
          replyData = pending;
          break;
        }
      }
    }

    if (!mounted) return;

    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      builder: (sheetContext) {
        return _AiReplyPanel(
          email: email,
          initialReply: replyData,
          onGenerate: () => _generateAiReply(email),
          onSave: _updateReplyDraft,
          onReject: _rejectReply,
          onApprove: _approveAndSendReply,
        );
      },
    );

    if (mounted) {
      await _loadPendingReplies();
    }
  }

  void _openEmail(Map<String, dynamic> email) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      builder: (sheetContext) {
        final sender = email['sender']?.toString();
        final senderName = _senderName(sender);
        final senderEmail = _senderEmail(sender);

        return SafeArea(
          child: SizedBox(
            height: MediaQuery.of(context).size.height * 0.92,
            child: Column(
              children: [
                AppBar(
                  automaticallyImplyLeading: false,
                  leading: IconButton(
                    onPressed: () => Navigator.pop(sheetContext),
                    icon: const Icon(Icons.arrow_back_rounded),
                  ),
                  title: const Text('Email'),
                  actions: [
                    IconButton(
                      onPressed: () {},
                      icon: const Icon(Icons.archive_outlined),
                    ),
                    IconButton(
                      onPressed: () {},
                      icon: const Icon(Icons.delete_outline_rounded),
                    ),
                  ],
                ),
                Expanded(
                  child: ListView(
                    padding: const EdgeInsets.fromLTRB(20, 8, 20, 30),
                    children: [
                      Text(
                        email['subject']?.toString() ?? '(No subject)',
                        style: const TextStyle(
                          fontSize: 23,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 20),
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          CircleAvatar(
                            radius: 23,
                            child: Text(
                              _initials(senderName),
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  senderName,
                                  style: const TextStyle(
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                                if (senderEmail.isNotEmpty)
                                  Text(
                                    senderEmail,
                                    style: Theme.of(context)
                                        .textTheme
                                        .bodySmall,
                                  ),
                              ],
                            ),
                          ),
                          Text(
                            _formatDate(email['received_at']),
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                        ],
                      ),
                      const SizedBox(height: 24),
                      if (email['ai_summary'] != null &&
                          email['ai_summary'].toString().trim().isNotEmpty)
                        Card(
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Icon(Icons.auto_awesome_rounded),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      const Text(
                                        'AI Summary',
                                        style: TextStyle(
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ),
                                      const SizedBox(height: 6),
                                      Text(email['ai_summary'].toString()),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      const SizedBox(height: 20),
                      Text(
                        email['body']?.toString() ?? 'No message content.',
                        style: const TextStyle(fontSize: 16, height: 1.6),
                      ),
                    ],
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
                  child: Row(
                    children: [
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: () {
                            _openAiReplyPanel(email);
                          },
                          icon: const Icon(Icons.auto_awesome_rounded),
                          label: const Text('AI Reply'),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: () {},
                          icon: const Icon(Icons.forward_rounded),
                          label: const Text('Forward'),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final visibleEmails = _visibleEmails;

    return Scaffold(
      appBar: AppBar(
        automaticallyImplyLeading: false,
        titleSpacing: 8,
        leading: IconButton(
          onPressed: _openDrawer,
          icon: const Icon(Icons.menu_rounded),
        ),
        title: const Text(
          'Email',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        actions: [
          IconButton(
            onPressed: _syncAndLoadEmails,
            tooltip: 'Sync Gmail',
            icon: const Icon(Icons.refresh_rounded),
          ),
          if (_pendingRepliesLoading)
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 8),
              child: SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(strokeWidth: 2),
              ),
            )
          else if (_pendingReplies.isNotEmpty)
            IconButton(
              onPressed: () {
                final pending = _pendingReplies.first;
                final emailId = (pending['email_id'] as num?)?.toInt();

                if (emailId == null) return;

                Map<String, dynamic>? email;

                for (final item in _emails) {
                  final itemId = (item['id'] as num?)?.toInt();

                  if (itemId == emailId) {
                    email = item;
                    break;
                  }
                }

                if (email != null) {
                  _openAiReplyPanel(email);
                }
              },
              tooltip:
                  '${_pendingReplies.length} AI reply${_pendingReplies.length == 1 ? '' : 'ies'} pending',
              icon: Badge(
                label: Text(_pendingReplies.length.toString()),
                child: const Icon(Icons.auto_awesome_rounded),
              ),
            )
          else if (_pendingRepliesError != null)
            IconButton(
              onPressed: _loadPendingReplies,
              tooltip: 'Retry pending AI replies',
              icon: const Icon(Icons.cloud_off_rounded),
            ),
          IconButton(
            onPressed: () {},
            tooltip: 'Search',
            icon: const Icon(Icons.search_rounded),
          ),
          const Padding(
            padding: EdgeInsets.only(right: 12),
            child: CircleAvatar(
              radius: 17,
              child: Text(
                'DK',
                style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
              ),
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          SizedBox(
            height: 48,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12),
              itemCount: _categories.length,
              itemBuilder: (context, index) {
                final category = _categories[index];
                final selected = !_folderMode && category == _selectedCategory;

                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: ChoiceChip(
                    label: Text(category),
                    selected: selected,
                    onSelected: (_) {
                      setState(() {
                        _selectedCategory = category;
                        _folderMode = false;
                      });
                    },
                  ),
                );
              },
            ),
          ),
          const Divider(height: 1),
          Expanded(
            child: _loading && _emails.isEmpty
                ? const Center(child: CircularProgressIndicator())
                : _error != null && _emails.isEmpty
                ? Center(
                    child: Padding(
                      padding: const EdgeInsets.all(24),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(Icons.cloud_off_rounded, size: 48),
                          const SizedBox(height: 16),
                          Text(_error!, textAlign: TextAlign.center),
                          const SizedBox(height: 16),
                          FilledButton.icon(
                            onPressed: _loadEmails,
                            icon: const Icon(Icons.refresh_rounded),
                            label: const Text('Retry'),
                          ),
                        ],
                      ),
                    ),
                  )
                : RefreshIndicator(
                    onRefresh: _loadEmails,
                    child: visibleEmails.isEmpty
                        ? ListView(
                            physics: const AlwaysScrollableScrollPhysics(),
                            padding: const EdgeInsets.all(24),
                            children: [
                              const SizedBox(height: 100),
                              Icon(
                                Icons.mail_outline_rounded,
                                size: 64,
                                color: Theme.of(context).colorScheme.primary,
                              ),
                              const SizedBox(height: 20),
                              Text(
                                _selectedCategory == 'Primary'
                                    ? 'No emails'
                                    : 'No $_selectedCategory emails',
                                textAlign: TextAlign.center,
                                style: const TextStyle(
                                  fontSize: 20,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              const SizedBox(height: 8),
                              const Text(
                                'Your connected email messages will appear here.',
                                textAlign: TextAlign.center,
                              ),
                            ],
                          )
                        : ListView.builder(
                            padding: const EdgeInsets.only(top: 4, bottom: 100),
                            itemCount: visibleEmails.length,
                            itemBuilder: (context, index) {
                              final email = visibleEmails[index];

                              final sender = email['sender']?.toString();
                              final senderName = _senderName(sender);
                              final subject =
                                  email['subject']?.toString() ??
                                  '(No subject)';
                              final body = email['body']?.toString() ?? '';
                              final isRead = email['is_read'] == true;
                              final isStarred = email['is_starred'] == true;

                              return Material(
                                color: Colors.transparent,
                                child: InkWell(
                                  onTap: () => _openEmail(email),
                                  child: Padding(
                                    padding: const EdgeInsets.symmetric(
                                      horizontal: 16,
                                      vertical: 12,
                                    ),
                                    child: Row(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        CircleAvatar(
                                          radius: 21,
                                          child: Text(
                                            _initials(senderName),
                                            style: const TextStyle(
                                              fontSize: 12,
                                              fontWeight: FontWeight.bold,
                                            ),
                                          ),
                                        ),
                                        const SizedBox(width: 12),
                                        Expanded(
                                          child: Column(
                                            crossAxisAlignment:
                                                CrossAxisAlignment.start,
                                            children: [
                                              Row(
                                                children: [
                                                  Expanded(
                                                    child: Text(
                                                      senderName,
                                                      maxLines: 1,
                                                      overflow:
                                                          TextOverflow.ellipsis,
                                                      style: TextStyle(
                                                        fontWeight: isRead
                                                            ? FontWeight.normal
                                                            : FontWeight.bold,
                                                      ),
                                                    ),
                                                  ),
                                                  Text(
                                                    _formatDate(
                                                      email['received_at'],
                                                    ),
                                                    style: Theme.of(context)
                                                        .textTheme
                                                        .bodySmall
                                                        ?.copyWith(
                                                          fontWeight: isRead
                                                              ? FontWeight
                                                                    .normal
                                                              : FontWeight.bold,
                                                        ),
                                                  ),
                                                ],
                                              ),
                                              const SizedBox(height: 3),
                                              Row(
                                                children: [
                                                  Expanded(
                                                    child: Text(
                                                      subject,
                                                      maxLines: 1,
                                                      overflow:
                                                          TextOverflow.ellipsis,
                                                      style: TextStyle(
                                                        fontWeight: isRead
                                                            ? FontWeight.normal
                                                            : FontWeight.w600,
                                                      ),
                                                    ),
                                                  ),
                                                  IconButton(
                                                    visualDensity:
                                                        VisualDensity.compact,
                                                    onPressed: () {},
                                                    icon: Icon(
                                                      isStarred
                                                          ? Icons.star_rounded
                                                          : Icons
                                                                .star_border_rounded,
                                                      size: 20,
                                                    ),
                                                  ),
                                                ],
                                              ),
                                              Text(
                                                body
                                                    .replaceAll(
                                                      RegExp(r'\s+'),
                                                      ' ',
                                                    )
                                                    .trim(),
                                                maxLines: 1,
                                                overflow: TextOverflow.ellipsis,
                                                style: Theme.of(context)
                                                    .textTheme
                                                    .bodySmall,
                                              ),
                                            ],
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                ),
                              );
                            },
                          ),
                  ),
          ),
        ],
      ),
    );
  }
}

class _AiReplyPanel extends StatefulWidget {
  final Map<String, dynamic> email;
  final Map<String, dynamic>? initialReply;
  final Future<Map<String, dynamic>?> Function() onGenerate;
  final Future<bool> Function(int replyId, String body) onSave;
  final Future<bool> Function(int replyId) onReject;
  final Future<bool> Function(int replyId) onApprove;

  const _AiReplyPanel({
    required this.email,
    required this.initialReply,
    required this.onGenerate,
    required this.onSave,
    required this.onReject,
    required this.onApprove,
  });

  @override
  State<_AiReplyPanel> createState() => _AiReplyPanelState();
}

class _AiReplyPanelState extends State<_AiReplyPanel> {
  final TextEditingController _controller = TextEditingController();

  Map<String, dynamic>? _reply;
  bool _loading = false;
  bool _saving = false;
  bool _sending = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _reply = widget.initialReply;

    final initialBody = _reply?['reply']?.toString() ?? '';
    _controller.text = initialBody;
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  int? get _replyId {
    final value = _reply?['reply_id'];
    return value is num ? value.toInt() : null;
  }

  double? get _confidence {
    final value = _reply?['confidence'];

    if (value is num) {
      return value.toDouble();
    }

    return double.tryParse(value?.toString() ?? '');
  }

  Future<void> _generate() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final result = await widget.onGenerate();

      if (!mounted) return;

      if (result == null) {
        setState(() {
          _loading = false;
          _error = 'The AI could not generate a reply.';
        });
        return;
      }

      final status = result['status']?.toString();

      if (status == 'skipped') {
        setState(() {
          _loading = false;
          _error =
              result['reason']?.toString() ??
              'This email is not eligible for an AI reply.';
        });
        return;
      }

      if (status == 'already_pending') {
        _reply = {
          'reply_id': result['reply_id'],
          'email_id': result['email_id'],
          'reply': result['reply'],
          'confidence': result['confidence'],
          'reason': result['reason'],
        };
      } else {
        _reply = result;
      }

      _controller.text = _reply?['reply']?.toString() ?? '';

      setState(() {
        _loading = false;
      });
    } catch (error) {
      if (!mounted) return;

      setState(() {
        _loading = false;
        _error = 'Unable to generate reply: $error';
      });
    }
  }

  Future<void> _save() async {
    final replyId = _replyId;
    final body = _controller.text.trim();

    if (replyId == null) {
      setState(() {
        _error = 'Generate a reply before saving.';
      });
      return;
    }

    if (body.isEmpty) {
      setState(() {
        _error = 'Reply cannot be empty.';
      });
      return;
    }

    setState(() {
      _saving = true;
      _error = null;
    });

    final success = await widget.onSave(replyId, body);

    if (!mounted) return;

    setState(() {
      _saving = false;
    });

    if (success) {
      _reply = {...?_reply, 'reply': body};

      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('Reply draft saved.')));
    }
  }

  Future<void> _reject() async {
    final replyId = _replyId;

    if (replyId == null) return;

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: const Text('Reject AI reply?'),
          content: const Text(
            'This AI-generated reply will be discarded and will not be sent.',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, false),
              child: const Text('Cancel'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(dialogContext, true),
              child: const Text('Reject'),
            ),
          ],
        );
      },
    );

    if (confirmed != true || !mounted) return;

    setState(() {
      _saving = true;
      _error = null;
    });

    final success = await widget.onReject(replyId);

    if (!mounted) return;

    if (success) {
      Navigator.pop(context);
      return;
    }

    setState(() {
      _saving = false;
    });
  }

  Future<void> _approve() async {
    final replyId = _replyId;
    final body = _controller.text.trim();

    if (replyId == null) {
      setState(() {
        _error = 'Generate a reply before sending.';
      });
      return;
    }

    if (body.isEmpty) {
      setState(() {
        _error = 'Reply cannot be empty.';
      });
      return;
    }

    if (_saving || _sending) return;

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: const Text('Approve & Send?'),
          content: const Text(
            'This will send the current reply through your connected Gmail account.',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, false),
              child: const Text('Cancel'),
            ),
            FilledButton.icon(
              onPressed: () => Navigator.pop(dialogContext, true),
              icon: const Icon(Icons.send_rounded),
              label: const Text('Send'),
            ),
          ],
        );
      },
    );

    if (confirmed != true || !mounted) return;

    setState(() {
      _sending = true;
      _error = null;
    });

    final saved = await widget.onSave(replyId, body);

    if (!mounted) return;

    if (!saved) {
      setState(() {
        _sending = false;
      });
      return;
    }

    final success = await widget.onApprove(replyId);

    if (!mounted) return;

    if (success) {
      Navigator.pop(context);
      return;
    }

    setState(() {
      _sending = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final subject = widget.email['subject']?.toString() ?? '(No subject)';
    final sender = widget.email['sender']?.toString() ?? 'Unknown sender';

    final confidence = _confidence;
    final hasReply = _replyId != null;
    final busy = _loading || _saving || _sending;

    return SafeArea(
      child: SizedBox(
        height: MediaQuery.of(context).size.height * 0.88,
        child: Column(
          children: [
            AppBar(
              automaticallyImplyLeading: false,
              title: const Row(
                children: [
                  Icon(Icons.auto_awesome_rounded),
                  SizedBox(width: 10),
                  Text('AI Reply'),
                ],
              ),
              actions: [
                IconButton(
                  onPressed: busy ? null : () => Navigator.pop(context),
                  icon: const Icon(Icons.close_rounded),
                ),
              ],
            ),
            Expanded(
              child: ListView(
                padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
                children: [
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            subject,
                            style: const TextStyle(
                              fontSize: 17,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: 6),
                          Text(
                            sender,
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  if (!hasReply && !_loading)
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(20),
                        child: Column(
                          children: [
                            const Icon(Icons.auto_awesome_rounded, size: 42),
                            const SizedBox(height: 12),
                            const Text(
                              'Generate an AI reply',
                              style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const SizedBox(height: 8),
                            const Text(
                              'TrippieAutoAI will prepare a factual reply for your review. Nothing will be sent automatically from this panel.',
                              textAlign: TextAlign.center,
                            ),
                            const SizedBox(height: 18),
                            FilledButton.icon(
                              onPressed: _generate,
                              icon: const Icon(Icons.auto_awesome_rounded),
                              label: const Text('Generate AI Reply'),
                            ),
                          ],
                        ),
                      ),
                    ),
                  if (_loading)
                    const Padding(
                      padding: EdgeInsets.all(32),
                      child: Column(
                        children: [
                          CircularProgressIndicator(),
                          SizedBox(height: 16),
                          Text('Generating AI reply...'),
                        ],
                      ),
                    ),
                  if (_error != null)
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Icon(Icons.info_outline_rounded),
                            const SizedBox(width: 12),
                            Expanded(child: Text(_error!)),
                          ],
                        ),
                      ),
                    ),
                  if (hasReply && !_loading) ...[
                    Row(
                      children: [
                        const Icon(Icons.auto_awesome_rounded),
                        const SizedBox(width: 8),
                        const Expanded(
                          child: Text(
                            'AI-generated draft',
                            style: TextStyle(fontWeight: FontWeight.bold),
                          ),
                        ),
                        if (confidence != null)
                          Text(
                            '${(confidence * 100).round()}% confidence',
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    TextField(
                      controller: _controller,
                      enabled: !busy,
                      minLines: 8,
                      maxLines: 14,
                      textCapitalization: TextCapitalization.sentences,
                      decoration: const InputDecoration(
                        hintText: 'AI reply draft',
                        border: OutlineInputBorder(),
                        alignLabelWithHint: true,
                      ),
                    ),
                    const SizedBox(height: 12),
                    if (_reply?['reason'] != null)
                      Card(
                        child: Padding(
                          padding: const EdgeInsets.all(14),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Icon(
                                Icons.lightbulb_outline_rounded,
                                size: 20,
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: Text(
                                  _reply!['reason'].toString(),
                                  style: Theme.of(context).textTheme.bodySmall,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    const SizedBox(height: 14),
                    OutlinedButton.icon(
                      onPressed: busy ? null : _save,
                      icon: _saving
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.save_outlined),
                      label: const Text('Save Draft'),
                    ),
                    const SizedBox(height: 10),
                    Row(
                      children: [
                        Expanded(
                          child: OutlinedButton.icon(
                            onPressed: busy ? null : _reject,
                            icon: const Icon(Icons.close_rounded),
                            label: const Text('Reject'),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: FilledButton.icon(
                            onPressed: busy ? null : _approve,
                            icon: _sending
                                ? const SizedBox(
                                    width: 18,
                                    height: 18,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                    ),
                                  )
                                : const Icon(Icons.send_rounded),
                            label: Text(
                              _sending ? 'Sending...' : 'Approve & Send',
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _EmailDrawerItem extends StatelessWidget {
  final IconData icon;
  final String title;
  final bool selected;
  final VoidCallback onTap;

  const _EmailDrawerItem({
    required this.icon,
    required this.title,
    this.selected = false,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      selected: selected,
      leading: Icon(icon),
      title: Text(title),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      onTap: onTap,
    );
  }
}

class SettingsPage extends StatefulWidget {
  final void Function(ThemeMode) onThemeChanged;
  final ThemeMode currentTheme;

  const SettingsPage({
    super.key,
    required this.onThemeChanged,
    required this.currentTheme,
  });

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  bool _biometricsEnabled = false;
  bool _passwordEnabled = false;
  String _autoLock = 'Immediately';

  bool _settingsLoading = true;
  String? _settingsError;

  bool _agentEnabled = true;
  bool _automaticJobDiscovery = true;
  bool _automaticApplication = false;
  bool _emailMonitoring = true;
  bool _autoReply = false;
  bool _requireApproval = true;

  int _minimumMatchScore = 70;
  int _dailyApplicationLimit = 10;

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    try {
      final data = await ApiService.getSettings(1);

      if (!mounted) return;

      setState(() {
        _agentEnabled = data['agent_enabled'] == true;
        _automaticJobDiscovery =
            data['automatic_job_discovery'] == true;
        _automaticApplication =
            data['automatic_application'] == true;
        _emailMonitoring =
            data['email_monitoring'] == true;
        _autoReply =
            data['auto_reply'] == true;
        _requireApproval =
            data['require_approval'] == true;
        _minimumMatchScore =
            (data['minimum_match_score'] as num?)?.toInt() ?? 70;
        _dailyApplicationLimit =
            (data['daily_application_limit'] as num?)?.toInt() ?? 10;
        _settingsLoading = false;
        _settingsError = null;
      });
    } catch (error) {
      if (!mounted) return;

      setState(() {
        _settingsLoading = false;
        _settingsError = 'Unable to load AI settings.';
      });
    }
  }

  Future<void> _updateSetting(
    Map<String, dynamic> updates,
  ) async {
    try {
      final data = await ApiService.updateSettings(1, updates);

      if (!mounted) return;

      setState(() {
        _agentEnabled = data['agent_enabled'] == true;
        _automaticJobDiscovery =
            data['automatic_job_discovery'] == true;
        _automaticApplication =
            data['automatic_application'] == true;
        _emailMonitoring =
            data['email_monitoring'] == true;
        _autoReply =
            data['auto_reply'] == true;
        _requireApproval =
            data['require_approval'] == true;
        _minimumMatchScore =
            (data['minimum_match_score'] as num?)?.toInt() ?? 70;
        _dailyApplicationLimit =
            (data['daily_application_limit'] as num?)?.toInt() ?? 10;
        _settingsError = null;
      });
    } catch (error) {
      if (!mounted) return;

      setState(() {
        _settingsError = 'Unable to save setting.';
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Unable to save setting: $error'),
          behavior: SnackBarBehavior.floating,
        ),
      );

      await _loadSettings();
    }
  }

  void _showComingSoon(String title) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('$title will be configured here.'),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  void _changePin() {
    _showComingSoon('Change PIN');
  }

  void _lockNow() {
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(
        builder: (_) => LockScreen(
          onThemeChanged: widget.onThemeChanged,
          currentTheme: widget.currentTheme,
        ),
      ),
      (route) => false,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Settings',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
          children: [
            const Text(
              'SECURITY',
              style: TextStyle(
                fontSize: 12,
                letterSpacing: 1.6,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),

            _SettingsCard(
              children: [
                SwitchListTile.adaptive(
                  contentPadding: EdgeInsets.zero,
                  secondary: const Icon(Icons.fingerprint_rounded),
                  title: const Text(
                    'Enable Biometrics',
                    style: TextStyle(fontWeight: FontWeight.w600),
                  ),
                  subtitle: const Text(
                    'Use fingerprint or supported biometrics to unlock',
                  ),
                  value: _biometricsEnabled,
                  onChanged: (value) {
                    setState(() {
                      _biometricsEnabled = value;
                    });
                  },
                ),
                const Divider(height: 1),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.pin_rounded),
                  title: const Text(
                    'Change PIN',
                    style: TextStyle(fontWeight: FontWeight.w600),
                  ),
                  subtitle: const Text('Update your app unlock PIN'),
                  trailing: const Icon(Icons.chevron_right_rounded),
                  onTap: _changePin,
                ),
                const Divider(height: 1),
                SwitchListTile.adaptive(
                  contentPadding: EdgeInsets.zero,
                  secondary: const Icon(Icons.password_rounded),
                  title: const Text(
                    'Use Password',
                    style: TextStyle(fontWeight: FontWeight.w600),
                  ),
                  subtitle: const Text(
                    'Allow password authentication for the app',
                  ),
                  value: _passwordEnabled,
                  onChanged: (value) {
                    setState(() {
                      _passwordEnabled = value;
                    });
                    _showComingSoon(
                      value
                          ? 'Password authentication enabled'
                          : 'Password authentication disabled',
                    );
                  },
                ),
                const Divider(height: 1),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.timer_outlined),
                  title: const Text(
                    'Auto-lock',
                    style: TextStyle(fontWeight: FontWeight.w600),
                  ),
                  subtitle: Text('Lock after $_autoLock'),
                  trailing: const Icon(Icons.chevron_right_rounded),
                  onTap: _showAutoLockOptions,
                ),
                const Divider(height: 1),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.lock_rounded),
                  title: const Text(
                    'Lock Now',
                    style: TextStyle(fontWeight: FontWeight.w600),
                  ),
                  subtitle: const Text('Lock TrippieAutoAI immediately'),
                  trailing: const Icon(Icons.chevron_right_rounded),
                  onTap: _lockNow,
                ),
              ],
            ),

            const SizedBox(height: 28),
            const Text(
              'APPEARANCE',
              style: TextStyle(
                fontSize: 12,
                letterSpacing: 1.6,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),

            _SettingsCard(
              children: [
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: Icon(
                    widget.currentTheme == ThemeMode.dark
                        ? Icons.dark_mode_rounded
                        : Icons.light_mode_rounded,
                  ),
                  title: const Text(
                    'Theme',
                    style: TextStyle(fontWeight: FontWeight.w600),
                  ),
                  subtitle: Text(
                    widget.currentTheme == ThemeMode.dark
                        ? 'Dark mode'
                        : 'Light mode',
                  ),
                  trailing: const Icon(Icons.chevron_right_rounded),
                  onTap: _showThemeOptions,
                ),
              ],
            ),

            const SizedBox(height: 28),
            const Text(
              'AI AGENT',
              style: TextStyle(
                fontSize: 12,
                letterSpacing: 1.6,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),

            _SettingsCard(
              children: [
                if (_settingsError != null)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: Text(
                      _settingsError!,
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.error,
                      ),
                    ),
                  ),

                SwitchListTile.adaptive(
                  contentPadding: EdgeInsets.zero,
                  secondary: const Icon(Icons.smart_toy_rounded),
                  title: const Text(
                    'AI Agent',
                    style: TextStyle(fontWeight: FontWeight.w600),
                  ),
                  subtitle: Text(
                    _agentEnabled
                        ? 'Background automation is enabled'
                        : 'Background automation is disabled',
                  ),
                  value: _agentEnabled,
                  onChanged: _settingsLoading
                      ? null
                      : (value) {
                          setState(() {
                            _agentEnabled = value;
                          });
                          _updateSetting({
                            'agent_enabled': value,
                          });
                        },
                ),

                const Divider(height: 1),

                SwitchListTile.adaptive(
                  contentPadding: EdgeInsets.zero,
                  secondary: const Icon(Icons.search_rounded),
                  title: const Text(
                    'Automatic Job Discovery',
                    style: TextStyle(fontWeight: FontWeight.w600),
                  ),
                  subtitle: const Text(
                    'Discover new jobs automatically',
                  ),
                  value: _automaticJobDiscovery,
                  onChanged: _settingsLoading
                      ? null
                      : (value) {
                          setState(() {
                            _automaticJobDiscovery = value;
                          });
                          _updateSetting({
                            'automatic_job_discovery': value,
                          });
                        },
                ),

                const Divider(height: 1),

                SwitchListTile.adaptive(
                  contentPadding: EdgeInsets.zero,
                  secondary: const Icon(Icons.send_rounded),
                  title: const Text(
                    'Automatic Applications',
                    style: TextStyle(fontWeight: FontWeight.w600),
                  ),
                  subtitle: const Text(
                    'Allow the agent to prepare applications automatically',
                  ),
                  value: _automaticApplication,
                  onChanged: _settingsLoading
                      ? null
                      : (value) {
                          setState(() {
                            _automaticApplication = value;
                          });
                          _updateSetting({
                            'automatic_application': value,
                          });
                        },
                ),

                const Divider(height: 1),

                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.speed_rounded),
                  title: const Text(
                    'Minimum Match Score',
                    style: TextStyle(fontWeight: FontWeight.w600),
                  ),
                  subtitle: Text(
                    'Only process jobs scoring $_minimumMatchScore% or higher',
                  ),
                  trailing: Text(
                    '$_minimumMatchScore%',
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  onTap: _settingsLoading
                      ? null
                      : _showMatchScoreOptions,
                ),

                const Divider(height: 1),

                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.today_rounded),
                  title: const Text(
                    'Daily Application Limit',
                    style: TextStyle(fontWeight: FontWeight.w600),
                  ),
                  subtitle: const Text(
                    'Maximum applications the agent may prepare per day',
                  ),
                  trailing: Text(
                    '$_dailyApplicationLimit',
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  onTap: _settingsLoading
                      ? null
                      : _showDailyLimitOptions,
                ),
              ],
            ),

            const SizedBox(height: 28),
            const Text(
              'EMAIL & DATA',
              style: TextStyle(
                fontSize: 12,
                letterSpacing: 1.6,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),

            _SettingsCard(
              children: [
                SwitchListTile.adaptive(
                  contentPadding: EdgeInsets.zero,
                  secondary: const Icon(Icons.mail_outline_rounded),
                  title: const Text(
                    'Email Monitoring',
                    style: TextStyle(fontWeight: FontWeight.w600),
                  ),
                  subtitle: const Text(
                    'Monitor Gmail for incoming messages',
                  ),
                  value: _emailMonitoring,
                  onChanged: _settingsLoading
                      ? null
                      : (value) {
                          setState(() {
                            _emailMonitoring = value;
                          });
                          _updateSetting({
                            'email_monitoring': value,
                          });
                        },
                ),

                const Divider(height: 1),

                SwitchListTile.adaptive(
                  contentPadding: EdgeInsets.zero,
                  secondary: const Icon(Icons.auto_awesome_rounded),
                  title: const Text(
                    'AI Replies',
                    style: TextStyle(fontWeight: FontWeight.w600),
                  ),
                  subtitle: const Text(
                    'Allow AI to prepare replies to incoming emails',
                  ),
                  value: _autoReply,
                  onChanged: _settingsLoading
                      ? null
                      : (value) {
                          setState(() {
                            _autoReply = value;
                          });
                          _updateSetting({
                            'auto_reply': value,
                          });
                        },
                ),

                const Divider(height: 1),

                SwitchListTile.adaptive(
                  contentPadding: EdgeInsets.zero,
                  secondary: const Icon(Icons.verified_user_rounded),
                  title: const Text(
                    'Approval Required',
                    style: TextStyle(fontWeight: FontWeight.w600),
                  ),
                  subtitle: const Text(
                    'Require your approval before sensitive replies are sent',
                  ),
                  value: _requireApproval,
                  onChanged: _settingsLoading
                      ? null
                      : (value) {
                          setState(() {
                            _requireApproval = value;
                          });
                          _updateSetting({
                            'require_approval': value,
                          });
                        },
                ),

                const Divider(height: 1),

                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.folder_outlined),
                  title: const Text(
                    'Documents',
                    style: TextStyle(fontWeight: FontWeight.w600),
                  ),
                  subtitle: const Text(
                    'CV, certificates and application documents',
                  ),
                  trailing: const Icon(Icons.chevron_right_rounded),
                  onTap: () => _showComingSoon('Documents'),
                ),

                const Divider(height: 1),

                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.add_circle_outline_rounded),
                  title: const Text(
                    'Add More',
                    style: TextStyle(fontWeight: FontWeight.w600),
                  ),
                  subtitle: const Text(
                    'Add email accounts, job sources and AI skills',
                  ),
                  trailing: const Icon(Icons.chevron_right_rounded),
                  onTap: () => _showComingSoon('Add More'),
                ),
              ],
            ),

            const SizedBox(height: 28),
            Center(
              child: Text(
                'TrippieAutoAI',
                style: TextStyle(
                  color: Colors.white.withValues(alpha: 0.35),
                  fontSize: 12,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showMatchScoreOptions() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Theme.of(context).colorScheme.surface,
      builder: (sheetContext) {
        const options = [50, 60, 70, 80, 90];

        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Minimum Match Score',
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 12),
                ...options.map(
                  (score) => ListTile(
                    contentPadding: EdgeInsets.zero,
                    title: Text('$score% or higher'),
                    trailing: _minimumMatchScore == score
                        ? const Icon(Icons.check_rounded)
                        : null,
                    onTap: () {
                      Navigator.pop(sheetContext);
                      _updateSetting({
                        'minimum_match_score': score,
                      });
                    },
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  void _showDailyLimitOptions() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Theme.of(context).colorScheme.surface,
      builder: (sheetContext) {
        const options = [5, 10, 15, 20, 30];

        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Daily Application Limit',
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 12),
                ...options.map(
                  (limit) => ListTile(
                    contentPadding: EdgeInsets.zero,
                    title: Text('$limit applications'),
                    trailing: _dailyApplicationLimit == limit
                        ? const Icon(Icons.check_rounded)
                        : null,
                    onTap: () {
                      Navigator.pop(sheetContext);
                      _updateSetting({
                        'daily_application_limit': limit,
                      });
                    },
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  void _showThemeOptions() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Theme.of(context).colorScheme.surface,
      builder: (context) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Choose Theme',
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 12),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.dark_mode_rounded),
                  title: const Text('Dark'),
                  subtitle: const Text('Use the dark TrippieAutoAI interface'),
                  trailing: widget.currentTheme == ThemeMode.dark
                      ? const Icon(Icons.check_rounded)
                      : null,
                  onTap: () {
                    widget.onThemeChanged(ThemeMode.dark);
                    Navigator.pop(context);
                  },
                ),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.light_mode_rounded),
                  title: const Text('Light'),
                  subtitle: const Text('Use the light TrippieAutoAI interface'),
                  trailing: widget.currentTheme == ThemeMode.light
                      ? const Icon(Icons.check_rounded)
                      : null,
                  onTap: () {
                    widget.onThemeChanged(ThemeMode.light);
                    Navigator.pop(context);
                  },
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  void _showAutoLockOptions() {
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF11151F),
      builder: (context) {
        const options = [
          'Immediately',
          'After 1 minute',
          'After 5 minutes',
          'After 15 minutes',
        ];

        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Auto-lock',
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 12),
                ...options.map(
                  (option) => ListTile(
                    contentPadding: EdgeInsets.zero,
                    title: Text(option),
                    trailing: _autoLock == option
                        ? const Icon(Icons.check_rounded)
                        : null,
                    onTap: () {
                      setState(() {
                        _autoLock = option;
                      });
                      Navigator.pop(context);
                    },
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _SettingsCard extends StatelessWidget {
  final List<Widget> children;

  const _SettingsCard({required this.children});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: const Color(0xFF11151F),
      borderRadius: BorderRadius.circular(20),
      clipBehavior: Clip.antiAlias,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: const Color(0xFF222938)),
        ),
        child: Column(children: children),
      ),
    );
  }
}

class _StatCard extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _StatCard({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF11151F),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFF222938)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 21, color: Colors.deepPurpleAccent),
          const SizedBox(height: 12),
          Text(
            value,
            style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 3),
          Text(
            label,
            style: TextStyle(
              fontSize: 12,
              color: Colors.white.withValues(alpha: 0.55),
            ),
          ),
        ],
      ),
    );
  }
}

class _ActivityItem extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;

  const _ActivityItem({
    required this.icon,
    required this.title,
    required this.subtitle,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(15),
      decoration: BoxDecoration(
        color: const Color(0xFF0F131C),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF1E2532)),
      ),
      child: Row(
        children: [
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(
              color: Colors.deepPurple.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon, color: Colors.deepPurpleAccent, size: 21),
          ),
          const SizedBox(width: 13),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 3),
                Text(
                  subtitle,
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.white.withValues(alpha: 0.5),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
