// LogTail — Tail -f visual com auto-scroll, cores por nível, filtros
import 'dart:async';
import 'package:flutter/material.dart';
import '../../models/ecosystem_state.dart';
import '../../theme/eco_theme.dart';

class LogTail extends StatefulWidget {
  final List<LogEntry> logs;
  final int maxLines;
  final bool autoScroll;
  final Set<String>? filterSources;
  final Set<String>? filterLevels;
  final bool showTimestamps;
  final bool showSource;
  final bool monospace;
  final VoidCallback? onClear;
  final ValueChanged<LogEntry>? onTap;

  const LogTail({
    super.key,
    required this.logs,
    this.maxLines = 500,
    this.autoScroll = true,
    this.filterSources,
    this.filterLevels,
    this.showTimestamps = true,
    this.showSource = true,
    this.monospace = true,
    this.onClear,
    this.onTap,
  });

  @override
  State<LogTail> createState() => _LogTailState();
}

class _LogTailState extends State<LogTail> {
  final ScrollController _scrollController = ScrollController();
  bool _userScrolled = false;
  Timer? _scrollDebounce;

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);
  }

  @override
  void didUpdateWidget(covariant LogTail oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.autoScroll && !_userScrolled && widget.logs.isNotEmpty) {
      _scrollToBottom();
    }
  }

  void _onScroll() {
    _userScrolled = _scrollController.position.pixels <
        _scrollController.position.maxScrollExtent - 50;
  }

  void _scrollToBottom() {
    _scrollDebounce?.cancel();
    _scrollDebounce = Timer(const Duration(milliseconds: 50), () {
      if (_scrollController.hasClients && mounted) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 200),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  void dispose() {
    _scrollController.removeListener(_onScroll);
    _scrollController.dispose();
    _scrollDebounce?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final filteredLogs = _getFilteredLogs();

    return Column(
      children: [
        // Toolbar
        if (widget.filterSources != null || widget.filterLevels != null || widget.onClear != null)
          _buildToolbar(context, filteredLogs.length),

        // Log list
        Expanded(
          child: filteredLogs.isEmpty
              ? _buildEmptyState(context)
              : ListView.builder(
                  controller: _scrollController,
                  reverse: true, // newest at bottom
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  itemCount: filteredLogs.length,
                  itemBuilder: (context, index) {
                    final log = filteredLogs[filteredLogs.length - 1 - index];
                    return _LogEntryTile(
                      log: log,
                      showTimestamp: widget.showTimestamps,
                      showSource: widget.showSource,
                      monospace: widget.monospace,
                      onTap: widget.onTap,
                    );
                  },
                ),
        ),

        // User scrolled indicator
        if (_userScrolled)
          _buildScrollIndicator(context),
      ],
    );
  }

  List<LogEntry> _getFilteredLogs() {
    var result = widget.logs.where((log) {
      if (widget.filterSources != null && !widget.filterSources!.contains(log.source)) return false;
      if (widget.filterLevels != null && !widget.filterLevels!.contains(log.level)) return false;
      return true;
    }).toList();

    if (result.length > widget.maxLines) {
      result = result.sublist(result.length - widget.maxLines);
    }
    return result;
  }

  Widget _buildToolbar(BuildContext context, int count) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: EcoColors.surfaceVariant,
        border: Border(bottom: BorderSide(color: EcoColors.outlineVariant)),
      ),
      child: Row(
        children: [
          Text('$count linhas', style: theme.textTheme.labelSmall?.copyWith(color: EcoColors.onSurfaceVariant)),
          const Spacer(),
          if (widget.filterSources != null)
            _FilterChipSet(
              label: 'Fontes',
              options: widget.filterSources!.toList()..sort(),
              selected: widget.filterSources!,
              onChanged: (val) {}, // Parent handles filter
            ),
          if (widget.filterLevels != null)
            _FilterChipSet(
              label: 'Níveis',
              options: widget.filterLevels!.toList()..sort(),
              selected: widget.filterLevels!,
              onChanged: (val) {},
            ),
          if (widget.onClear != null)
            TextButton.icon(
              onPressed: widget.onClear,
              icon: const Icon(Icons.clear_all, size: 16),
              label: const Text('Limpar'),
              style: TextButton.styleFrom(foregroundColor: EcoColors.error),
            ),
        ],
      ),
    );
  }

  Widget _buildEmptyState(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.terminal, size: 48, color: EcoColors.onSurfaceDisabled),
          const SizedBox(height: 12),
          Text('Nenhum log', style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: EcoColors.onSurfaceVariant)),
        ],
      ),
    );
  }

  Widget _buildScrollIndicator(BuildContext context) {
    return Container(
      margin: const EdgeInsets.all(8),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: EcoColors.primaryContainer,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: EcoColors.primary),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.keyboard_arrow_down, size: 16, color: EcoColors.primary),
          const SizedBox(width: 4),
          Text(
            'Novos logs',
            style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: EcoColors.primary,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(width: 8),
          TextButton(
            onPressed: () {
              _userScrolled = false;
              _scrollToBottom();
            },
            style: TextButton.styleFrom(
              padding: EdgeInsets.zero,
              minimumSize: Size.zero,
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
              foregroundColor: EcoColors.primary,
            ),
            child: const Text('Ir para o final'),
          ),
        ],
      ),
    );
  }
}

