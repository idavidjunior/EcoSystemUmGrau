import 'package:supabase_flutter/supabase_flutter.dart';

import '../config/app_config.dart';
import '../../models/midia_model.dart';

/// Servico de acesso ao backend Supabase.
///
/// Centraliza a inicializacao do cliente e as consultas ao catalogo.
class SupabaseService {
  SupabaseService._();

  static final SupabaseService instance = SupabaseService._();

  /// Inicializa o Supabase (deve ser chamado antes do `runApp`).
  Future<void> init() async {
    await Supabase.initialize(
      url: AppConfig.supabaseUrl,
      anonKey: AppConfig.supabaseAnonKey,
    );
  }

  /// Retorna o cliente Supabase ativo.
  SupabaseClient get client => Supabase.instance.client;

  /// Busca todo o catalogo de midias da tabela `midias`.
  Future<List<Midia>> fetchMidias() async {
    final response = await client
        .from(AppConfig.midiasTable)
        .select()
        .order('titulo');

    return response
        .map((row) => Midia.fromJson(Map<String, dynamic>.from(row)))
        .toList();
  }

  /// Busca midias filtrando por tipo (filme, serie, dorama).
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
