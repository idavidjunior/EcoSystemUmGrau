// EcoDashboard — Layout responsivo 3/2/1 colunas com NavigationRail
// Breakpoints: <900 (1 col), 900-1300 (2 col), >1300 (3 col)

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../widgets/eco_card.dart';
import '../widgets/status_dot.dart';
import '../widgets/memory_bar.dart';
import '../widgets/voice_waveform.dart';
import '../widgets/log_tail.dart';
import '../widgets/sync_spinner.dart';
import '../widgets/status_dot.dart' show RadarProgress;
import '../services/bridge_client.dart';
import '../models/ecosystem_state.dart';
import '../theme/eco_theme.dart';

class EcoDashboard extends StatefulWidget {
  const EcoDashboard({super.key});

  @override
  State<EcoDashboard> createState() => _EcoDashboardState();
}

class _EcoDashboardState extends State<EcoDashboard> {
  int _selectedNavIndex = 0;
  static const List<String> _navLabels = [
    'Dashboard',
    'Memória',
    'Agentes',
    'Radar',
    'Config',
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Row(
        children: [
          // NavigationRail (sempre visível no desktop)
          NavigationRail(
            selectedIndex: _selectedNavIndex,
            onDestinationSelected: (i) => setState(() => _selectedNavIndex = i),
            labelType: NavigationRailLabelType.all,
            extended: true,
            minExtendedWidth: 200,
            leading: Padding(
              padding: const EdgeInsets.symmetric(vertical: 16),
              child: Column(
                children: [
                  Icon(Icons.eco_outlined, color: EcoColors.primary, size: 32),
                  const SizedBox(height: 8),
                  Text(
                    'EcoSystemUmGrau',
                    style: Theme.of(context).textTheme.labelLarge?.copyWith(
                      color: EcoColors.primary,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ],
              ),
            ),
            trailing: Expanded(
              child: Align(
                alignment: Alignment.bottomCenter,
                child: Padding(
                  padding: const EdgeInsets.only(bottom: 16),
                  child: Consumer<BridgeClientProvider>(
                    builder: (context, provider, _) => StatusLabel(
                      status: provider.connectionStatus == ConnectionStatus.connected
                          ? ColorStatus.success
                          : ColorStatus.error,
                      label: provider.connectionStatus == ConnectionStatus.connected
                          ? 'Conectado'
                          : 'Desconectado',
                      dotSize: 8,
                      pulse: provider.connectionStatus == ConnectionStatus.connected,
                    ),
                  ),
                ),
              ),
            ),
            destinations: _navLabels.asMap().entries.map((e) {
              final icons = [
                Icons.dashboard_outlined,
                Icons.memory_outlined,
                Icons.psychology_outlined,
                Icons.radar_outlined,
                Icons.settings_outlined,
              ];
              return NavigationRailDestination(
                icon: Icon(icons[e.key], size: 22),
                selectedIcon: Icon(icons[e.key], size: 22, color: EcoColors.primary),
                label: Text(e.value),
              );
            }).toList(),
          ),

          // Vertical divider
          VerticalDivider(
            thickness: 1,
            width: 1,
            color: EcoColors.outline,
          ),

          // Main content
          Expanded(
            child: _buildContent(context),
          ),
        ],
      ),
    );
  }

  Widget _buildContent(BuildContext context) {
    switch (_selectedNavIndex) {
      case 0:
        return _DashboardView();
      case 1:
        return _MemoryView();
      case 2:
        return _AgentsView();
      case 3:
        return _RadarView();
      case 4:
        return _ConfigView();
      default:
        return _DashboardView();
    }
  }
}

// ============================================================================
// DASHBOARD VIEW — 3/2/1 colunas
// ============================================================================

class _DashboardView extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Consumer<BridgeClientProvider>(
      builder: (context, provider, _) {
        final state = provider.currentState ?? EcosystemState.empty();
        return LayoutBuilder(
          builder: (context, constraints) {
            final isWide = constraints.maxWidth > 1300;
            final isMedium = constraints.maxWidth > 900;

            return SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Header row
                  _buildHeader(context, state),
                  const SizedBox(height: 16),

                  // Row 1: Memória + Vigilante (ou 3 colunas se wide)
                  if (isWide)
                    _buildThreeColumns(context, state)
                  else if (isMedium)
                    _buildTwoColumns(context, state)
                  else
                    _buildSingleColumn(context, state),

                  const SizedBox(height: 16),

                  // Row 2: Voice + Logs (sempre 2 colunas se medium, 1 se narrow)
                  if (isMedium)
                    _buildBottomRow(context, state)
                  else
                    _buildBottomSingle(context, state),
                ],
              ),
            );
          },
        );
      },
    );
  }

  Widget _buildHeader(BuildContext context, EcosystemState state) {
    final theme = Theme.of(context);
    return Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Dashboard', style: theme.textTheme.headlineSmall),
              Text(
                'EcoSystemUmGrau — Estado vivo do ecossistema',
                style: theme.textTheme.bodyMedium?.copyWith(color: EcoColors.onSurfaceVariant),
              ),
            ],
          ),
        ),
        _ConnectionStatusBadge(state: state),
        const SizedBox(width: 12),
        _LastSyncBadge(state: state),
      ],
    );
  }

  Widget _buildThreeColumns(BuildContext context, EcosystemState state) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(flex: 2, child: _MemoryColumn(state: state)),
        const SizedBox(width: 16),
        Expanded(flex: 2, child: _VigilanteColumn(state: state)),
        const SizedBox(width: 16),
        Expanded(flex: 1, child: _RadarColumn(state: state)),
      ],
    );
  }

  Widget _buildTwoColumns(BuildContext context, EcosystemState state) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(flex: 3, child: _MemoryColumn(state: state)),
        const SizedBox(width: 16),
        Expanded(flex: 2, child: Column(
          children: [
            _VigilanteColumn(state: state),
            const SizedBox(height: 16),
            _RadarColumn(state: state),
          ],
        )),
      ],
    );
  }

  Widget _buildSingleColumn(BuildContext context, EcosystemState state) {
    return Column(
      children: [
        _MemoryColumn(state: state),
        const SizedBox(height: 16),
        _VigilanteColumn(state: state),
        const SizedBox(height: 16),
        _RadarColumn(state: state),
      ],
    );
  }

  Widget _buildBottomRow(BuildContext context, EcosystemState state) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(flex: 2, child: _VoiceColumn(state: state)),
        const SizedBox(width: 16),
        Expanded(flex: 3, child: _LogsColumn(state: state)),
      ],
    );
  }

  Widget _buildBottomSingle(BuildContext context, EcosystemState state) {
    return Column(
      children: [
        _VoiceColumn(state: state),
        const SizedBox(height: 16),
        _LogsColumn(state: state),
      ],
    );
  }
}

