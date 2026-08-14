// EcoCard — Card base com glassmorphism, animação de entrada, estados
import 'package:flutter/material.dart';
import '../../theme/eco_theme.dart';

class EcoCard extends StatefulWidget {
  final Widget child;
  final EdgeInsetsGeometry? padding;
  final EdgeInsetsGeometry? margin;
  final Color? backgroundColor;
  final Color? borderColor;
  final double? elevation;
  final VoidCallback? onTap;
  final bool animate;
  final Duration animationDuration;
  final BorderRadius? borderRadius;

  const EcoCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(16),
    this.margin = const EdgeInsets.all(8),
    this.backgroundColor,
    this.borderColor,
    this.elevation = 0,
    this.onTap,
    this.animate = true,
    this.animationDuration = const Duration(milliseconds: 400),
    this.borderRadius,
  });

  @override
  State<EcoCard> createState() => _EcoCardState();
}

class _EcoCardState extends State<EcoCard> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;
  late Animation<double> _fadeAnimation;
  bool _hovered = false;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: widget.animationDuration,
      vsync: this,
    );
    _scaleAnimation = Tween<double>(begin: 0.95, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOutCubic),
    );
    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOut),
    );
    if (widget.animate) {
      _controller.forward();
    } else {
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
    final bgColor = widget.backgroundColor ?? theme.cardTheme.color ?? EcoColors.surfaceContainer;
    final borderCol = widget.borderColor ?? theme.cardTheme.shape is RoundedRectangleBorder
        ? (theme.cardTheme.shape as RoundedRectangleBorder).side.color
        : EcoColors.outline;

    Widget card = AnimatedBuilder(
      animation: _controller,
      builder: (context, child) => Transform.scale(
        scale: widget.animate ? _scaleAnimation.value : 1.0,
        child: Opacity(
          opacity: widget.animate ? _fadeAnimation.value : 1.0,
          child: child,
        ),
      ),
      child: MouseRegion(
        onEnter: (_) => setState(() => _hovered = true),
        onExit: (_) => setState(() => _hovered = false),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          curve: Curves.easeOut,
          margin: widget.margin,
          padding: widget.padding,
          decoration: BoxDecoration(
            color: _hovered ? bgColor.withValues(alpha: 0.95) : bgColor,
            borderRadius: widget.borderRadius ?? BorderRadius.circular(12),
            border: Border.all(
              color: _hovered ? EcoColors.primary : borderCol,
              width: _hovered ? 1.5 : 1,
            ),
            boxShadow: _hovered
                ? [
                    BoxShadow(
                      color: EcoColors.primary.withValues(alpha: 0.08),
                      blurRadius: 16,
                      spreadRadius: 2,
                    ),
                  ]
                : null,
          ),
          child: widget.child,
        ),
      ),
    );

    if (widget.onTap != null) {
      card = InkWell(
        onTap: widget.onTap,
        borderRadius: widget.borderRadius ?? BorderRadius.circular(12),
        splashColor: EcoColors.primary.withValues(alpha: 0.1),
        highlightColor: EcoColors.primary.withValues(alpha: 0.05),
        child: card,
      );
    }

    return card;
  }
}

/// EcoCard com header (título + ação opcional)
class EcoCardHeader extends StatelessWidget {
  final String title;
  final String? subtitle;
  final Widget? leading;
  final Widget? trailing;
  final Widget child;
  final EdgeInsetsGeometry? padding;

  const EcoCardHeader({
    super.key,
    required this.title,
    this.subtitle,
    this.leading,
    this.trailing,
    required this.child,
    this.padding,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return EcoCard(
      padding: padding ?? const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              if (leading != null) ...[leading!, const SizedBox(width: 12)],
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: theme.textTheme.titleMedium),
                    if (subtitle != null)
                      Text(subtitle!, style: theme.textTheme.bodySmall?.copyWith(color: EcoColors.onSurfaceVariant)),
                  ],
                ),
              ),
              if (trailing != null) trailing!,
            ],
          ),
          const SizedBox(height: 16),
          child,
        ],
      ),
    );
  }
}