// Modelo FinancasState — dados reais de runtime/financas_snapshot.json
// Fontes: BCB SGS, AwesomeAPI, CoinGecko, Investidor10 (espelho B3)

/// Snapshot financeiro completo do ecossistema
class FinancasState {
  final MacroState? macro;
  final CambioState? cambio;
  final CryptoState? crypto;
  final IndicesState? indices;
  final TesouroState tesouro;
  final DateTime geradoEm;

  const FinancasState({
    required this.macro,
    required this.cambio,
    required this.crypto,
    required this.indices,
    required this.tesouro,
    required this.geradoEm,
  });

  factory FinancasState.fromJson(Map<String, dynamic> json) => FinancasState(
    macro: json['macro'] != null ? MacroState.fromJson(json['macro']) : null,
    cambio: json['cambio'] != null ? CambioState.fromJson(json['cambio']) : null,
    crypto: json['crypto'] != null ? CryptoState.fromJson(json['crypto']) : null,
    indices: json['indices'] != null ? IndicesState.fromJson(json['indices']) : null,
    tesouro: TesouroState.fromJson(json['tesouro'] ?? {}),
    geradoEm: DateTime.tryParse(json['gerado_em'] ?? '') ?? DateTime.now(),
  );

  bool get isEmpty => macro == null && cambio == null && crypto == null;
}

/// Selic, IPCA, CDI (BCB SGS)
class MacroState {
  final Indicador? selic;
  final Indicador? ipca12m;
  final double? cdiAnualizado;

  const MacroState({required this.selic, required this.ipca12m, required this.cdiAnualizado});

  factory MacroState.fromJson(Map<String, dynamic> json) => MacroState(
    selic: json['selic'] != null ? Indicador.fromJson(json['selic']) : null,
    ipca12m: json['ipca_12m'] != null ? Indicador.fromJson(json['ipca_12m']) : null,
    cdiAnualizado: (json['cdi_anualizado'] as num?)?.toDouble(),
  );
}

class Indicador {
  final double valor;
  final String data;
  final int serie;

  const Indicador({required this.valor, required this.data, required this.serie});

  factory Indicador.fromJson(Map<String, dynamic> json) => Indicador(
    valor: (json['valor'] as num?)?.toDouble() ?? 0,
    data: json['data'] ?? '',
    serie: json['serie'] ?? 0,
  );
}

/// Câmbio USD/BRL, EUR/BRL
class CambioState {
  final MoedaCotacao? usdBrl;
  final MoedaCotacao? eurBrl;

  const CambioState({required this.usdBrl, required this.eurBrl});

  factory CambioState.fromJson(Map<String, dynamic> json) => CambioState(
    usdBrl: json['usd_brl'] != null ? MoedaCotacao.fromJson(json['usd_brl']) : null,
    eurBrl: json['eur_brl'] != null ? MoedaCotacao.fromJson(json['eur_brl']) : null,
  );
}

class MoedaCotacao {
  final double bid;
  final double pctVariacao;
  final String? atualizado;

  const MoedaCotacao({required this.bid, required this.pctVariacao, this.atualizado});

  factory MoedaCotacao.fromJson(Map<String, dynamic> json) => MoedaCotacao(
    bid: (json['bid'] as num?)?.toDouble() ?? 0,
    pctVariacao: (json['pct_variacao'] as num?)?.toDouble() ?? 0,
    atualizado: json['atualizado'],
  );
}

/// BTC/ETH
class CryptoState {
  final CryptoAtivo? btc;
  final CryptoAtivo? eth;

  const CryptoState({required this.btc, required this.eth});

  factory CryptoState.fromJson(Map<String, dynamic> json) => CryptoState(
    btc: json['btc'] != null ? CryptoAtivo.fromJson(json['btc']) : null,
    eth: json['eth'] != null ? CryptoAtivo.fromJson(json['eth']) : null,
  );
}

class CryptoAtivo {
  final double? brl;
  final double? usd;
  final double variacao24hPct;

  const CryptoAtivo({required this.brl, required this.usd, required this.variacao24hPct});

  factory CryptoAtivo.fromJson(Map<String, dynamic> json) => CryptoAtivo(
    brl: (json['brl'] as num?)?.toDouble(),
    usd: (json['usd'] as num?)?.toDouble(),
    variacao24hPct: (json['variacao_24h_pct'] as num?)?.toDouble() ?? 0,
  );
}

/// IBOV, VIX
class IndicesState {
  final IndiceValor? ibov;
  final IndiceValor? vix;

  const IndicesState({required this.ibov, required this.vix});

  factory IndicesState.fromJson(Map<String, dynamic> json) => IndicesState(
    ibov: json['ibov'] != null ? IndiceValor.fromJson(json['ibov']) : null,
    vix: json['vix'] != null ? IndiceValor.fromJson(json['vix']) : null,
  );
}

class IndiceValor {
  final double? valor;
  final double? pctVariacao;

  const IndiceValor({this.valor, this.pctVariacao});

  factory IndiceValor.fromJson(Map<String, dynamic> json) => IndiceValor(
    valor: (json['valor'] as num?)?.toDouble(),
    pctVariacao: (json['pct_variacao'] as num?)?.toDouble(),
  );
}

/// Títulos do Tesouro Direto
class TesouroState {
  final String fonte;
  final bool aoVivo;
  final List<TituloTesouro> titulos;

  const TesouroState({required this.fonte, required this.aoVivo, required this.titulos});

  factory TesouroState.fromJson(Map<String, dynamic> json) => TesouroState(
    fonte: json['fonte'] ?? '',
    aoVivo: json['ao_vivo'] ?? false,
    titulos: (json['titulos'] as List? ?? []).map((e) => TituloTesouro.fromJson(e)).toList(),
  );

  /// Títulos acessíveis com capital pequeno (preço unitário ou fração <= R$200)
  List<TituloTesouro> get acessiveisAte200 =>
      titulos.where((t) => t.fracaoMinima <= 200 && t.precoUnitario > 0).toList();
}

class TituloTesouro {
  final String nome;
  final String indexador;
  final String tipoTaxa; // selic | selic_spread | prefixado | ipca
  final double? taxa;
  final String taxaTexto;
  final double precoUnitario;
  final String vencimento;

  const TituloTesouro({
    required this.nome,
    required this.indexador,
    required this.tipoTaxa,
    required this.taxa,
    required this.taxaTexto,
    required this.precoUnitario,
    required this.vencimento,
  });

  factory TituloTesouro.fromJson(Map<String, dynamic> json) => TituloTesouro(
    nome: json['nome'] ?? '',
    indexador: json['indexador'] ?? '',
    tipoTaxa: json['tipo_taxa'] ?? '',
    taxa: (json['taxa'] as num?)?.toDouble(),
    taxaTexto: json['taxa_texto'] ?? '',
    precoUnitario: (json['preco_unitario'] as num?)?.toDouble() ?? 0,
    vencimento: json['vencimento'] ?? '',
  );

  /// Fração mínima = 1% do preço unitário (regra Tesouro Direto),
  /// exceto quando o título inteiro custa menos que isso.
  double get fracaoMinima =>
      precoUnitario < 30 ? precoUnitario : (precoUnitario * 0.01);
}
