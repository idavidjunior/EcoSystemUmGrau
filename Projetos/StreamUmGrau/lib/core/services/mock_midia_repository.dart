import '../../models/midia_model.dart';
import 'midia_repository.dart';

/// Repositorio local com dados de exemplo, usado enquanto o Supabase
/// ainda nao foi configurado. Permite desenvolver e testar a interface
/// completa do catalogo sem backend.
class MockMidiaRepository implements MidiaRepository {
  static const List<Map<String, dynamic>> _seed = [
    {
      'id': '00000000-0000-0000-0000-000000000001',
      'titulo': 'Interestelar',
      'tipo': 'filme',
      'categoria': 'Ficção Científica',
      'sinopse':
          'Uma equipe de exploradores viaja por um buraco de minhoca no espaço '
          'em busca de um novo lar para a humanidade, guiados pelo amor que '
          'transcende o tempo e as dimensões.',
      'capa_url':
          'https://m.media-amazon.com/images/M/MV5BYzdjMDAxZGItMjI2My00ODA1LTlkNzItOWFjMDU5ZDJlYWY3XkEyXkFqcGc@._V1_QL75_UX380_CR0,0,380,562_.jpg',
      'banner_url':
          'https://m.media-amazon.com/images/M/MV5BYzdjMDAxZGItMjI2My00ODA1LTlkNzItOWFjMDU5ZDJlYWY3XkEyXkFqcGc@._V1_QL75_UX380_CR0,0,380,562_.jpg',
      'ano': 2014,
      'idioma_tipo': 'DUB',
      'classificacao_etaria': 10,
    },
    {
      'id': '00000000-0000-0000-0000-000000000002',
      'titulo': 'Breaking Bad',
      'tipo': 'serie',
      'categoria': 'Drama',
      'sinopse':
          'Um professor de química diagnosticado com câncer terminal começa a '
          'produzir metanfetamina para garantir o futuro financeiro da família.',
      'capa_url':
          'https://image.tmdb.org/t/p/w500/ggFHVNu6YYI5L9pCfOacjizRGt.jpg',
      'banner_url':
          'https://image.tmdb.org/t/p/w1280/5FiO4cTUyQHDw2jJQ4qAVMfNGJX.jpg',
      'ano': 2008,
      'idioma_tipo': 'LEG',
      'classificacao_etaria': 16,
    },
    {
      'id': '00000000-0000-0000-0000-000000000003',
      'titulo': 'Vagabond',
      'tipo': 'dorama',
      'categoria': 'Ação',
      'sinopse':
          'Um homem investiga a queda de um avião que envolve seu sobrinho e '
          'descobre uma conspiração muito maior por trás do acidente.',
      'capa_url':
          'https://static.tvmaze.com/uploads/images/original_untouched/211/529234.jpg',
      'banner_url':
          'https://static.tvmaze.com/uploads/images/original_untouched/211/529234.jpg',
      'ano': 2019,
      'idioma_tipo': 'DUAL',
      'classificacao_etaria': 16,
    },
    {
      'id': '00000000-0000-0000-0000-000000000004',
      'titulo': 'O Rei Leão',
      'tipo': 'filme',
      'categoria': 'Animação',
      'sinopse':
          'O leãozinho Simba foge de casa após a morte do pai e precisa '
          'encontrar coragem para assumir seu lugar como rei da savana.',
      'capa_url':
          'https://m.media-amazon.com/images/M/MV5BZGRiZDZhZjItM2M3ZC00Y2IyLTk3Y2MtMWY5YjliNDFkZTJlXkEyXkFqcGc@._V1_SX300.jpg',
      'banner_url':
          'https://m.media-amazon.com/images/M/MV5BZGRiZDZhZjItM2M3ZC00Y2IyLTk3Y2MtMWY5YjliNDFkZTJlXkEyXkFqcGc@._V1_SX300.jpg',
      'ano': 1994,
      'idioma_tipo': 'DUB',
      'classificacao_etaria': 0,
    },
    {
      'id': '00000000-0000-0000-0000-000000000005',
      'titulo': 'Pousando no Amor',
      'tipo': 'dorama',
      'categoria': 'Romance',
      'sinopse':
          'Uma herdeira sul-coreana cai de parapente na Coreia do Norte e '
          'encontra abrigo com um oficial que a ajuda a esconder sua origem.',
      'capa_url':
          'https://static.tvmaze.com/uploads/images/original_untouched/235/588087.jpg',
      'banner_url':
          'https://static.tvmaze.com/uploads/images/original_untouched/235/588087.jpg',
      'ano': 2019,
      'idioma_tipo': 'LEG',
      'classificacao_etaria': 12,
    },
    {
      'id': '00000000-0000-0000-0000-000000000006',
      'titulo': 'Stranger Things',
      'tipo': 'serie',
      'categoria': 'Sobrenatural',
      'sinopse':
          'O desaparecimento de um garoto na pequena Hawkins abre uma porta '
          'para um mundo paralelo cheio de mistérios e perigos.',
      'capa_url':
          'https://static.tvmaze.com/uploads/images/original_untouched/595/1489169.jpg',
      'banner_url':
          'https://static.tvmaze.com/uploads/images/original_untouched/595/1489169.jpg',
      'ano': 2016,
      'idioma_tipo': 'DUAL',
      'classificacao_etaria': 14,
    },
    {
      'id': '00000000-0000-0000-0000-000000000007',
      'titulo': 'Round 6',
      'tipo': 'serie',
      'categoria': 'Suspense',
      'sinopse':
          'Pessoas endividadas participam de jogos mortais infantis em troca '
          'de uma fortuna em dinheiro para o vencedor.',
      'capa_url':
          'https://image.tmdb.org/t/p/w500/dDlEmu3EZ0Pgg93K2SVNLCjCSvE.jpg',
      'banner_url':
          'https://image.tmdb.org/t/p/w1280/7HmNvs8SDsA8L1c0SMCY2M3QWZ4.jpg',
      'ano': 2021,
      'idioma_tipo': 'LEG',
      'classificacao_etaria': 16,
    },
    {
      'id': '00000000-0000-0000-0000-000000000008',
      'titulo': 'A Origem',
      'tipo': 'filme',
      'categoria': 'Ação',
      'sinopse':
          'Um ladrão especializado em invadir sonhos precisa realizar a '
          'inversão de um pensamento: plantar uma ideia na mente de um alvo.',
      'capa_url':
          'https://m.media-amazon.com/images/M/MV5BMjAxMzY3NjcxNF5BMl5BanBnXkFtZTcwNTI5OTM0Mw@@._V1_QL75_UX380_CR0,0,380,562_.jpg',
      'banner_url':
          'https://m.media-amazon.com/images/M/MV5BMjAxMzY3NjcxNF5BMl5BanBnXkFtZTcwNTI5OTM0Mw@@._V1_QL75_UX380_CR0,0,380,562_.jpg',
      'ano': 2010,
      'idioma_tipo': 'DUB',
      'classificacao_etaria': 12,
    },
  ];

  @override
  Future<List<Midia>> fetchMidias() async {
    await Future<void>.delayed(const Duration(milliseconds: 400));
    return _seed.map(Midia.fromJson).toList();
  }

  @override
  Future<List<Midia>> fetchMidiasPorTipo(String tipo) async {
    await Future<void>.delayed(const Duration(milliseconds: 400));
    return _seed
        .where((m) => m['tipo'] == tipo)
        .map(Midia.fromJson)
        .toList();
  }
}