// ============================================================================
// COLUMN WIDGETS
// ============================================================================

class _MemoryColumn extends StatelessWidget {
  final EcosystemState state;
  const _MemoryColumn({required this.state});

  @override
  Widget build(BuildContext context) {
    return EcoCardHeader(
      title: 'Memória Episódica',
      subtitle: '${state.memory.total} total • ${state.memory.active} ativos',
      leading: const Icon(Icons.memory_outlined, color: EcoColors.primary),
      child: Column(
        children: [
          // Confidence bars
          _ConfidenceBars(memory: state.memory),
          const SizedBox(height: 16),
          // By kind
          _KindBreakdown(byKind: state.memory.byKind),
          const SizedBox(height: 16),
          // By source
          _SourceBreakdown(bySource: state.memory.bySource),
        ],
      ),
    );
  }
}

class _ConfidenceBars extends StatelessWidget {
  final MemoryState memory;
  const _ConfidenceBars({required this.memory});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text('Confiança', style: theme.textTheme.labelMedium?.copyWith(color: EcoColors.onSurfaceVariant)),
            Text(
              '${memory.confidenceHighPct.toStringAsFixed(0)}% • ${memory.confidenceMedPct.toStringAsFixed(0)}% • ${memory.confidenceLowPct.toStringAsFixed(0)}%',
              style: theme.textTheme.labelSmall?.copyWith(color: EcoColors.onSurfaceVariant),
            ),
          ],
        ),
        const SizedBox(height: 8),
        MemoryBarSegmented(
          factPct: memory.byConfidence['alta']?.toDouble() ?? 0,
          probablePct: memory.byConfidence['media']?.toDouble() ?? 0,
          hypothesisPct: memory.byConfidence['baixa']?.toDouble() ?? 0,
          height: 12,
        ),
        const SizedBox(height: 4),
        const ConfidenceLegend(),
      ],
    );
  }
}

class _KindBreakdown extends StatelessWidget {
  final Map<String, int> byKind;
  const _KindBreakdown({required this.byKind});

