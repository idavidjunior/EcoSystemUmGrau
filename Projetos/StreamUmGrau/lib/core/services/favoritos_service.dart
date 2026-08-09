import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Servico de favoritos locais (sem login).
///
/// Persiste os IDs das midias favoritas no aparelho via [SharedPreferences]
/// e notifica ouvintes (ChangeNotifier) para a UI atualizar em tempo real.
class FavoritosService extends ChangeNotifier {
  FavoritosService._();

  static final FavoritosService instance = FavoritosService._();

  static const String _chave = 'favoritos_ids';

  Set<String> _ids = {};

  /// Conjunto de IDs favoritados (somente leitura).
  Set<String> get ids => Set.unmodifiable(_ids);

  /// Carrega os favoritos persistidos (chamar uma vez no boot).
  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    _ids = (prefs.getStringList(_chave) ?? const []).toSet();
    notifyListeners();
  }

  bool ehFavorito(String id) => _ids.contains(id);

  Future<void> toggle(String id) async {
    if (!_ids.add(id)) {
      _ids.remove(id);
    }
    await _persistir();
    notifyListeners();
  }

  Future<void> _persistir() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList(_chave, _ids.toList()..sort());
  }
}
