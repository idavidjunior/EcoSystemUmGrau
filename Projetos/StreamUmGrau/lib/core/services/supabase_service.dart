import 'package:supabase_flutter/supabase_flutter.dart';

import '../config/app_config.dart';
import '../../models/midia_model.dart';
import 'midia_repository.dart';

/// Servico de acesso ao backend Supabase.
///
/// Centraliza a inicializacao do cliente e as consultas ao catalogo.
class SupabaseService implements MidiaRepository {
  SupabaseService._();

  static final SupabaseService instance = SupabaseService._();

  /// Inicializa o Supabase (deve ser chamado antes do `runApp`).
  Future<void> init() async {
    await Supabase.initialize(
      url: AppConfig.supabaseUrl,
      publishableKey: AppConfig.supabaseAnonKey,
    );
  }

  /// Retorna o cliente Supabase ativo.
  SupabaseClient get client => Supabase.instance.client;

  @override
  Future<List<Midia>> fetchMidias() async {
    final response = await client
        .from(AppConfig.midiasTable)
        .select()
        .order('titulo');

    return response
        .map((row) => Midia.fromJson(Map<String, dynamic>.from(row)))
        .toList();
  }

  @override
  Future<List<Midia>> fetchMidiasPorTipo(String tipo) async {
    final response = await client
        .from(AppConfig.midiasTable)
        .select()
        .eq('tipo', tipo)
        .order('titulo');

    return response
        .map((row) => Midia.fromJson(Map<String, dynamic>.from(row)))
        .toList();
  }
}