  static const Map<String, IconData> _icons = {
    'decisao': Icons.gavel_outlined,
    'padrao': Icons.pattern_outlined,
    'erro': Icons.bug_report_outlined,
    'episodio': Icons.event_outlined,
  };

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final total = byKind.values.fold(0, (a, b) => a + b);
    if (total == 0) return const SizedBox();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Por tipo', style: theme.textTheme.labelMedium?.copyWith(color: EcoColors.onSurfaceVariant)),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: byKind.entries.map((e) {
            final pct = total > 0 ? e.value / total * 100 : 0.0;
            return Chip(
              avatar: Icon(_icons[e.key] ?? Icons.help_outline, size: 16, color: EcoColors.primary),
              label: Text('${e.key}: ${e.value} (${pct.toStringAsFixed(0)}%)'),
              labelStyle: theme.textTheme.labelSmall,
              backgroundColor: EcoColors.surfaceVariant,
              side: BorderSide(color: EcoColors.outline),
            );
          }).toList(),
        ),
      ],
    );
  }
}

class _SourceBreakdown extends StatelessWidget {
  final Map<String, int> bySource;
  const _SourceBreakdown({required this.bySource});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final total = bySource.values.fold(0, (a, b) => a + b);
    if (total == 0) return const SizedBox();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Por fonte', style: theme.textTheme.labelMedium?.copyWith(color: EcoColors.onSurfaceVariant)),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: bySource.entries.map((e) {
            final pct = total > 0 ? e.value / total * 100 : 0.0;
            return Chip(
              label: Text('${e.key}: ${e.value} (${pct.toStringAsFixed(0)}%)'),
              labelStyle: theme.textTheme.labelSmall,
              backgroundColor: EcoColors.surfaceVariant,
              side: BorderSide(color: EcoColors.outline),
            );
          }).toList(),
        ),
      ],
    );
  }
}

class _VigilanteColumn extends StatelessWidget {
  final EcosystemState state;
  const _VigilanteColumn({required this.state});

  @override
  Widget build(BuildContext context) {
    return EcoCardHeader(
      title: 'Vigilante',
      subtitle: state.vigilante.running ? 'PID ${state.vigilante.pid} • Ativo' : 'Parado',
      leading: Icon(
        Icons.shield_outlined,
        color: state.vigilante.running ? EcoColors.success : EcoColors.error,
      ),
      trailing: StatusLabel(
        status: state.vigilante.running ? ColorStatus.success : ColorStatus.error,
        label: state.vigilante.running ? 'Online' : 'Offline',
        pulse: state.vigilante.running,
      ),
      child: Column(
        children: [
          // Timers grid
          ...state.vigilante.timers.entries.map((e) => _TimerTile(
            name: e.key,
            status: e.value,
          )).toList(),
        ],
      ),
    );
  }
}

class _TimerTile extends StatelessWidget {
  final String name;
  final TimerStatus status;
  const _TimerTile({required this.name, required this.status});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          StatusDot(status: status.colorStatus, size: 8, pulse: status.active),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(name, style: theme.textTheme.labelMedium),
                Text(
                  '${status.interval} • Próximo: ${status.nextRun}',
                  style: theme.textTheme.labelSmall?.copyWith(color: EcoColors.onSurfaceVariant),
                ),
              ],
            ),
          ),
          Text(
            status.lastRun,
            style: theme.textTheme.labelSmall?.copyWith(
              color: EcoColors.onSurfaceDisabled,
              fontFamily: 'JetBrainsMono',
            ),
          ),
        ],
      );
    }
  }
}

class _RadarColumn extends StatelessWidget {
  final EcosystemState state;
  const _RadarColumn({required this.state});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return EcoCardHeader(
      title: 'Evolution Radar',
      subtitle: state.radar.adminEnabled ? 'Admin OK' : 'Sem permissão admin',
      leading: Icon(Icons.radar_outlined, color: state.radar.adminEnabled ? EcoColors.primary : EcoColors.onSurfaceVariant),
      trailing: StatusLabel(
        status: state.radar.adminEnabled ? ColorStatus.success : ColorStatus.warning,
        label: state.radar.adminEnabled ? 'Ativo' : 'Bloqueado',
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          RadarProgress(
            phase: state.radar.phase,
            currentItem: state.radar.recentProposals.isNotEmpty
                ? state.radar.recentProposals.first.title
                : null,
            size: 100,
            showDetails: true,
          ),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _StatChip(label: 'Encontrados', value: '${state.radar.proposalsFound}', icon: Icons.search_outlined),
              _StatChip(label: 'Validados', value: '${state.radar.proposalsValidated}', icon: Icons.verified_outlined),
              _StatChip(label: 'Pacotes', value: '${state.radar.packagesReady}', icon: Icons.inventory_2_outlined),
            ],
          ),
        ],
      ),
    );
  }
}

