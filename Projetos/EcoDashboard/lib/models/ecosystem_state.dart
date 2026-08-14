// Modelos de dados tipados do EcoSystemUmGrau
// Serialização JSON compatível com bridge/memory_engine

import 'package:flutter/foundation.dart';

/// Estado geral do ecossistema (snapshot único do bridge)
class EcosystemState {
  final MemoryState memory;
  final VigilanteState vigilante;
  final RadarState radar;
  final VoiceState voice;
  final List<AgentState> agents;
  final List<ProjectState> projects;
  final List<McpServerState> mcpServers;
  final List<LogEntry> recentLogs;
  final DateTime timestamp;

  const EcosystemState({
    required this.memory,
    required this.vigilante,
    required this.radar,
    required this.voice,
    required this.agents,
    required this.projects,
    required this.mcpServers,
    required this.recentLogs,
    required this.timestamp,
  });

  factory EcosystemState.fromJson(Map<String, dynamic> json) => EcosystemState(
    memory: MemoryState.fromJson(json['memory'] ?? {}),
    vigilante: VigilanteState.fromJson(json['vigilante'] ?? {}),
    radar: RadarState.fromJson(json['radar'] ?? {}),
    voice: VoiceState.fromJson(json['voice'] ?? {}),
    agents: (json['agents'] as List? ?? []).map((e) => AgentState.fromJson(e)).toList(),
    projects: (json['projects'] as List? ?? []).map((e) => ProjectState.fromJson(e)).toList(),
    mcpServers: (json['mcp_servers'] as List? ?? []).map((e) => McpServerState.fromJson(e)).toList(),
    recentLogs: (json['recent_logs'] as List? ?? []).map((e) => LogEntry.fromJson(e)).toList(),
    timestamp: DateTime.tryParse(json['timestamp'] ?? '') ?? DateTime.now(),
  );

  Map<String, dynamic> toJson() => {
    'memory': memory.toJson(),
    'vigilante': vigilante.toJson(),
    'radar': radar.toJson(),
    'voice': voice.toJson(),
    'agents': agents.map((e) => e.toJson()).toList(),
    'projects': projects.map((e) => e.toJson()).toList(),
    'mcp_servers': mcpServers.map((e) => e.toJson()).toList(),
    'recent_logs': recentLogs.map((e) => e.toJson()).toList(),
    'timestamp': timestamp.toIso8601String(),
  };
}

/// Memória episódica
class MemoryState {
  final int total;
  final int active;
  final Map<String, int> byKind;
  final Map<String, int> byConfidence;
  final Map<String, int> bySource;

  const MemoryState({
    required this.total,
    required this.active,
    required this.byKind,
    required this.byConfidence,
    required this.bySource,
  });

  factory MemoryState.fromJson(Map<String, dynamic> json) => MemoryState(
    total: json['total'] ?? 0,
    active: json['active'] ?? 0,
    byKind: Map<String, int>.from(json['by_kind'] ?? {}),
    byConfidence: Map<String, int>.from(json['by_confidence'] ?? {}),
    bySource: Map<String, int>.from(json['by_source'] ?? {}),
  );

  Map<String, dynamic> toJson() => {
    'total': total,
    'active': active,
    'by_kind': byKind,
    'by_confidence': byConfidence,
    'by_source': bySource,
  };

  double get confidenceHighPct => total > 0 ? (byConfidence['alta'] ?? 0) / total * 100 : 0;
  double get confidenceMedPct => total > 0 ? (byConfidence['media'] ?? 0) / total * 100 : 0;
  double get confidenceLowPct => total > 0 ? (byConfidence['baixa'] ?? 0) / total * 100 : 0;
}

/// Item de memória individual (para listas detalhadas)
class MemoryItem {
  final int id;
  final String kind;
  final String task;
  final String summary;
  final double confidence;
  final String sourceType;
  final List<String> tags;
  final DateTime createdAt;

  const MemoryItem({
    required this.id,
    required this.kind,
    required this.task,
    required this.summary,
    required this.confidence,
    required this.sourceType,
    required this.tags,
    required this.createdAt,
  });

