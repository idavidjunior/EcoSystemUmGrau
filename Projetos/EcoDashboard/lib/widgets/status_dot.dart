// StatusDot — Ponto de status animado (pulsante, cores semânticas)
import 'package:flutter/material.dart';
import '../../models/ecosystem_state.dart';
import '../../theme/eco_theme.dart';

class StatusDot extends StatefulWidget {
  final ColorStatus status;
  final double size;
  final bool pulse;
  final Duration pulseDuration;
  final String? tooltip;
  final VoidCallback? onTap;

  const StatusDot({
    super.key,
    required this.status,
    this.size = 10,
    this.pulse = true,
    this.pulseDuration = const Duration(milliseconds: 1500),
    this.tooltip,
    this.onTap,
  });

  @override
  State<StatusDot> createState() => _StatusDotState();
}

class _StatusDotState extends State<StatusDot> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;
  late Animation<double> _opacityAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: widget.pulseDuration,
      vsync: this,
    );
    _scaleAnimation = Tween<double>(begin: 1.0, end: 1.4).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
    _opacityAnimation = Tween<double>(begin: 1.0, end: 0.3).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
    if (widget.pulse) {
      _controller.repeat(reverse: true);
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Color get _color {
    switch (widget.status) {
      case ColorStatus.success:
        return EcoColors.success;
      case ColorStatus.warning:
        return EcoColors.warning;
      case ColorStatus.error:
        return EcoColors.error;
      case ColorStatus.info:
        return EcoColors.info;
    }
  }

  @override
  Widget build(BuildContext context) {
    Widget dot = AnimatedBuilder(
      animation: _controller,
      builder: (context, child) => Transform.scale(
        scale: widget.pulse ? _scaleAnimation.value : 1.0,
        child: Opacity(
          opacity: widget.pulse ? _opacityAnimation.value : 1.0,
          child: child,
        ),
      ),
      child: Container(
        width: widget.size,
        height: widget.size,
        decoration: BoxDecoration(
          color: _color,
          shape: BoxShape.circle,
          boxShadow: [
            BoxShadow(
              color: _color.withValues(alpha: 0.5),
              blurRadius: widget.size * 0.8,
              spreadRadius: widget.size * 0.2,
            ),
          ],
        ),
      ),
    );

    if (widget.tooltip != null) {
      dot = Tooltip(
        message: widget.tooltip!,
        child: dot,
      );
    }

    if (widget.onTap != null) {
      dot = InkWell(
        onTap: widget.onTap,
        borderRadius: BorderRadius.circular(widget.size),
        child: Padding(
          padding: EdgeInsets.all(widget.size * 0.5),
          child: dot,
        ),
      );
    }

    return dot;
  }
}

/// StatusDot com label (ex: "● Conectado")
class StatusLabel extends StatelessWidget {
  final ColorStatus status;
  final String label;
  final double dotSize;
  final TextStyle? labelStyle;
  final bool pulse;

  const StatusLabel({
    super.key,
    required this.status,
    required this.label,
    this.dotSize = 8,
    this.labelStyle,
    this.pulse = true,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        StatusDot(
          status: status,
          size: dotSize,
          pulse: pulse,
        ),
        const SizedBox(width: 6),
        Text(
          label,
          style: labelStyle ?? theme.textTheme.labelMedium?.copyWith(
            color: EcoColors.onSurface,
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }
}

/// Status anel (para indicadores maiores)
class StatusRing extends StatefulWidget {
  final ColorStatus status;
  final double size;
  final double strokeWidth;
  final bool animate;
  final double progress; // 0.0 - 1.0 para anel de progresso

  const StatusRing({
    super.key,
    required this.status,
    this.size = 24,
    this.strokeWidth = 3,
    this.animate = true,
    this.progress = 1.0,
  });

  @override
  State<StatusRing> createState() => _StatusRingState();
}

class _StatusRingState extends State<StatusRing> with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 1000),
      vsync: this,
    );
    if (widget.animate) {
      _controller.repeat();
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Color get _color {
    switch (widget.status) {
      case ColorStatus.success:
        return EcoColors.success;
      case ColorStatus.warning:
        return EcoColors.warning;
      case ColorStatus.error:
        return EcoColors.error;
      case ColorStatus.info:
        return EcoColors.info;
    }
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: widget.size,
      height: widget.size,
      child: AnimatedBuilder(
        animation: _controller,
        builder: (context, child) => CustomPaint(
          painter: _StatusRingPainter(
            color: _color,
            strokeWidth: widget.strokeWidth,
            progress: widget.progress,
            rotation: widget.animate ? _controller.value * 2 * 3.14159 : 0,
          ),
        ),
      ),
    );
  }
}

class _StatusRingPainter extends CustomPainter {
  final Color color;
  final double strokeWidth;
  final double progress;
  final double rotation;

  _StatusRingPainter({
    required this.color,
    required this.strokeWidth,
    required this.progress,
    required this.rotation,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = (size.width - strokeWidth) / 2;

    // Background ring
    final bgPaint = Paint()
      ..color = color.withValues(alpha: 0.15)
      ..strokeWidth = strokeWidth
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    canvas.drawCircle(center, radius, bgPaint);

    // Progress ring
    final fgPaint = Paint()
      ..color = color
      ..strokeWidth = strokeWidth
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    const startAngle = -3.14159 / 2; // Top
    final sweepAngle = 2 * 3.14159 * progress;

    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      startAngle + rotation,
      sweepAngle,
      false,
      fgPaint,
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) {
    return oldDelegate is _StatusRingPainter &&
        (oldDelegate.color != color ||
         oldDelegate.progress != progress ||
         oldDelegate.rotation != rotation);
  }
}