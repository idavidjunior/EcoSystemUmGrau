import 'package:flutter/material.dart';

import 'core/config/app_config.dart';
import 'core/services/favoritos_service.dart';
import 'core/services/supabase_service.dart';
import 'core/theme/app_theme.dart';
import 'views/home_view.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Favoritos locais (nao depende de rede).
  await FavoritosService.instance.init();

  // So inicializa o Supabase quando as credenciais reais estao presentes.
  // Com placeholders, o app usa o repositorio mock local.
  if (AppConfig.supabaseConfigurado) {
    await SupabaseService.instance.init();
  }

  runApp(const StreamUmGrauApp());
}

/// Raiz do aplicativo de catalogo de streaming.
class StreamUmGrauApp extends StatelessWidget {
  const StreamUmGrauApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: AppConfig.appName,
      debugShowCheckedModeBanner: false,
      themeMode: ThemeMode.dark,
      theme: AppTheme.dark,
      home: const HomeView(),
    );
  }
}
