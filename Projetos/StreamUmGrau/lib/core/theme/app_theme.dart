import 'package:flutter/material.dart';

/// Paleta e tema escuro padrao do catalogo de streaming.
class AppColors {
  AppColors._();

  static const Color background = Color(0xFF0E0E11); // fundo principal (quase preto)
  static const Color surface = Color(0xFF16161B); // cards / superficies
  static const Color surfaceAlt = Color(0xFF1E1E24); // elevacao leve
  static const Color accent = Color(0xFFE50914); // vermelho streaming
  static const Color textPrimary = Color(0xFFF5F5F5);
  static const Color textSecondary = Color(0xFF9E9EA7);
}

/// Tema escuro unico do aplicativo.
class AppTheme {
  AppTheme._();

  static ThemeData get dark {
    final base = ThemeData.dark(useMaterial3: true);
    return base.copyWith(
      scaffoldBackgroundColor: AppColors.background,
      colorScheme: base.colorScheme.copyWith(
        primary: AppColors.accent,
        secondary: AppColors.accent,
        surface: AppColors.surface,
        background: AppColors.background,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: AppColors.background,
        elevation: 0,
        centerTitle: false,
        titleTextStyle: TextStyle(
          color: AppColors.textPrimary,
          fontSize: 20,
          fontWeight: FontWeight.bold,
        ),
      ),
      textTheme: base.textTheme.apply(
        bodyColor: AppColors.textPrimary,
        displayColor: AppColors.textPrimary,
      ),
      dividerTheme: const DividerThemeData(color: AppColors.surfaceAlt),
    );
  }
}
