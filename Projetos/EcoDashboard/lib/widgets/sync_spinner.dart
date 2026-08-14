// SyncSpinner + RadarProgress — Indicadores animados para sincronização e radar
import 'package:flutter/material.dart';
import '../../theme/eco_theme.dart';

/// SyncSpinner — Spinner de sincronização com estados
class SyncSpinner extends StatefulWidget {
  final SyncPhase phase;
  final double size;
  final double strokeWidth;
  final bool showLabel;
  final String? customLabel;
  final Duration animationDuration;

  const SyncSpinner({
    super.key,
    required this.phase,
    this.size = 32,
    this.strokeWidth = 3,
    this.showLabel = true,
    this.customLabel,
    this.animationDuration = const Duration(milliseconds: 1000),
  });

  @override
  State<SyncSpinner> createState() => _SyncSpinnerState();
}

class _SyncSpinnerState extends State<SyncSpinner> with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: widget.animationDuration,
      vsync: this,
    );
    _updateAnimation();
  }

  @override
  void didUpdateWidget(covariant SyncSpinner oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.phase != widget.phase) {
      _updateAnimation();
    }
  }

  void _updateAnimation() {
    switch (widget.phase) {
      case SyncPhase.idle:
      case SyncPhase.completed:
        _controller.stop();
        _controller.value = 0;
        break;
      case SyncPhase.syncing:
      case SyncPhase.pushing:
      case SyncPhase.pulling:
        _controller.repeat();
        break;
      case SyncPhase.error:
        _controller.stop();
        _controller.value = 0;
        break;
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
    final (color, label) = _getPhaseStyle();

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        SizedBox(
          width: widget.size,
          height: widget.size,
          child: AnimatedBuilder(
            animation: _controller,
            builder: (context, child) => CustomPaint(
              painter: _SyncSpinnerPainter(
                progress: _controller.value,
                phase: widget.phase,
                color: color,
                strokeWidth: widget.strokeWidth,
              ),
            ),
          ),
        ),
        if (widget.showLabel) ...[
          const SizedBox(height: 8),
          Text(
            widget.customLabel ?? label,
            style: theme.textTheme.labelMedium?.copyWith(
              color: color,
              fontWeight: FontWeight.w500,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ],
    );
  }

  (Color, String) _getPhaseStyle() {
    switch (widget.phase) {
      case SyncPhase.idle:
        return (EcoColors.onSurfaceVariant, 'Parado');
      case SyncPhase.syncing:
        return (EcoColors.primary, 'Sincronizando...');
      case SyncPhase.pulling:
        return (EcoColors.info, 'Puxando alterações...');
      case SyncPhase.pushing:
        return (EcoColors.primary, 'Enviando alterações...');
      case SyncPhase.completed:
        return (EcoColors.success, 'Sincronizado');
      case SyncPhase.error:
        return (EcoColors.error, 'Erro na sincronização');
    }
  }
}

enum SyncPhase { idle, syncing, pulling, pushing, completed, error }

class _SyncSpinnerPainter extends CustomPainter {
  final double progress;
  final SyncPhase phase;
  final Color color;
  final double strokeWidth;

  _SyncSpinnerPainter({
    required this.progress,
    required this.phase,
    required this.color,
    required this.strokeWidth,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = (size.width - strokeWidth) / 2;

    final bgPaint = Paint()
      ..color = color.withValues(alpha: 0.1)
      ..strokeWidth = strokeWidth
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    canvas.drawCircle(center, radius, bgPaint);

    final fgPaint = Paint()
      ..color = color
      ..strokeWidth = strokeWidth
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    switch (phase) {
      case SyncPhase.syncing:
      case SyncPhase.pulling:
      case SyncPhase.pushing:
        // Rotating arc
        const startAngle = -math.pi / 2;
        final sweepAngle = (0.6 + 0.4 * math.sin(progress * 2 * math.pi * 2)).abs() * math.pi;
        canvas.drawArc(
          Rect.fromCircle(center: center, radius: radius),
          startAngle + progress * 2 * math.pi,
          sweepAngle,
          false,
          fgPaint,
        );
        break;
      case SyncPhase.completed:
        // Checkmark
        _drawCheckmark(canvas, center, radius, fgPaint);
        break;
      case SyncPhase.error:
        // X mark
        _drawError(canvas, center, radius, fgPaint);
        break;
      case SyncPhase.idle:
        // Static ring
        canvas.drawCircle(center, radius, fgPaint);
        break;
    }
  }

  void _drawCheckmark(Canvas canvas, Offset center, double radius, Paint paint) {
    final path = Path();
    const scale = 0.4;
    path.moveTo(center.dx - radius * scale * 0.5, center.dy);
    path.lineTo(center.dx - radius * scale * 0.1, center.dy + radius * scale * 0.4);
    path.lineTo(center.dx + radius * scale * 0.5, center.dy - radius * scale * 0.4);
    canvas.drawPath(path, paint);
  }

  void _drawError(Canvas canvas, Offset center, double radius, Paint paint) {
    final path = Path();
    const scale = 0.5;
    path.moveTo(center.dx - radius * scale, center.dy - radius * scale);
    path.lineTo(center.dx + radius * scale, center.dy + radius * scale);
    path.moveTo(center.dx + radius * scale, center.dy - radius * scale);
    path.lineTo(center.dx - radius * scale, center.dy + radius * scale);
    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) {
    return oldDelegate is _SyncSpinnerPainter &&
        oldDelegate.progress != progress &&
        oldDelegate.phase != phase;
  }
}

import 'dart:math' as math;

/// RadarProgress — Progresso do Evolution Radar (collect → filter → package)
class RadarProgress extends StatelessWidget {
  final RadarPhase phase;
  final int currentStep;
  final int totalSteps;
  final String? currentItem;
  final double size;
  final bool showDetails;

  const RadarProgress({
    super.key,
    required this.phase,
    this.currentStep = 0,
    this.totalSteps = 3,
    this.currentItem,
    this.size = 120,
    this.showDetails = true,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final phaseConfig = _getPhaseConfig();

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        SizedBox(
          width: size,
          height: size,
          child: Stack(
            alignment: Alignment.center,
            children: [
              // Background steps
              CustomPaint(
                size: Size(size, size),
                painter: _RadarStepsPainter(
                  totalSteps: totalSteps,
                  activeStep: phase.index,
                  color: phaseConfig.color,
                ),
              ),
              // Center icon
              Container(
                width: size * 0.5,
                height: size * 0.5,
                decoration: BoxDecoration(
                  color: phaseConfig.color.withValues(alpha: 0.15),
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  phaseConfig.icon,
                  color: phaseConfig.color,
                  size: size * 0.25,
                ),
              ),
            ],
          ),
        ),
        if (showDetails) ...[
          const SizedBox(height: 12),
          Text(
            phaseConfig.label,
            style: theme.textTheme.titleSmall?.copyWith(
              color: phaseConfig.color,
              fontWeight: FontWeight.w600,
            ),
          ),
          if (currentItem != null) ...[
            const SizedBox(height: 4),
            Text(
              currentItem!,
              style: theme.textTheme.bodySmall?.copyWith(color: EcoColors.onSurfaceVariant),
              textAlign: TextAlign.center,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ],
          const SizedBox(height: 8),
          // Step indicators
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(totalSteps, (i) {
              final isActive = i <= phase.index;
              final isCurrent = i == phase.index;
              return Padding(
                padding: const EdgeInsets.symmetric(horizontal: 4),
                child: _StepIndicator(
                  index: i + 1,
                  active: isActive,
                  current: isCurrent,
                  color: phaseConfig.color,
                  label: _getStepLabel(i),
                ),
              );
            }),
          ),
        ],
      ],
    );
  }

  _PhaseConfig _getPhaseConfig() {
    switch (phase) {
      case RadarPhase.idle:
        return _PhaseConfig(
          color: EcoColors.onSurfaceVariant,
          icon: Icons.radar_outlined,
          label: 'Aguardando',
        );
      case RadarPhase.collect:
        return _PhaseConfig(
          color: EcoColors.info,
          icon: Icons.cloud_download_outlined,
          label: 'Coletando fontes...',
        );
      case RadarPhase.filter:
        return _PhaseConfig(
          color: EcoColors.primary,
          icon: Icons.filter_alt_outlined,
          label: 'Filtrando propostas...',
        );
      case RadarPhase.package:
        return _PhaseConfig(
          color: EcoColors.tertiary,
          icon: Icons.inventory_2_outlined,
          label: 'Empacotando...',
        );
      case RadarPhase.apply:
        return _PhaseConfig(
          color: EcoColors.success,
          icon: Icons.rocket_launch_outlined,
          label: 'Aplicando pacote...',
        );
      case RadarPhase.completed:
        return _PhaseConfig(
          color: EcoColors.success,
          icon: Icons.check_circle_outline,
          label: 'Concluído',
        );
      case RadarPhase.error:
        return _PhaseConfig(
          color: EcoColors.error,
          icon: Icons.error_outline,
          label: 'Erro',
        );
    }
  }

  String _getStepLabel(int index) {
    const labels = ['Coletar', 'Filtrar', 'Empacotar'];
    return index < labels.length ? labels[index] : 'Etapa ${index + 1}';
  }
}

enum RadarPhase { idle, collect, filter, package, apply, completed, error }

class _PhaseConfig {
  final Color color;
  final IconData icon;
  final String label;

  _PhaseConfig({required this.color, required this.icon, required this.label});
}

class _RadarStepsPainter extends CustomPainter {
  final int totalSteps;
  final int activeStep;
  final Color color;

  _RadarStepsPainter({
    required this.totalSteps,
    required this.activeStep,
    required this.color,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2 - 20;

    for (int i = 0; i < totalSteps; i++) {
      final angle = -math.pi / 2 + (i / totalSteps) * 2 * math.pi;
      final isActive = i <= activeStep;

      // Outer circle
      final outerPaint = Paint()
        ..color = isActive ? color : EcoColors.outlineVariant
        ..strokeWidth = 3
        ..style = PaintingStyle.stroke;

      canvas.drawCircle(center, radius, outerPaint);

      // Step dot
      final dotX = center.dx + radius * math.cos(angle);
      final dotY = center.dy + radius * math.sin(angle);

      final dotPaint = Paint()..color = isActive ? color : EcoColors.outlineVariant;
      canvas.drawCircle(Offset(dotX, dotY), 8, dotPaint);

      // Connect lines
      if (i < totalSteps - 1) {
        final nextAngle = -math.pi / 2 + ((i + 1) / totalSteps) * 2 * math.pi;
        final nextX = center.dx + radius * math.cos(nextAngle);
        final nextY = center.dy + radius * math.sin(nextAngle);

        final linePaint = Paint()
          ..color = i < activeStep ? color : EcoColors.outlineVariant
          ..strokeWidth = 2
          ..style = PaintingStyle.stroke;

        canvas.drawLine(Offset(dotX, dotY), Offset(nextX, nextY), linePaint);
      }
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) {
    return oldDelegate is _RadarStepsPainter &&
        oldDelegate.activeStep != activeStep;
  }
}

class _StepIndicator extends StatelessWidget {
  final int index;
  final bool active;
  final bool current;
  final Color color;
  final String label;

  const _StepIndicator({
    required this.index,
    required this.active,
    required this.current,
    required this.color,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        AnimatedContainer(
          duration: const Duration(milliseconds: 300),
          width: 24,
          height: 24,
          decoration: BoxDecoration(
            color: active ? color : EcoColors.outlineVariant,
            shape: BoxShape.circle,
            border: current && active
                ? Border.all(color: color, width: 2)
                : null,
            boxShadow: current && active
                ? [BoxShadow(color: color.withValues(alpha: 0.3), blurRadius: 8, spreadRadius: 2)]
                : null,
          ),
          child: Center(
            child: active
                ? Icon(Icons.check, size: 14, color: active ? (color == EcoColors.success ? Colors.white : EcoColors.onPrimary) : EcoColors.onSurfaceVariant)
                : Text('$index', style: TextStyle(color: EcoColors.onSurfaceVariant, fontSize: 10, fontWeight: FontWeight.w600)),
          ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: theme.textTheme.labelSmall?.copyWith(
            color: active ? color : EcoColors.onSurfaceVariant,
            fontWeight: current ? FontWeight.w600 : FontWeight.w400,
          ),
        ),
      ],
    );
  }
}