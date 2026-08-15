// MemoryBar — Barra de confiança com gradiente fato/provável/hipótese
import 'package:flutter/material.dart';
import '../../theme/eco_theme.dart';

class MemoryBar extends StatelessWidget {
  final double confidence; // 0.0 - 1.0
  final double height;
  final double borderRadius;
  final bool showLabel;
  final String? label;
  final bool animate;
  final Duration animationDuration;

  const MemoryBar({
    super.key,
    required this.confidence,
    this.height = 8,
    this.borderRadius = 4,
    this.showLabel = true,
    this.label,
    this.animate = true,
    this.animationDuration = const Duration(milliseconds: 800),
  });

  @override
  Widget build(BuildContext context) {
    final clampedConfidence = confidence.clamp(0.0, 1.0);
    final level = _getLevel(clampedConfidence);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (showLabel && (label != null || level != ConfidenceLevel.high))
          Padding(
            padding: const EdgeInsets.only(bottom: 4),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                if (label != null)
                  Text(label!, style: Theme.of(context).textTheme.labelSmall?.copyWith(color: EcoColors.onSurfaceVariant)),
                Text(
                  '${(clampedConfidence * 100).toStringAsFixed(0)}%',
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: _getColor(level),
                    fontWeight: FontWeight.w600,
                    fontFeatures: const [FontFeature.tabularFigures()],
                  ),
                ),
              ],
            ),
          ),
        AnimatedContainer(
          duration: animate ? animationDuration : Duration.zero,
          curve: Curves.easeOutCubic,
          height: height,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(borderRadius),
            color: EcoColors.surfaceVariant,
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(borderRadius),
            child: Stack(
              children: [
                // Background track
                Container(
                  width: double.infinity,
                  height: height,
                  color: EcoColors.surfaceVariant,
                ),
                // Confidence fill with gradient
                AnimatedFractionallySizedBox(
                  duration: animate ? animationDuration : Duration.zero,
                  curve: Curves.easeOutCubic,
                  widthFactor: clampedConfidence,
                  child: Container(
                    height: height,
                    decoration: BoxDecoration(
                      gradient: _getGradient(level),
                      borderRadius: BorderRadius.circular(borderRadius),
                    ),
                  ),
                ),
                // Segment markers (subtle)
                if (clampedConfidence > 0)
                  Positioned.fill(
                    child: CustomPaint(
                      painter: _SegmentMarkerPainter(
                        confidence: clampedConfidence,
                        color: EcoColors.onSurface.withValues(alpha: 0.1),
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  ConfidenceLevel _getLevel(double conf) {
    if (conf >= 0.9) return ConfidenceLevel.high;
    if (conf >= 0.7) return ConfidenceLevel.medium;
    return ConfidenceLevel.low;
  }

  Color _getColor(ConfidenceLevel level) {
    switch (level) {
      case ConfidenceLevel.high:
        return EcoColors.confidenceHigh;
      case ConfidenceLevel.medium:
        return EcoColors.confidenceMed;
      case ConfidenceLevel.low:
        return EcoColors.confidenceLow;
    }
  }

  LinearGradient _getGradient(ConfidenceLevel level) {
    switch (level) {
      case ConfidenceLevel.high:
        return LinearGradient(
          colors: [EcoColors.confidenceHigh, EcoColors.confidenceHigh.withValues(alpha: 0.8)],
          begin: Alignment.centerLeft,
          end: Alignment.centerRight,
        );
      case ConfidenceLevel.medium:
        return LinearGradient(
          colors: [EcoColors.confidenceMed, EcoColors.confidenceMed.withValues(alpha: 0.8)],
          begin: Alignment.centerLeft,
          end: Alignment.centerRight,
        );
      case ConfidenceLevel.low:
        return LinearGradient(
          colors: [EcoColors.confidenceLow, EcoColors.confidenceLow.withValues(alpha: 0.8)],
          begin: Alignment.centerLeft,
          end: Alignment.centerRight,
        );
    }
  }
}

enum ConfidenceLevel { high, medium, low }

/// MemoryBar horizontal com segmentos coloridos (fato | provável | hipótese)
class MemoryBarSegmented extends StatelessWidget {
  final double factPct;      // >= 0.9
  final double probablePct;  // 0.7 - 0.9
  final double hypothesisPct; // < 0.7
  final double height;
  final double borderRadius;
  final bool animate;

  const MemoryBarSegmented({
    super.key,
    required this.factPct,
    required this.probablePct,
    required this.hypothesisPct,
    this.height = 10,
    this.borderRadius = 5,
    this.animate = true,
  });

  @override
  Widget build(BuildContext context) {
    final total = factPct + probablePct + hypothesisPct;
    if (total == 0) return _emptyBar();

    return ClipRRect(
      borderRadius: BorderRadius.circular(borderRadius),
      child: Container(
        height: height,
        child: Row(
          children: [
            if (factPct > 0)
              _Segment(
                fraction: factPct / total,
                color: EcoColors.confidenceHigh,
                animate: animate,
              ),
            if (probablePct > 0)
              _Segment(
                fraction: probablePct / total,
                color: EcoColors.confidenceMed,
                animate: animate,
              ),
            if (hypothesisPct > 0)
              _Segment(
                fraction: hypothesisPct / total,
                color: EcoColors.confidenceLow,
                animate: animate,
              ),
          ],
        ),
      ),
    );
  }

  Widget _emptyBar() => Container(
    height: height,
    decoration: BoxDecoration(
      color: EcoColors.surfaceVariant,
      borderRadius: BorderRadius.circular(borderRadius),
    ),
  );
}

class _Segment extends StatelessWidget {
  final double fraction;
  final Color color;
  final bool animate;

  const _Segment({
    required this.fraction,
    required this.color,
    this.animate = true,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      flex: (fraction * 1000).round().clamp(1, 1000),
      child: AnimatedContainer(
        duration: animate ? const Duration(milliseconds: 800) : Duration.zero,
        curve: Curves.easeOutCubic,
        height: double.infinity,
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [color, color.withValues(alpha: 0.85)],
            begin: Alignment.centerLeft,
            end: Alignment.centerRight,
          ),
        ),
      ),
    );
  }
}

class _SegmentMarkerPainter extends CustomPainter {
  final double confidence;
  final Color color;

  _SegmentMarkerPainter({required this.confidence, required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..strokeWidth = 1;

    // Marker at 0.7 (provável threshold)
    final x7 = size.width * 0.7;
    canvas.drawLine(Offset(x7, 0), Offset(x7, size.height), paint);

    // Marker at 0.9 (fato threshold)
    final x9 = size.width * 0.9;
    canvas.drawLine(Offset(x9, 0), Offset(x9, size.height), paint);

    // Current confidence indicator
    final xConf = size.width * confidence;
    final confPaint = Paint()
      ..color = EcoColors.onSurface
      ..strokeWidth = 2;
    canvas.drawLine(Offset(xConf, -2), Offset(xConf, size.height + 2), confPaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) {
    return oldDelegate is _SegmentMarkerPainter &&
        oldDelegate.confidence != confidence;
  }
}

/// Legenda de confiança
class ConfidenceLegend extends StatelessWidget {
  const ConfidenceLegend({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        _LegendItem(color: EcoColors.confidenceHigh, label: 'Fato (≥0.9)'),
        const SizedBox(width: 16),
        _LegendItem(color: EcoColors.confidenceMed, label: 'Provável (0.7-0.9)'),
        const SizedBox(width: 16),
        _LegendItem(color: EcoColors.confidenceLow, label: 'Hipótese (<0.7)'),
      ],
    );
  }
}

class _LegendItem extends StatelessWidget {
  final Color color;
  final String label;

  const _LegendItem({required this.color, required this.label});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(3),
          ),
        ),
        const SizedBox(width: 6),
        Text(label, style: theme.textTheme.labelSmall?.copyWith(color: EcoColors.onSurfaceVariant)),
      ],
    );
  }
}