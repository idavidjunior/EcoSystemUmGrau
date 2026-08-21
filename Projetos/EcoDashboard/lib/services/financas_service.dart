// Serviço FinancasService — lê runtime/financas_snapshot.json (dados reais)
// Refresh periódico a cada 5 minutos; fail-soft se arquivo ausente/corrompido

import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import '../models/financas_state.dart';

class FinancasService extends ChangeNotifier {
  /// Caminho padrão: repositório irmão EcoSystemUmGrau
  static const String defaultPath =
      r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\runtime\financas_snapshot.json';

  final String path;
  final Duration refreshInterval;
  Timer? _timer;
  bool _disposed = false;

  FinancasState? _state;
  FinancasState? get state => _state;

  DateTime? _lastLoad;
  DateTime? get lastLoad => _lastLoad;

  String? _error;
  String? get error => _error;

  FinancasService({this.path = defaultPath, this.refreshInterval = const Duration(minutes: 5)});

  void start() {
    load();
    _timer?.cancel();
    _timer = Timer.periodic(refreshInterval, (_) => load());
  }

  Future<void> load() async {
    if (_disposed) return;
    try {
      final file = File(path);
      if (!await file.exists()) {
        _error = 'Snapshot não encontrado: $path';
        notifyListeners();
        return;
      }
      final raw = await file.readAsString();
      final json = jsonDecode(raw) as Map<String, dynamic>;
      _state = FinancasState.fromJson(json);
      _lastLoad = DateTime.now();
      _error = null;
    } catch (e) {
      _error = 'Erro ao carregar snapshot: $e';
    }
    if (!_disposed) notifyListeners();
  }

  @override
  void dispose() {
    _disposed = true;
    _timer?.cancel();
    super.dispose();
  }
}