  factory MemoryItem.fromJson(Map<String, dynamic> json) => MemoryItem(
    id: json['id'] ?? 0,
    kind: json['kind'] ?? '',
    task: json['task'] ?? '',
    summary: json['summary'] ?? '',
    confidence: (json['confidence'] ?? 1.0).toDouble(),
    sourceType: json['source_type'] ?? 'desconhecido',
    tags: List<String>.from(json['tags'] ?? []),
    createdAt: DateTime.tryParse(json['created_at'] ?? '') ?? DateTime.now(),
  );

  ConfidenceLevel get confidenceLevel {
    if (confidence >= 0.9) return ConfidenceLevel.high;
    if (confidence >= 0.7) return ConfidenceLevel.medium;
    return ConfidenceLevel.low;
  }
}

enum ConfidenceLevel { high, medium, low }

/// Vigilante — timers e status
class VigilanteState {
  final bool running;
  final int pid;
  final Map<String, TimerStatus> timers;
  final DateTime lastSync;

  const VigilanteState({
    required this.running,
    required this.pid,
    required this.timers,
    required this.lastSync,
  });

  factory VigilanteState.fromJson(Map<String, dynamic> json) => VigilanteState(
    running: json['running'] ?? false,
    pid: json['pid'] ?? 0,
    timers: (json['timers'] as Map? ?? {}).map(
      (k, v) => MapEntry(k.toString(), TimerStatus.fromJson(v)),
    ),
    lastSync: DateTime.tryParse(json['last_sync'] ?? '') ?? DateTime.now(),
  );

  Map<String, dynamic> toJson() => {
    'running': running,
    'pid': pid,
    'timers': timers.map((k, v) => MapEntry(k, v.toJson())),
    'last_sync': lastSync.toIso8601String(),
  };
}

class TimerStatus {
  final String name;
  final bool active;
  final String interval;
  final String lastRun;
  final String nextRun;
  final String status; // 'ok', 'warning', 'error', 'pending'

  const TimerStatus({
    required this.name,
    required this.active,
    required this.interval,
    required this.lastRun,
    required this.nextRun,
    required this.status,
  });

  factory TimerStatus.fromJson(Map<String, dynamic> json) => TimerStatus(
    name: json['name'] ?? '',
    active: json['active'] ?? false,
    interval: json['interval'] ?? '',
    lastRun: json['last_run'] ?? '',
    nextRun: json['next_run'] ?? '',
    status: json['status'] ?? 'pending',
  );

  Map<String, dynamic> toJson() => {
    'name': name,
    'active': active,
    'interval': interval,
    'last_run': lastRun,
    'next_run': nextRun,
    'status': status,
  };

  ColorStatus get colorStatus {
    switch (status) {
      case 'ok': return ColorStatus.success;
      case 'warning': return ColorStatus.warning;
      case 'error': return ColorStatus.error;
      default: return ColorStatus.info;
    }
  }
}

enum ColorStatus { success, warning, error, info }

/// Evolution Radar
class RadarState {
  final bool adminEnabled;
  final String phase; // 'idle', 'collect', 'filter', 'package', 'apply'
  final int proposalsFound;
  final int proposalsValidated;
  final int packagesReady;
  final String nextRun;
  final List<RadarProposal> recentProposals;

  const RadarState({
    required this.adminEnabled,
    required this.phase,
    required this.proposalsFound,
    required this.proposalsValidated,
    required this.packagesReady,
    required this.nextRun,
    required this.recentProposals,
  });

  factory RadarState.fromJson(Map<String, dynamic> json) => RadarState(
    adminEnabled: json['admin_enabled'] ?? false,
    phase: json['phase'] ?? 'idle',
    proposalsFound: json['proposals_found'] ?? 0,
    proposalsValidated: json['proposals_validated'] ?? 0,
    packagesReady: json['packages_ready'] ?? 0,
    nextRun: json['next_run'] ?? '',
    recentProposals: (json['recent_proposals'] as List? ?? [])
        .map((e) => RadarProposal.fromJson(e))
        .toList(),
  );

