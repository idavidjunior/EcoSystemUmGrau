// VoiceWaveform — Visualizador de áudio em tempo real (STT/TTS/VAD)
import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../../models/ecosystem_state.dart';
import '../../theme/eco_theme.dart';

class VoiceWaveform extends StatefulWidget {
  final VoiceState voiceState;
  final double height;
  final int barCount;
  final Duration animationDuration;
  final bool showVadIndicator;
  final bool showLevelMeter;

  const VoiceWaveform({
    super.key,
    required this.voiceState,
    this.height = 60,
    this.barCount = 32,
    this.animationDuration = const Duration(milliseconds: 50),
    this.showVadIndicator = true,
    this.showLevelMeter = true,
  });

  @override
  State<VoiceWaveform> createState() => _VoiceWaveformState();
}

class _VoiceWaveformState extends State<VoiceWaveform> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  final List<double> _bars = [];
  final math.Random _random = math.Random();

  @override
  void initState() {
    super.initState();
    _bars.addAll(List.generate(widget.barCount, (_) => 0.0));
    _controller = AnimationController(
      duration: widget.animationDuration,
      vsync: this,
    )..addListener(_animateBars);
    _controller.repeat();
  }

  void _animateBars() {
    if (!mounted) return;
    setState(() {
      final isActive = widget.voiceState.sttActive || widget.voiceState.ttsPlaying;
      final baseLevel = widget.voiceState.inputLevel;

      for (int i = 0; i < widget.barCount; i++) {
        double target;
        if (isActive) {
          // Simula forma de onda com variação natural
          final center = widget.barCount / 2;
          final distFromCenter = (i - center).abs() / center;
          final envelope = 1.0 - distFromCenter * 0.7;
          final noise = _random.nextDouble() * 0.3 + 0.2;
          target = baseLevel * envelope * noise * (0.8 + _random.nextDouble() * 0.4);
        } else {
          // Decay to zero
          target = _bars[i] * 0.92;
        }
        _bars[i] = _bars[i] + (target - _bars[i]) * 0.3;
      }
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isStt = widget.voiceState.sttActive;
    final isTts = widget.voiceState.ttsPlaying;
    final isVad = widget.voiceState.vadActive;

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Waveform bars
        SizedBox(
          height: widget.height,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: List.generate(widget.barCount, (i) {
              final h = (widget.height - 4) * _bars[i].clamp(0.0, 1.0);
              final color = _getBarColor(i, isStt, isTts);
              return Padding(
                padding: const EdgeInsets.symmetric(horizontal: 1.5),
                child: AnimatedContainer(
                  duration: widget.animationDuration,
                  curve: Curves.easeOut,
                  width: 4,
                  height: h.clamp(2.0, widget.height - 4),
                  decoration: BoxDecoration(
                    color: color,
                    borderRadius: BorderRadius.circular(2),
                    boxShadow: [
                      BoxShadow(
                        color: color.withValues(alpha: 0.4),
                        blurRadius: 4,
                        spreadRadius: 0,
                      ),
                    ],
                  ),
                ),
              );
            }),
          ),
        ),

        // Indicators row
        if (widget.showVadIndicator || widget.showLevelMeter) ...[
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (widget.showVadIndicator) ...[
                _IndicatorDot(
                  active: isVad,
                  color: EcoColors.primary,
                  label: 'VAD',
                  pulse: isVad,
                ),
                const SizedBox(width: 16),
              ],
              if (widget.showLevelMeter) ...[
                _LevelMeter(
                  level: widget.voiceState.inputLevel,
                  active: isStt || isTts,
                ),
                const SizedBox(width: 16),
              ],
              _StatusText(
                isStt: isStt,
                isTts: isTts,
                text: isStt
                    ? widget.voiceState.currentText
                    : (isTts ? 'Falando...' : 'Aguardando'),
              ),
            ],
          ),
        ],
      ],
    );
  }

  Color _getBarColor(int index, bool isStt, bool isTts) {
    final progress = index / widget.barCount;
    if (isStt) {
      // STT: verde → ciano
      return Color.lerp(EcoColors.success, EcoColors.primary, progress)!;
    } else if (isTts) {
      // TTS: ciano → roxo
      return Color.lerp(EcoColors.primary, const Color(0xFFA371F7), progress)!;
    } else {
      // Idle: cinza sutil
      return EcoColors.outlineVariant;
    }
  }
}

class _IndicatorDot extends StatefulWidget {
  final bool active;
  final Color color;
  final String label;
  final bool pulse;

  const _IndicatorDot({
    required this.active,
    required this.color,
    required this.label,
    this.pulse = true,
  });

  @override
  State<_IndicatorDot> createState() => _IndicatorDotState();
}

