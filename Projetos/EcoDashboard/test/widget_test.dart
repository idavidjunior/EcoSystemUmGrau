// Testes do modelo financas_state.dart (dados reais do snapshot).
// Nota: o app completo depende de BridgeClient/WebSocket e não monta
// em ambiente de teste isolado — cobertura unitária focada no modelo.
import 'package:flutter_test/flutter_test.dart';
import 'package:eco_dashboard/models/financas_state.dart';

void main() {
  final json = <String, dynamic>{
    'gerado_em': '2026-08-21T12:00:00.000Z',
    'macro': {
      'selic': {'valor': 14.0, 'data': '16/09/2026', 'serie': 432},
      'ipca_12m': {'valor': 4.44, 'data': '01/08/2026', 'serie': 13522},
      'cdi_anualizado': 13.9,
    },
    'cambio': {
      'usd_brl': {'bid': 5.1951, 'pct_variacao': -0.12},
    },
    'crypto': {
      'btc': {'brl': 406638.0, 'usd': 72658.0, 'variacao_24h_pct': 9.51},
    },
    'tesouro': {
      'fonte': 'investidor10.com.br',
      'ao_vivo': true,
      'titulos': [
        {
          'nome': 'Tesouro Reserva 2036',
          'indexador': 'SELIC',
          'tipo_taxa': 'selic',
          'taxa': 14.00,
          'taxa_texto': 'SELIC',
          'preco_unitario': 10.90,
          'vencimento': '01/01/2036',
        },
        {
          'nome': 'Tesouro Selic 2031',
          'indexador': 'SELIC + 0,0732%',
          'tipo_taxa': 'selic_spread',
          'taxa': 0.0732,
          'taxa_texto': 'SELIC + 0,0732%',
          'preco_unitario': 19647.06,
          'vencimento': '01/03/2031',
        },
      ],
    },
  };

  test('FinancasState parses snapshot completo', () {
    final s = FinancasState.fromJson(json);
    expect(s.isEmpty, isFalse);
    expect(s.macro?.selic?.valor, 14.0);
    expect(s.macro?.ipca12m?.valor, 4.44);
    expect(s.macro?.cdiAnualizado, 13.9);
    expect(s.cambio?.usdBrl?.bid, 5.1951);
    expect(s.crypto?.btc?.brl, 406638.0);
    expect(s.tesouro.aoVivo, isTrue);
    expect(s.tesouro.titulos.length, 2);
  });

  test('Fração mínima: título barato = preço cheio; caro = 1%', () {
    final titulos = TesouroState.fromJson(json['tesouro'] as Map<String, dynamic>).titulos;
    // Reserva 2036 custa R$10,90 < R$30 -> fração = preço inteiro
    expect(titulos[0].fracaoMinima, closeTo(10.90, 0.001));
    // Selic 2031 custa R$19.647,06 -> fração = 1% ≈ R$196,47
    expect(titulos[1].fracaoMinima, closeTo(196.47, 0.01));
  });

  test('Filtro acessiveisAte200 inclui Reserva e Selic 2031 (fração R\$196)', () {
    final t = TesouroState.fromJson(json['tesouro'] as Map<String, dynamic>);
    final acessiveis = t.acessiveisAte200;
    // Ambos acessíveis: Reserva inteira (R$10,90) e fração do Selic 2031 (R$196,47)
    expect(acessiveis.length, 2);
    expect(acessiveis.map((e) => e.nome), contains(contains('Reserva')));
    expect(acessiveis.map((e) => e.nome), contains(contains('Selic 2031')));
  });

  test('FinancasState tolera JSON vazio', () {
    final s = FinancasState.fromJson({});
    expect(s.isEmpty, isTrue);
    expect(s.tesouro.titulos, isEmpty);
  });
}
