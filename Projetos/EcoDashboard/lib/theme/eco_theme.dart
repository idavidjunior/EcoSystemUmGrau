// EcoSystemUmGrau Theme — Paleta ciano/verde escuro, Material 3
// "Profundo, técnico, vivo"

import 'package:flutter/material.dart';

/// Paleta de cores do EcoSystemUmGrau
class EcoColors {
  // Primária: Ciano vivo — identidade do ecossistema
  static const Color primary = Color(0xFF00E5A0);
  static const Color primaryContainer = Color(0xFF004D36);
  static const Color onPrimary = Color(0xFF001D14);
  static const Color onPrimaryContainer = Color(0xFFB7FDD9);

  // Secundária: Azul ciano — dados, MCP, bridge
  static const Color secondary = Color(0xFF00B8D4);
  static const Color secondaryContainer = Color(0xFF003643);
  static const Color onSecondary = Color(0xFF001D23);
  static const Color onSecondaryContainer = Color(0xFFB2E8FF);

  // Terciária: Âmbar — avisos, radar, atenção
  static const Color tertiary = Color(0xFFFFB300);
  static const Color tertiaryContainer = Color(0xFF3D2E00);
  static const Color onTertiary = Color(0xFF141000);
  static const Color onTertiaryContainer = Color(0xFFFFDC82);

  // Superfícies: Escuro profundo
  static const Color surface = Color(0xFF0D1117);
  static const Color surfaceVariant = Color(0xFF161B22);
  static const Color surfaceBright = Color(0xFF1C2128);
  static const Color surfaceContainer = Color(0xFF21262D);
  static const Color surfaceContainerHigh = Color(0xFF30363D);

  // Outline/Bordas
  static const Color outline = Color(0xFF30363D);
  static const Color outlineVariant = Color(0xFF21262D);

  // Estados semânticos
  static const Color success = Color(0xFF3FB950);    // OK, conectado, ativo
  static const Color warning = Color(0xFFFFB300);    // Atenção, coletando
  static const Color error = Color(0xFFF85149);      // Falha, offline, crítico
  static const Color info = Color(0xFF58A6FF);       // Info, neutro

  // Confiança (memory bars)
  static const Color confidenceHigh = Color(0xFF3FB950);    // >= 0.9 — fato
  static const Color confidenceMed = Color(0xFFA371F7);     // 0.7-0.9 — provável
  static const Color confidenceLow = Color(0xFFFFB300);     // < 0.7 — hipótese

  // Fonte
  static const Color onSurface = Color(0xFFF0F6FC);
  static const Color onSurfaceVariant = Color(0xFF8B949E);
  static const Color onSurfaceDisabled = Color(0xFF484F58);

  // Glassmorphism
  static const Color glassWhite = Color(0x1AFFFFFF);      // 10% white
  static const Color glassBorder = Color(0x1AFFFFFF);     // 10% white border
}

/// Gradientes reutilizáveis
class EcoGradients {
  static const LinearGradient primaryHorizontal = LinearGradient(
    colors: [EcoColors.primary, EcoColors.secondary],
    begin: Alignment.centerLeft,
    end: Alignment.centerRight,
  );

  static const LinearGradient confidenceGradient = LinearGradient(
    colors: [
      EcoColors.confidenceLow,    // hipótese
      EcoColors.confidenceMed,    // provável
      EcoColors.confidenceHigh,   // fato
    ],
    stops: [0.0, 0.5, 1.0],
    begin: Alignment.centerLeft,
    end: Alignment.centerRight,
  );

