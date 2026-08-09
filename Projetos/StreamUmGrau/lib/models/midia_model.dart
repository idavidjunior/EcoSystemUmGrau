/// Tipos de midia suportados pelo catalogo.
enum TipoMidia { filme, serie, dorama, desconhecido }

/// Formatos de idioma da midia.
enum IdiomaTipo { dub, leg, dual, desconhecido }

/// Modelo que mapeia a tabela `midias` do Supabase.
///
/// Colunas da tabela:
/// - id                 (UUID, chave primaria)
/// - titulo             (Texto)
/// - tipo               (Texto: filme, serie, dorama)
/// - categoria          (Texto)
/// - sinopse            (Texto)
/// - capa_url           (Texto)
/// - banner_url         (Texto)
/// - ano                (Inteiro)
/// - idioma_tipo        (Texto: DUB, LEG, DUAL)
/// - classificacao_etaria (Inteiro)
/// - popularidade       (Inteiro 0-100, rank para 'Populares')
class Midia {
  final String id;
  final String titulo;
  final String tipo;
  final String categoria;
  final String sinopse;
  final String capaUrl;
  final String bannerUrl;
  final int ano;
  final String idiomaTipo;
  final int classificacaoEtaria;
  final int popularidade;

  const Midia({
    required this.id,
    required this.titulo,
    required this.tipo,
    required this.categoria,
    required this.sinopse,
    required this.capaUrl,
    required this.bannerUrl,
    required this.ano,
    required this.idiomaTipo,
    required this.classificacaoEtaria,
    this.popularidade = 0,
  });

  /// Converte o enum [TipoMidia] para o valor armazenado no banco.
  static String tipoParaString(TipoMidia tipo) {
    switch (tipo) {
      case TipoMidia.filme:
        return 'filme';
      case TipoMidia.serie:
        return 'serie';
      case TipoMidia.dorama:
        return 'dorama';
      case TipoMidia.desconhecido:
        return '';
    }
  }

  /// Converte o enum [IdiomaTipo] para o valor armazenado no banco.
  static String idiomaParaString(IdiomaTipo idioma) {
    switch (idioma) {
      case IdiomaTipo.dub:
        return 'DUB';
      case IdiomaTipo.leg:
        return 'LEG';
      case IdiomaTipo.dual:
        return 'DUAL';
      case IdiomaTipo.desconhecido:
        return '';
    }
  }

  /// Converte um registro do Supabase (Map) em [Midia].
  factory Midia.fromJson(Map<String, dynamic> json) {
    return Midia(
      id: json['id']?.toString() ?? '',
      titulo: json['titulo']?.toString() ?? '',
      tipo: json['tipo']?.toString() ?? '',
      categoria: json['categoria']?.toString() ?? '',
      sinopse: json['sinopse']?.toString() ?? '',
      capaUrl: json['capa_url']?.toString() ?? '',
      bannerUrl: json['banner_url']?.toString() ?? '',
      ano: _parseInt(json['ano']) ?? 0,
      idiomaTipo: json['idioma_tipo']?.toString() ?? '',
      classificacaoEtaria: _parseInt(json['classificacao_etaria']) ?? 0,
      popularidade: _parseInt(json['popularidade']) ?? 0,
    );
  }

  /// Converte [Midia] em um registro (Map) pronto para o Supabase.
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'titulo': titulo,
      'tipo': tipo,
      'categoria': categoria,
      'sinopse': sinopse,
      'capa_url': capaUrl,
      'banner_url': bannerUrl,
      'ano': ano,
      'idioma_tipo': idiomaTipo,
      'classificacao_etaria': classificacaoEtaria,
      'popularidade': popularidade,
    };
  }

  /// Cria uma copia com campos alterados.
  Midia copyWith({
    String? id,
    String? titulo,
    String? tipo,
    String? categoria,
    String? sinopse,
    String? capaUrl,
    String? bannerUrl,
    int? ano,
    String? idiomaTipo,
    int? classificacaoEtaria,
    int? popularidade,
  }) {
    return Midia(
      id: id ?? this.id,
      titulo: titulo ?? this.titulo,
      tipo: tipo ?? this.tipo,
      categoria: categoria ?? this.categoria,
      sinopse: sinopse ?? this.sinopse,
      capaUrl: capaUrl ?? this.capaUrl,
      bannerUrl: bannerUrl ?? this.bannerUrl,
      ano: ano ?? this.ano,
      idiomaTipo: idiomaTipo ?? this.idiomaTipo,
      classificacaoEtaria: classificacaoEtaria ?? this.classificacaoEtaria,
      popularidade: popularidade ?? this.popularidade,
    );
  }

  /// Tipo normalizado para comparacoes (ex.: 'Filme').
  String get tipoFormatado => _capitalizar(tipo);

  /// Idioma normalizado (ex.: 'DUB').
  String get idiomaFormatado => idiomaTipo.toUpperCase();

  /// Tag composta exibida nos cards: "FILME • DUB" ou "SERIE • LEG".
  String get tagFormato =>
      '${tipoFormatado.toUpperCase()} • $idiomaFormatado';

  bool get temCapa => capaUrl.isNotEmpty;
  bool get temBanner => bannerUrl.isNotEmpty;

  static int? _parseInt(dynamic value) {
    if (value is int) return value;
    if (value is num) return value.toInt();
    if (value is String && value.isNotEmpty) return int.tryParse(value);
    return null;
  }

  static String _capitalizar(String valor) {
    if (valor.isEmpty) return valor;
    return valor[0].toUpperCase() + valor.substring(1).toLowerCase();
  }
}