  Map<String, dynamic> toJson() => {
    'admin_enabled': adminEnabled,
    'phase': phase,
    'proposals_found': proposalsFound,
    'proposals_validated': proposalsValidated,
    'packages_ready': packagesReady,
    'next_run': nextRun,
    'recent_proposals': recentProposals.map((e) => e.toJson()).toList(),
  };
}

class RadarProposal {
  final String id;
  final String source;
  final String title;
  final String status; // 'raw', 'validated', 'packaged', 'applied', 'rejected'
  final double relevanceScore;
  final DateTime detectedAt;

  const RadarProposal({
    required this.id,
    required this.source,
    required this.title,
    required this.status,
    required this.relevanceScore,
    required this.detectedAt,
  });

  factory RadarProposal.fromJson(Map<String, dynamic> json) => RadarProposal(
    id: json['id'] ?? '',
    source: json['source'] ?? '',
    title: json['title'] ?? '',
    status: json['status'] ?? 'raw',
    relevanceScore: (json['relevance_score'] ?? 0).toDouble(),
    detectedAt: DateTime.tryParse(json['detected_at'] ?? '') ?? DateTime.now(),
  );

  Map<String, dynamic> toJson() => {
    'id': id,
    'source': source,
    'title': title,
    'status': status,
    'relevance_score': relevanceScore,
    'detected_at': detectedAt.toIso8601String(),
  };
}

/// Voz / Áudio
class VoiceState {
  final bool sttActive;
  final bool ttsPlaying;
  final bool vadActive;
  final double inputLevel; // 0.0 - 1.0
  final String currentText; // STT parcial
  final String lastSpoken;  // último TTS

  const VoiceState({
    required this.sttActive,
    required this.ttsPlaying,
    required this.vadActive,
    required this.inputLevel,
    required this.currentText,
    required this.lastSpoken,
  });

  factory VoiceState.fromJson(Map<String, dynamic> json) => VoiceState(
    sttActive: json['stt_active'] ?? false,
    ttsPlaying: json['tts_playing'] ?? false,
    vadActive: json['vad_active'] ?? false,
    inputLevel: (json['input_level'] ?? 0).toDouble(),
    currentText: json['current_text'] ?? '',
    lastSpoken: json['last_spoken'] ?? '',
  );

  Map<String, dynamic> toJson() => {
    'stt_active': sttActive,
    'tts_playing': ttsPlaying,
    'vad_active': vadActive,
    'input_level': inputLevel,
    'current_text': currentText,
    'last_spoken': lastSpoken,
  };
}

/// Agentes do ecossistema
class AgentState {
  final String id;
  final String name;
  final String icon; // emoji ou code
  final String role; // 'maestro', 'especialista', 'executor', 'revisor'
  final AgentStatus status; // 'idle', 'thinking', 'working', 'done', 'error'
  final String? currentTask;

  const AgentState({
    required this.id,
    required this.name,
    required this.icon,
    required this.role,
    required this.status,
    this.currentTask,
  });

  factory AgentState.fromJson(Map<String, dynamic> json) => AgentState(
    id: json['id'] ?? '',
    name: json['name'] ?? '',
    icon: json['icon'] ?? '🤖',
    role: json['role'] ?? 'executor',
    status: AgentStatus.values.firstWhere(
      (e) => e.name == json['status'],
      orElse: () => AgentStatus.idle,
    ),
    currentTask: json['current_task'],
  );

  Map<String, dynamic> toJson() => {
    'id': id,
    'name': name,
    'icon': icon,
    'role': role,
    'status': status.name,
    'current_task': currentTask,
  };
}

enum AgentStatus { idle, thinking, working, done, error }

/// Projetos Android
class ProjectState {
  final String name;
  final String path;
  final ProjectSyncStatus syncStatus;
  final int pendingFiles;
  final DateTime? lastSync;
  final String? remoteUrl;