  static const LinearGradient surfaceGlass = LinearGradient(
    colors: [EcoColors.glassWhite, EcoColors.glassWhite],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const RadialGradient pulseBackground = RadialGradient(
    colors: [EcoColors.surfaceVariant, EcoColors.surface],
    center: Alignment.center,
    radius: 1.5,
  );
}

/// Tema completo do EcoSystemUmGrau
class EcoTheme {
  static ThemeData get dark {
    final ColorScheme colorScheme = const ColorScheme.dark(
      primary: EcoColors.primary,
      onPrimary: EcoColors.onPrimary,
      primaryContainer: EcoColors.primaryContainer,
      onPrimaryContainer: EcoColors.onPrimaryContainer,
      secondary: EcoColors.secondary,
      onSecondary: EcoColors.onSecondary,
      secondaryContainer: EcoColors.secondaryContainer,
      onSecondaryContainer: EcoColors.onSecondaryContainer,
      tertiary: EcoColors.tertiary,
      onTertiary: EcoColors.onTertiary,
      tertiaryContainer: EcoColors.tertiaryContainer,
      onTertiaryContainer: EcoColors.onTertiaryContainer,
      surface: EcoColors.surface,
      surfaceVariant: EcoColors.surfaceVariant,
      onSurface: EcoColors.onSurface,
      onSurfaceVariant: EcoColors.onSurfaceVariant,
      outline: EcoColors.outline,
      outlineVariant: EcoColors.outlineVariant,
      error: EcoColors.error,
      onError: EcoColors.onSurface,
      scrim: Colors.black87,
      shadow: Colors.black87,
    );

    final TextTheme textTheme = _textTheme(colorScheme);

    return ThemeData(
      useMaterial3: true,
      colorScheme: colorScheme,
      textTheme: textTheme,
      scaffoldBackgroundColor: EcoColors.surface,
      canvasColor: EcoColors.surface,

      // AppBar
      appBarTheme: AppBarTheme(
        backgroundColor: EcoColors.surface,
        foregroundColor: EcoColors.onSurface,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: textTheme.titleLarge?.copyWith(
          fontWeight: FontWeight.w600,
          letterSpacing: 0.5,
        ),
        iconTheme: const IconThemeData(color: EcoColors.onSurface),
        actionsIconTheme: const IconThemeData(color: EcoColors.onSurface),
      ),

      // Card / EcoCard
      cardTheme: CardThemeData(
        color: EcoColors.surfaceContainer,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: const BorderSide(color: EcoColors.outline, width: 1),
        ),
        margin: const EdgeInsets.all(8),
        clipBehavior: Clip.antiAlias,
      ),

      // ElevatedButton
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: EcoColors.primary,
          foregroundColor: EcoColors.onPrimary,
          elevation: 0,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          textStyle: textTheme.labelLarge?.copyWith(fontWeight: FontWeight.w600),
        ).copyWith(
          overlayColor: WidgetStateProperty.resolveWith<Color?>(
            (states) => states.contains(WidgetState.pressed)
                ? EcoColors.primary.withValues(alpha: 0.8)
                : null,
          ),
        ),
      ),