class _StatChip extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  const _StatChip({required this.label, required this.value, required this.icon});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      children: [
        Icon(icon, color: EcoColors.primary, size: 20),
        const SizedBox(height: 4),
        Text(value, style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700, color: EcoColors.primary)),
        Text(label, style: theme.textTheme.labelSmall?.copyWith(color: EcoColors.onSurfaceVariant)),
      ],
    );
  }
}

class _VoiceColumn extends StatelessWidget {
  final EcosystemState state;
  const _VoiceColumn({required this.state});

  @override
  Widget build(BuildContext context) {
    return EcoCardHeader(
      title: 'Voz / Áudio',
      subtitle: state.voice.vadActive ? 'VAD ativo' : 'Em espera',
      leading: Icon(Icons.mic_outlined, color: state.voice.sttActive || state.voice.ttsPlaying ? EcoColors.primary : EcoColors.onSurfaceVariant),
      child: VoiceWaveform(voiceState: state.voice, height: 80),
    );
  }
}

class _LogsColumn extends StatelessWidget {
  final EcosystemState state;
  const _LogsColumn({required this.state});

  @override
  Widget build(BuildContext context) {
    return EcoCardHeader(
      title: 'Logs Recentes',
      subtitle: '${state.recentLogs.length} entradas',
      leading: const Icon(Icons.terminal_outlined, color: EcoColors.primary),
      trailing: PopupMenuButton<String>(
        icon: const Icon(Icons.filter_list, color: EcoColors.onSurfaceVariant),
        itemBuilder: (context) => [
          const PopupMenuItem(value: 'all', child: Text('Todos')),
          const PopupMenuItem(value: 'vigilante', child: Text('Vigilante')),
          const PopupMenuItem(value: 'radar', child: Text('Radar')),
          const PopupMenuItem(value: 'voice', child: Text('Voz')),
          const PopupMenuItem(value: 'sync', child: Text('Sync')),
          const PopupMenuItem(value: 'memory', child: Text('Memória')),
        ],
        onSelected: (val) {}, // TODO: implement filter
      ),
      child: LogTail(
        logs: state.recentLogs,
        maxLines: 100,
        autoScroll: true,
        showTimestamps: true,
        showSource: true,
        monospace: true,
      ),
    );
  }
}

// ============================================================================
// HEADER WIDGETS
// ============================================================================

class _ConnectionStatusBadge extends StatelessWidget {
  final EcosystemState state;
  const _ConnectionStatusBadge({required this.state});

  @override
  Widget build(BuildContext context) {
    // Determine overall connection from various states
    final connected = state.vigilante.running &&
        state.mcpServers.every((s) => s.status == McpServerStatus.online);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: connected ? EcoColors.success.withValues(alpha: 0.15) : EcoColors.error.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: connected ? EcoColors.success : EcoColors.error),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          StatusDot(
            status: connected ? ColorStatus.success : ColorStatus.error,
            size: 8,
            pulse: connected,
          ),
          const SizedBox(width: 6),
          Text(
            connected ? '● Conectado' : '● Desconectado',
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
              color: connected ? EcoColors.success : EcoColors.error,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}

class _LastSyncBadge extends StatelessWidget {
  final EcosystemState state;
  const _LastSyncBadge({required this.state});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: EcoColors.surfaceVariant,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: EcoColors.outline),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.sync_outlined, size: 14, color: EcoColors.onSurfaceVariant),
          const SizedBox(width: 6),
          Text(
            'Sync: ${_formatDuration(state.timestamp)}',
            style: theme.textTheme.labelSmall?.copyWith(
              color: EcoColors.onSurfaceVariant,
              fontFamily: 'JetBrainsMono',
            ),
          ),
        ],
      ),
    );
  }

  String _formatDuration(DateTime dt) {
    final diff = DateTime.now().difference(dt);
    if (diff.inSeconds < 60) return '${diff.inSeconds}s';
    if (diff.inMinutes < 60) return '${diff.inMinutes}m';
    if (diff.inHours < 24) return '${diff.inHours}h';
    return '${diff.inDays}d';
  }
}

// ============================================================================
// OTHER VIEWS (Placeholder)
// ============================================================================

class _MemoryView extends StatelessWidget {
  @override
  Widget build(BuildContext context) => const Center(child: Text('Memória - Em desenvolvimento'));
}

class _AgentsView extends StatelessWidget {
  @override
  Widget build(BuildContext context) => const Center(child: Text('Agentes - Em desenvolvimento'));
}

class _RadarView extends StatelessWidget {
  @override
  Widget build(BuildContext context) => const Center(child: Text('Radar - Em desenvolvimento'));
}

class _ConfigView extends StatelessWidget {
  @override
  Widget build(BuildContext context) => const Center(child: Text('Configuração - Em desenvolvimento'));
}