class _LogEntryTile extends StatelessWidget {
  final LogEntry log;
  final bool showTimestamp;
  final bool showSource;
  final bool monospace;
  final ValueChanged<LogEntry>? onTap;

  const _LogEntryTile({
    required this.log,
    required this.showTimestamp,
    required this.showSource,
    required this.monospace,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final timeStr = showTimestamp ? '${log.timestamp.hour.toString().padLeft(2, '0')}:${log.timestamp.minute.toString().padLeft(2, '0')}:${log.timestamp.second.toString().padLeft(2, '0')}' : '';
    final sourceStr = showSource ? '[${log.source}]' : '';

    Widget content = Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (timeStr.isNotEmpty) ...[
          Text(
            timeStr,
            style: theme.textTheme.labelSmall?.copyWith(
              color: EcoColors.onSurfaceDisabled,
              fontFamily: monospace ? 'JetBrainsMono' : null,
              fontFeatures: const [FontFeature.tabularFigures()],
            ),
          ),
          const SizedBox(width: 8),
        ],
        if (sourceStr.isNotEmpty) ...[
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
            decoration: BoxDecoration(
              color: log.levelColor.withValues(alpha: 0.15),
              borderRadius: BorderRadius.circular(4),
            ),
            child: Text(
              sourceStr,
              style: theme.textTheme.labelSmall?.copyWith(
                color: log.levelColor,
                fontWeight: FontWeight.w500,
                fontFamily: monospace ? 'JetBrainsMono' : null,
              ),
            ),
          ),
          const SizedBox(width: 8),
        ],
        Expanded(
          child: SelectableText(
            log.message,
            style: theme.textTheme.bodySmall?.copyWith(
              color: EcoColors.onSurface,
              fontFamily: monospace ? 'JetBrainsMono' : null,
              height: 1.4,
            ),
          ),
        ),
      ],
    );

    if (onTap != null) {
      return InkWell(
        onTap: () => onTap!(log),
        borderRadius: BorderRadius.circular(4),
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 2, horizontal: 8),
          child: content,
        ),
      );
    }

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2, horizontal: 8),
      child: content,
    );
  }
}

class _FilterChipSet extends StatelessWidget {
  final String label;
  final List<String> options;
  final Set<String> selected;
  final ValueChanged<Set<String>> onChanged;

  const _FilterChipSet({
    required this.label,
    required this.options,
    required this.selected,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return PopupMenuButton<Set<String>>(
      offset: const Offset(0, 40),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(
          color: EcoColors.surfaceContainer,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: EcoColors.outline),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(label, style: Theme.of(context).textTheme.labelSmall?.copyWith(color: EcoColors.onSurfaceVariant)),
            const SizedBox(width: 4),
            const Icon(Icons.expand_more, size: 16, color: EcoColors.onSurfaceVariant),
          ],
        ),
      ),
      itemBuilder: (context) => [
        PopupMenuItem<Set<String>>(
          value: {},
          enabled: false,
          child: Text('Filtrar $label', style: Theme.of(context).textTheme.labelMedium?.copyWith(fontWeight: FontWeight.w600)),
        ),
        const PopupMenuDivider(),
        ...options.map((opt) => PopupMenuItem<Set<String>>(
          value: selected.contains(opt) ? (selected..remove(opt)) : (selected..add(opt)),
          child: Row(
            children: [
              if (selected.contains(opt)) const Icon(Icons.check, size: 18, color: EcoColors.primary),
              const SizedBox(width: 8),
              Text(opt),
            ],
          ),
        )),
      ],
    );
  }
}

/// LogTail compacto (para cards pequenos)
class LogTailCompact extends StatelessWidget {
  final List<LogEntry> logs;
  final int maxLines;
  final bool showTimestamp;

  const LogTailCompact({
    super.key,
    required this.logs,
    this.maxLines = 5,
    this.showTimestamp = true,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final displayLogs = logs.length > maxLines
        ? logs.sublist(logs.length - maxLines)
        : logs;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: displayLogs.reversed.map((log) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 1),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (showTimestamp)
              Text(
                '${log.timestamp.hour.toString().padLeft(2, '0')}:${log.timestamp.minute.toString().padLeft(2, '0')}:${log.timestamp.second.toString().padLeft(2, '0')} ',
                style: theme.textTheme.labelSmall?.copyWith(
                  color: EcoColors.onSurfaceDisabled,
                  fontFamily: 'JetBrainsMono',
                  fontFeatures: const [FontFeature.tabularFigures()],
                ),
              ),
            Container(
              width: 4,
              height: 4,
              margin: const EdgeInsets.only(top: 3, right: 6),
              decoration: BoxDecoration(
                color: log.levelColor,
                shape: BoxShape.circle,
              ),
            ),
            Expanded(
              child: Text(
                log.message,
                style: theme.textTheme.labelSmall?.copyWith(
                  color: EcoColors.onSurfaceVariant,
                  fontFamily: 'JetBrainsMono',
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
      )).toList(),
    );
  }
}