  const ProjectState({
    required this.name,
    required this.path,
    required this.syncStatus,
    required this.pendingFiles,
    this.lastSync,
    this.remoteUrl,
  });

  factory ProjectState.fromJson(Map<String, dynamic> json) => ProjectState(
    name: json['name'] ?? '',
    path: json['path'] ?? '',
    syncStatus: ProjectSyncStatus.values.firstWhere(
      (e) => e.name == json['sync_status'],
      orElse: () => ProjectSyncStatus.unknown,
    ),
    pendingFiles: json['pending_files'] ?? 0,
    lastSync: json['last_sync'] != null ? DateTime.tryParse(json['last_sync']) : null,
    remoteUrl: json['remote_url'],
  );

  Map<String, dynamic> toJson() => {
    'name': name,
    'path': path,
    'sync_status': syncStatus.name,
    'pending_files': pendingFiles,
    'last_sync': lastSync?.toIso8601String(),
    'remote_url': remoteUrl,
  };
}

enum ProjectSyncStatus { synced, pending, warning, error, noRemote, unknown }

/// MCP Servers
class McpServerState {
  final String name;
  final String transport; // 'stdio', 'ws', 'sse'
  final McpServerStatus status;
  final int toolsCount;
  final String? error;

  const McpServerState({
    required this.name,
    required this.transport,
    required this.status,
    required this.toolsCount,
    this.error,
  });

  factory McpServerState.fromJson(Map<String, dynamic> json) => McpServerState(
    name: json['name'] ?? '',
    transport: json['transport'] ?? 'stdio',
    status: McpServerStatus.values.firstWhere(
      (e) => e.name == json['status'],
      orElse: () => McpServerStatus.unknown,
    ),
    toolsCount: json['tools_count'] ?? 0,
    error: json['error'],
  );

  Map<String, dynamic> toJson() => {
    'name': name,
    'transport': transport,
    'status': status.name,
    'tools_count': toolsCount,
    'error': error,
  };
}

enum McpServerStatus { online, offline, starting, error, unknown }

/// Log entry
class LogEntry {
  final DateTime timestamp;
  final String level; // 'info', 'warn', 'error', 'debug'
  final String source; // 'vigilante', 'radar', 'voice', 'sync', 'memory'
  final String message;

  const LogEntry({
    required this.timestamp,
    required this.level,
    required this.source,
    required this.message,
  });

  factory LogEntry.fromJson(Map<String, dynamic> json) => LogEntry(
    timestamp: DateTime.tryParse(json['timestamp'] ?? '') ?? DateTime.now(),
    level: json['level'] ?? 'info',
    source: json['source'] ?? 'unknown',
    message: json['message'] ?? '',
  );

  Map<String, dynamic> toJson() => {
    'timestamp': timestamp.toIso8601String(),
    'level': level,
    'source': source,
    'message': message,
  };

  Color get levelColor {
    switch (level) {
      case 'error': return const Color(0xFFF85149);
      case 'warn': return const Color(0xFFFFB300);
      case 'debug': return const Color(0xFF58A6FF);
      default: return const Color(0xFFF0F6FC);
    }
  }
}

/// Estado vazio/default para inicialização
extension EcosystemStateDefaults on EcosystemState {
  static EcosystemState empty() => EcosystemState(
    memory: const MemoryState(total: 0, active: 0, byKind: {}, byConfidence: {}, bySource: {}),
    vigilante: const VigilanteState(running: false, pid: 0, timers: {}, lastSync: DateTime.now()),
    radar: const RadarState(adminEnabled: false, phase: 'idle', proposalsFound: 0, proposalsValidated: 0, packagesReady: 0, nextRun: '', recentProposals: []),
    voice: const VoiceState(sttActive: false, ttsPlaying: false, vadActive: false, inputLevel: 0, currentText: '', lastSpoken: ''),
    agents: [],
    projects: [],
    mcpServers: [],
    recentLogs: [],
    timestamp: DateTime.now(),
  );
}