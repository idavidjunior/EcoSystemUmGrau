// EcoDashboard — Entry point Flutter Desktop
// Material 3 + Provider + WebSocket bridge

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'layout/eco_dashboard.dart';
import 'services/bridge_client.dart';
import 'theme/eco_theme.dart';

void main() {
  // Garante inicialização do Flutter
  WidgetsFlutterBinding.ensureInitialized();

  // Configurações de debug
  // debugPaintSizeEnabled = true;
  // debugRepaintRainbowEnabled = true;

  runApp(const EcoDashboardApp());
}

class EcoDashboardApp extends StatelessWidget {
  const EcoDashboardApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider<BridgeClientProvider>(
          create: (_) => BridgeClientProvider(
            host: const String.fromEnvironment('BRIDGE_HOST', defaultValue: 'localhost'),
            port: int.tryParse(const String.fromEnvironment('BRIDGE_PORT', defaultValue: '8765')) ?? 8765,
          ),
          lazy: false,
        ),
      ],
      child: MaterialApp(
        title: 'EcoSystemUmGrau Dashboard',
        debugShowCheckedModeBanner: false,
        theme: EcoTheme.dark,
        // Tema claro opcional (futuro)
        // lightTheme: EcoTheme.light,
        // themeMode: ThemeMode.system,
        home: const EcoDashboard(),
        // Configurações de janela desktop
        builder: (context, child) {
          return MediaQuery(
            data: MediaQuery.of(context).copyWith(
              // Escala de texto consistente
              textScaler: const TextScaler.linear(1.0),
            ),
            child: child!,
          );
        },
      ),
    );
  }
}