class _IndicatorDotState extends State<_IndicatorDot> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 1000),
      vsync: this,
    );
    _animation = Tween<double>(begin: 1.0, end: 1.5).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
    if (widget.pulse && widget.active) {
      _controller.repeat(reverse: true);
    }
  }

  @override
  void didUpdateWidget(covariant _IndicatorDot oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.active && widget.pulse) {
      _controller.repeat(reverse: true);
    } else {
      _controller.stop();
      _controller.value = 1.0;
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) => Transform.scale(
        scale: widget.active && widget.pulse ? _animation.value : 1.0,
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 8,
              height: 8,
              decoration: BoxDecoration(
                color: widget.active ? widget.color : EcoColors.outlineVariant,
                shape: BoxShape.circle,
                boxShadow: widget.active
                    ? [BoxShadow(color: widget.color.withValues(alpha: 0.5), blurRadius: 6, spreadRadius: 1)]
                    : null,
              ),
            ),
            const SizedBox(width: 4),
            Text(
              widget.label,
              style: theme.textTheme.labelSmall?.copyWith(
                color: widget.active ? widget.color : EcoColors.onSurfaceVariant,
                fontWeight: widget.active ? FontWeight.w600 : FontWeight.w400,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _LevelMeter extends StatelessWidget {
  final double level;
  final bool active;

  const _LevelMeter({required this.level, required this.active});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final segments = 8;
    final filled = (level * segments).round().clamp(0, segments);

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        SizedBox(
          width: 48,
          height: 12,
          child: Stack(
            children: [
              // Background segments
              Row(
                children: List.generate(segments, (i) => Expanded(
                  child: Container(
                    margin: const EdgeInsets.symmetric(horizontal: 1),
                    decoration: BoxDecoration(
                      color: EcoColors.surfaceVariant,
                      borderRadius: BorderRadius.circular(1),
                    ),
                  ),
                )),
              ),
              // Filled segments
              Row(
                children: List.generate(segments, (i) => Expanded(
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 50),
                    curve: Curves.easeOut,
                    margin: const EdgeInsets.symmetric(horizontal: 1),
                    decoration: BoxDecoration(
                      color: i < filled
                          ? (level > 0.8 ? EcoColors.error : (level > 0.5 ? EcoColors.warning : EcoColors.success))
                          : Colors.transparent,
                      borderRadius: BorderRadius.circular(1),
                    ),
                  ),
                )),
              ),
            ],
          ),
        ),
        const SizedBox(width: 6),
        Text(
          '${(level * 100).toInt()}%',
          style: theme.textTheme.labelSmall?.copyWith(
            color: active ? EcoColors.onSurface : EcoColors.onSurfaceVariant,
            fontFeatures: const [FontFeature.tabularFigures()],
          ),
        ),
      ],
    );
  }
}

class _StatusText extends StatelessWidget {
  final bool isStt;
  final bool isTts;
  final String text;

  const _StatusText({required this.isStt, required this.isTts, required this.text});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    Color color;
    if (isStt) color = EcoColors.success;
    else if (isTts) color = EcoColors.primary;
    else color = EcoColors.onSurfaceVariant;

    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 200),
      child: Container(
        key: ValueKey(text),
        constraints: const BoxConstraints(maxWidth: 200),
        child: Text(
          text,
          style: theme.textTheme.bodySmall?.copyWith(
            color: color,
            fontWeight: isStt || isTts ? FontWeight.w500 : FontWeight.w400,
          ),
          overflow: TextOverflow.ellipsis,
        ),
      ),
    );
  }
}

/// Waveform circular (para avatar de voz)
class VoiceWaveformCircular extends StatefulWidget {
  final VoiceState voiceState;
  final double size;
  final double strokeWidth;

  const VoiceWaveformCircular({
    super.key,
    required this.voiceState,
    this.size = 48,
    this.strokeWidth = 3,
  });

  @override
  State<VoiceWaveformCircular> createState() => _VoiceWaveformCircularState();
}

class _VoiceWaveformCircularState extends State<VoiceWaveformCircular>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 1200),
      vsync: this,
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isActive = widget.voiceState.sttActive || widget.voiceState.ttsPlaying;
    final level = widget.voiceState.inputLevel;

    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) => SizedBox(
        width: widget.size,
        height: widget.size,
        child: CustomPaint(
          painter: _CircularWaveformPainter(
            progress: _controller.value,
            level: isActive ? level : 0.0,
            strokeWidth: widget.strokeWidth,
            color: widget.voiceState.sttActive ? EcoColors.success : EcoColors.primary,
          ),
        ),
      ),
    );
  }
}

class _CircularWaveformPainter extends CustomPainter {
  final double progress;
  final double level;
  final double strokeWidth;
  final Color color;

  _CircularWaveformPainter({
    required this.progress,
    required this.level,
    required this.strokeWidth,
    required this.color,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = (size.width - strokeWidth) / 2;

    // Background ring
    final bgPaint = Paint()
      ..color = color.withValues(alpha: 0.1)
      ..strokeWidth = strokeWidth
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    canvas.drawCircle(center, radius, bgPaint);

    // Animated arcs based on audio level
    final arcs = 4;
    for (int i = 0; i < arcs; i++) {
      final arcProgress = (progress + i / arcs) % 1.0;
      final startAngle = -math.pi / 2 + arcProgress * 2 * math.pi;
      final sweepAngle = (0.3 + level * 0.7) * math.pi / 2;

      final arcPaint = Paint()
        ..color = color.withValues(alpha: 1.0 - i * 0.2)
        ..strokeWidth = strokeWidth
        ..style = PaintingStyle.stroke
        ..strokeCap = StrokeCap.round;

      canvas.drawArc(
        Rect.fromCircle(center: center, radius: radius - i * 3.0),
        startAngle,
        sweepAngle,
        false,
        arcPaint,
      );
    }

    // Center dot pulse
    final dotPaint = Paint()..color = color;
    final dotRadius = 4.0 + level * 6.0;
    canvas.drawCircle(center, dotRadius, dotPaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}