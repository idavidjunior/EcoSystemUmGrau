import '../../models/midia_model.dart';

/// Contrato de acesso ao catalogo de midias.
///
/// Implementado por [SupabaseService] (dados reais) e por
/// [MockMidiaRepository] (dados locais para desenvolvimento).
abstract class MidiaRepository {
  /// Busca todo o catalogo de midias.
  Future<List<Midia>> fetchMidias();

  /// Busca midias filtrando por tipo (filme, serie, dorama).
  Future<List<Midia>> fetchMidiasPorTipo(String tipo);
}
