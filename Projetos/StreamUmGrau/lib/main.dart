import 'package:flutter/material.dart';

import 'core/services/supabase_service.dart';
import 'core/theme/app_theme.dart';
import 'views/home_view.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  await SupabaseService.instance.init();

  runApp(const StreamUmGrauApp());
}

/// Raiz do aplicativo de catalogo de streaming.
class StreamUmGrauApp extends StatelessWidget {
  const StreamUmGrauApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'StreamUmGrau',
      debugShowCheckedModeBanner: false,
      themeMode: ThemeMode.dark,
      theme: AppTheme.dark,
      home: const HomeView(),
    );
  }
}