      // FilledButton (ações primárias)
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: EcoColors.primary,
          foregroundColor: EcoColors.onPrimary,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          textStyle: textTheme.labelLarge?.copyWith(fontWeight: FontWeight.w600),
        ),
      ),

      // OutlinedButton
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: EcoColors.primary,
          side: const BorderSide(color: EcoColors.primary, width: 1.5),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          textStyle: textTheme.labelLarge?.copyWith(fontWeight: FontWeight.w600),
        ),
      ),

      // TextButton
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: EcoColors.primary,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          textStyle: textTheme.labelLarge?.copyWith(fontWeight: FontWeight.w500),
        ),
      ),

      // InputDecoration (campos)
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: EcoColors.surfaceVariant,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: EcoColors.outline),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: EcoColors.outline),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: EcoColors.primary, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: EcoColors.error),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        labelStyle: textTheme.bodyMedium?.copyWith(color: EcoColors.onSurfaceVariant),
        hintStyle: textTheme.bodyMedium?.copyWith(color: EcoColors.onSurfaceDisabled),
      ),

      // Chip
      chipTheme: ChipThemeData(
        backgroundColor: EcoColors.surfaceVariant,
        selectedColor: EcoColors.primaryContainer,
        disabledColor: EcoColors.surfaceContainer,
        labelStyle: textTheme.labelMedium?.copyWith(color: EcoColors.onSurface),
        secondaryLabelStyle: textTheme.labelMedium?.copyWith(color: EcoColors.onPrimary),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
          side: const BorderSide(color: EcoColors.outline),
        ),
        side: const BorderSide(color: EcoColors.outline),
      ),

      // ProgressIndicator
      progressIndicatorTheme: ProgressIndicatorThemeData(
        color: EcoColors.primary,
        linearTrackColor: EcoColors.surfaceVariant,
        circularTrackColor: EcoColors.surfaceVariant,
      ),

      // Slider
      sliderTheme: SliderThemeData(
        activeTrackColor: EcoColors.primary,
        inactiveTrackColor: EcoColors.outlineVariant,
        thumbColor: EcoColors.primary,
        overlayColor: EcoColors.primary.withValues(alpha: 0.12),
        valueIndicatorColor: EcoColors.primary,
        valueIndicatorTextStyle: textTheme.labelSmall?.copyWith(color: EcoColors.onPrimary),
      ),

      // Divider
      dividerTheme: DividerThemeData(
        color: EcoColors.outlineVariant,
        thickness: 1,
        space: 1,
      ),

      // ListTile
      listTileTheme: ListTileThemeData(
        tileColor: Colors.transparent,
        selectedTileColor: EcoColors.primaryContainer.withValues(alpha: 0.3),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        titleTextStyle: textTheme.bodyLarge?.copyWith(color: EcoColors.onSurface),
        subtitleTextStyle: textTheme.bodySmall?.copyWith(color: EcoColors.onSurfaceVariant),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      ),

      // Tooltip
      tooltipTheme: TooltipThemeData(
        decoration: BoxDecoration(
          color: EcoColors.surfaceContainerHigh,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: EcoColors.outline),
        ),
        textStyle: textTheme.bodySmall?.copyWith(color: EcoColors.onSurface),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        preferBelow: true,
      ),

      // SnackBar
      snackBarTheme: SnackBarThemeData(
        backgroundColor: EcoColors.surfaceContainerHigh,
        contentTextStyle: textTheme.bodyMedium?.copyWith(color: EcoColors.onSurface),
        actionTextColor: EcoColors.primary,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        elevation: 8,
      ),

      // BottomSheet
      bottomSheetTheme: BottomSheetThemeData(
        backgroundColor: EcoColors.surface,
        surfaceTintColor: Colors.transparent,
        elevation: 16,
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        ),
        modalBackgroundColor: EcoColors.surface,
      ),

      // Dialog
      dialogTheme: DialogThemeData(
        backgroundColor: EcoColors.surface,
        surfaceTintColor: Colors.transparent,
        elevation: 16,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: EcoColors.outline),
        ),
        titleTextStyle: textTheme.titleLarge?.copyWith(color: EcoColors.onSurface),
        contentTextStyle: textTheme.bodyMedium?.copyWith(color: EcoColors.onSurfaceVariant),
      ),

      // NavigationRail
      navigationRailTheme: NavigationRailThemeData(
        backgroundColor: EcoColors.surface,
        indicatorColor: EcoColors.primaryContainer,
        selectedIconTheme: const IconThemeData(color: EcoColors.primary, size: 24),
        unselectedIconTheme: const IconThemeData(color: EcoColors.onSurfaceVariant, size: 24),
        selectedLabelTextStyle: textTheme.labelSmall?.copyWith(
          color: EcoColors.primary,
          fontWeight: FontWeight.w600,
        ),
        unselectedLabelTextStyle: textTheme.labelSmall?.copyWith(
          color: EcoColors.onSurfaceVariant,
        ),
        labelType: NavigationRailLabelType.all,
        useIndicator: true,
        groupAlignment: -0.9,
      ),

      // NavigationBar (mobile)
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: EcoColors.surface,
        surfaceTintColor: Colors.transparent,
        indicatorColor: EcoColors.primaryContainer,
        labelTextStyle: WidgetStateProperty.resolveWith<TextStyle>(
          (states) => textTheme.labelSmall!.copyWith(
            color: states.contains(WidgetState.selected)
                ? EcoColors.primary
                : EcoColors.onSurfaceVariant,
            fontWeight: states.contains(WidgetState.selected)
                ? FontWeight.w600
                : FontWeight.w400,
          ),
        ),
        iconTheme: WidgetStateProperty.resolveWith<IconThemeData>(
          (states) => IconThemeData(
            color: states.contains(WidgetState.selected)
                ? EcoColors.primary
                : EcoColors.onSurfaceVariant,
            size: 24,
          ),
        ),
        height: 72,
      ),

      // TabBar
      tabBarTheme: TabBarThemeData(
        labelColor: EcoColors.primary,
        unselectedLabelColor: EcoColors.onSurfaceVariant,
        indicatorColor: EcoColors.primary,
        indicatorSize: TabBarIndicatorSize.label,
        labelStyle: textTheme.labelLarge?.copyWith(fontWeight: FontWeight.w600),
        unselectedLabelStyle: textTheme.labelLarge?.copyWith(fontWeight: FontWeight.w400),
        dividerColor: EcoColors.outlineVariant,
        overlayColor: WidgetStateProperty.resolveWith<Color?>(
          (states) => states.contains(WidgetState.pressed)
              ? EcoColors.primary.withValues(alpha: 0.08)
              : null,
        ),
      ),

      // FloatingActionButton
      floatingActionButtonTheme: FloatingActionButtonThemeData(
        backgroundColor: EcoColors.primary,
        foregroundColor: EcoColors.onPrimary,
        elevation: 4,
        focusElevation: 6,
        hoverElevation: 8,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        extendedPadding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      ),

      // IconTheme default
      iconTheme: const IconThemeData(
        color: EcoColors.onSurfaceVariant,
        size: 24,
      ),

      // PrimaryIconTheme
      primaryIconTheme: const IconThemeData(
        color: EcoColors.onPrimary,
        size: 24,
      ),

      // Platform overrides
      platform: TargetPlatform.windows,
    );
  }

  /// TextTheme tipográfico — JetBrains Mono para código, Inter para UI
  static TextTheme _textTheme(ColorScheme scheme) {
    const String fontFamilyUI = 'Inter';
    const String fontFamilyMono = 'JetBrainsMono';

    return TextTheme(
      // Display — títulos grandes
      displayLarge: TextStyle(
        fontFamily: fontFamilyUI,
        fontSize: 57,
        fontWeight: FontWeight.w700,
        letterSpacing: -0.25,
        height: 1.12,
        color: scheme.onSurface,
      ),
      displayMedium: TextStyle(
        fontFamily: fontFamilyUI,
        fontSize: 45,
        fontWeight: FontWeight.w700,
        letterSpacing: 0,
        height: 1.16,
        color: scheme.onSurface,
      ),
      displaySmall: TextStyle(
        fontFamily: fontFamilyUI,
        fontSize: 36,
        fontWeight: FontWeight.w600,
        letterSpacing: 0,
        height: 1.22,
        color: scheme.onSurface,
      ),

      // Headline — seções
      headlineLarge: TextStyle(
        fontFamily: fontFamilyUI,
        fontSize: 32,
        fontWeight: FontWeight.w600,
        letterSpacing: 0,
        height: 1.25,
        color: scheme.onSurface,
      ),
      headlineMedium: TextStyle(
        fontFamily: fontFamilyUI,
        fontSize: 28,
        fontWeight: FontWeight.w600,
        letterSpacing: 0,
        height: 1.29,
        color: scheme.onSurface,
      ),
      headlineSmall: TextStyle(
        fontFamily: fontFamilyUI,
        fontSize: 24,
        fontWeight: FontWeight.w600,
        letterSpacing: 0,
        height: 1.33,
        color: scheme.onSurface,
      ),

      // Title — cards, listas
      titleLarge: TextStyle(
        fontFamily: fontFamilyUI,
        fontSize: 22,
        fontWeight: FontWeight.w600,
        letterSpacing: 0,
        height: 1.27,
        color: scheme.onSurface,
      ),
      titleMedium: TextStyle(
        fontFamily: fontFamilyUI,
        fontSize: 16,
        fontWeight: FontWeight.w500,
        letterSpacing: 0.15,
        height: 1.5,
        color: scheme.onSurface,
      ),
      titleSmall: TextStyle(
        fontFamily: fontFamilyUI,
        fontSize: 14,
        fontWeight: FontWeight.w500,
        letterSpacing: 0.1,
        height: 1.43,
        color: scheme.onSurface,
      ),

      // Body — texto corrido
      bodyLarge: TextStyle(
        fontFamily: fontFamilyUI,
        fontSize: 16,
        fontWeight: FontWeight.w400,
        letterSpacing: 0.5,
        height: 1.5,
        color: scheme.onSurface,
      ),
      bodyMedium: TextStyle(
        fontFamily: fontFamilyUI,
        fontSize: 14,
        fontWeight: FontWeight.w400,
        letterSpacing: 0.25,
        height: 1.43,
        color: scheme.onSurface,
      ),
      bodySmall: TextStyle(
        fontFamily: fontFamilyUI,
        fontSize: 12,
        fontWeight: FontWeight.w400,
        letterSpacing: 0.4,
        height: 1.33,
        color: scheme.onSurfaceVariant,
      ),

      // Label — botões, chips, tabs
      labelLarge: TextStyle(
        fontFamily: fontFamilyUI,
        fontSize: 14,
        fontWeight: FontWeight.w500,
        letterSpacing: 0.1,
        height: 1.43,
        color: scheme.onSurface,
      ),
      labelMedium: TextStyle(
        fontFamily: fontFamilyUI,
        fontSize: 12,
        fontWeight: FontWeight.w500,
        letterSpacing: 0.5,
        height: 1.33,
        color: scheme.onSurface,
      ),
      labelSmall: TextStyle(
        fontFamily: fontFamilyUI,
        fontSize: 11,
        fontWeight: FontWeight.w500,
        letterSpacing: 0.5,
        height: 1.45,
        color: scheme.onSurface,
      ),

      // Mono — logs, código, IDs
      // Usar via: style: EcoTheme.monoStyle
      // bodyMedium.copyWith(fontFamily: fontFamilyMono, fontFeatures: [FontFeature.tabularFigures()])
    );
  }

  /// Estilo monoespaçado para logs, IDs, código
  static TextStyle monoStyle({Color? color, double? fontSize}) => TextStyle(
    fontFamily: 'JetBrainsMono',
    fontSize: fontSize ?? 12,
    fontWeight: FontWeight.w400,
    letterSpacing: 0,
    height: 1.5,
    color: color ?? EcoColors.onSurfaceVariant,
  ).copyWith(fontFeatures: const [FontFeature.tabularFigures()]);
}