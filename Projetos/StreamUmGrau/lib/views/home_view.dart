import 'package:flutter/material.dart';

import '../core/config/app_config.dart';
import '../core/services/favoritos_service.dart';
import '../core/services/midia_repository.dart';
import '../core/services/mock_midia_repository.dart';
import '../core/services/supabase_service.dart';
import '../core/theme/app_theme.dart';
import '../models/midia_model.dart';
import '../widgets/midia_card.dart';
import 'detail_view.dart';

/// Tela inicial: catalogo de midias com busca, filtros (tipo/ano/categoria/
/// classificacao), secoes de destaque (Lancamentos e Populares) e aba
/// Favoritos (local, sem login).
class HomeView extends StatefulWidget {
  const HomeView({super.key});

  @override
  State<HomeView> createState() => _HomeViewState();
}

enum _Aba { catalogo, favoritos }

class _HomeViewState extends State<HomeView> {
  late final MidiaRepository _repository;
  List<Midia> _todas = const [];
  List<Midia> _exibidas = const [];
  bool _carregando = true;
  String? _erro;
  bool _usandoFallback = false;

  _Aba _aba = _Aba.catalogo;
  String _filtroTipo = 'todos';
  String _busca = '';

  // Filtros avancados.
  int? _anoMin;
  int? _anoMax;
  String? _categoria;
  int _idadeMax = 0; // 0 = sem limite

  @override
  void initState() {
    super.initState();
    _repository = AppConfig.usarMock
        ? MockMidiaRepository()
        : SupabaseService.instance;
    _carregar();
  }

  Future<void> _carregar() async {
    setState(() {
      _carregando = true;
      _erro = null;
    });
    try {
      final midias = await _repository.fetchMidias();
      if (!mounted) return;
      setState(() {
        _todas = midias;
        _aplicarFiltros();
        _carregando = false;
        _usandoFallback = false;
      });
    } catch (e) {
      // Fallback automatico: se o backend real falhar (sem rede, sem
      // credenciais), usa o espelho local do catalogo em vez de erro.
      try {
        final fallback = MockMidiaRepository();
        final midias = await fallback.fetchMidias();
        if (!mounted) return;
        setState(() {
          _todas = midias;
          _aplicarFiltros();
          _carregando = false;
          _erro = null;
          _usandoFallback = true;
        });
      } catch (fallbackErro) {
        if (!mounted) return;
        setState(() {
          _erro = e.toString();
          _carregando = false;
          _usandoFallback = false;
        });
      }
    }
  }

  List<String> get _categoriasDisponiveis {
    final set = <String>{};
    for (final m in _todas) {
      if (m.categoria.isNotEmpty) set.add(m.categoria);
    }
    final lista = set.toList()..sort();
    return lista;
  }

  int? get _anoMinimoDisponivel {
    final anos = _todas.map((m) => m.ano).where((a) => a > 0).toList();
    return anos.isEmpty ? null : anos.reduce((a, b) => a < b ? a : b);
  }

  int? get _anoMaximoDisponivel {
    final anos = _todas.map((m) => m.ano).where((a) => a > 0).toList();
    return anos.isEmpty ? null : anos.reduce((a, b) => a > b ? a : b);
  }

  bool get _temFiltroAvancado =>
      _anoMin != null || _anoMax != null || _categoria != null || _idadeMax > 0;

  void _aplicarFiltros() {
    var lista = _todas;
    if (_filtroTipo != 'todos') {
      lista = lista.where((m) => m.tipo == _filtroTipo).toList();
    }
    if (_busca.trim().isNotEmpty) {
      final q = _busca.trim().toLowerCase();
      lista = lista
          .where((m) => m.titulo.toLowerCase().contains(q))
          .toList();
    }
    if (_categoria != null) {
      lista = lista.where((m) => m.categoria == _categoria).toList();
    }
    if (_anoMin != null) {
      lista = lista.where((m) => m.ano >= _anoMin!).toList();
    }
    if (_anoMax != null) {
      lista = lista.where((m) => m.ano <= _anoMax!).toList();
    }
    if (_idadeMax > 0) {
      lista = lista.where((m) => m.classificacaoEtaria <= _idadeMax).toList();
    }
    _exibidas = lista;
  }

  List<Midia> get _lancamentos {
    final lista = _todas.where((m) => m.ano > 0).toList()
      ..sort((a, b) => b.ano.compareTo(a.ano));
    return lista.take(10).toList();
  }

  List<Midia> get _populares {
    final lista = _todas.toList()
      ..sort((a, b) => b.popularidade.compareTo(a.popularidade));
    return lista.take(10).toList();
  }

  List<Midia> get _favoritos {
    final ids = FavoritosService.instance.ids;
    return _todas.where((m) => ids.contains(m.id)).toList();
  }

  void _onTipoSelecionado(String tipo) {
    setState(() {
      _filtroTipo = tipo;
      _aplicarFiltros();
    });
  }

  void _onBusca(String valor) {
    setState(() {
      _busca = valor;
      _aplicarFiltros();
    });
  }

  Future<void> _abrirFiltros() async {
    final resultado = await showModalBottomSheet<_FiltroResultado>(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.surface,
      builder: (_) => _PainelFiltros(
        anoMinimo: _anoMinimoDisponivel ?? DateTime.now().year,
        anoMaximo: _anoMaximoDisponivel ?? DateTime.now().year,
        anoMin: _anoMin,
        anoMax: _anoMax,
        categoria: _categoria,
        categorias: _categoriasDisponiveis,
        idadeMax: _idadeMax,
      ),
    );
    if (resultado == null || !mounted) return;
    setState(() {
      _anoMin = resultado.anoMin;
      _anoMax = resultado.anoMax;
      _categoria = resultado.categoria;
      _idadeMax = resultado.idadeMax;
      _aplicarFiltros();
    });
  }

  void _limparFiltros() {
    setState(() {
      _anoMin = null;
      _anoMax = null;
      _categoria = null;
      _idadeMax = 0;
      _aplicarFiltros();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(AppConfig.appName),
        actions: [
          IconButton(
            onPressed: _carregando ? null : _carregar,
            tooltip: 'Atualizar',
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: Column(
        children: [
          _AbaSelector(
            aba: _aba,
            onSelecionada: (aba) => setState(() => _aba = aba),
          ),
          if (_aba == _Aba.catalogo) ...[
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 4, 16, 8),
              child: _CampoBusca(valor: _busca, onChanged: _onBusca),
            ),
            _BarraFiltros(
              selecionado: _filtroTipo,
              onSelecionado: _onTipoSelecionado,
              temFiltroAvancado: _temFiltroAvancado,
              onFiltros: _abrirFiltros,
              onLimpar: _limparFiltros,
            ),
          ],
          Expanded(child: _corpo()),
          if (_usandoFallback)
            Container(
              width: double.infinity,
              color: AppColors.surface,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
              child: Row(
                children: [
                  const Icon(Icons.cloud_off, size: 16, color: Colors.white54),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Offline — mostrando catálogo local',
                      style: Theme.of(context)
                          .textTheme
                          .bodySmall
                          ?.copyWith(color: Colors.white54),
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  Widget _corpo() {
    if (_carregando) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_erro != null) {
      return _ErroView(erro: _erro!, onRetry: _carregar);
    }

    if (_aba == _Aba.favoritos) {
      if (_favoritos.isEmpty) {
        return const _VazioView(
          mensagem:
              'Nenhum favorito ainda.\nToque no coração de uma obra para salvá-la aqui.',
        );
      }
      return _Grade(midias: _favoritos, onTap: _abrirDetalhe);
    }

    final temFiltroAtivo = _filtroTipo != 'todos' ||
        _busca.isNotEmpty ||
        _temFiltroAvancado;

    if (temFiltroAtivo) {
      if (_exibidas.isEmpty) {
        return const _VazioView(
          mensagem: 'Nenhum resultado para o filtro aplicado.',
        );
      }
      return _Grade(midias: _exibidas, onTap: _abrirDetalhe);
    }

    return CustomScrollView(
      slivers: [
        SliverToBoxAdapter(child: _SecaoHoriz(
          titulo: 'Lançamentos',
          midias: _lancamentos,
          onTap: _abrirDetalhe,
        )),
        SliverToBoxAdapter(child: _SecaoHoriz(
          titulo: 'Populares',
          midias: _populares,
          onTap: _abrirDetalhe,
        )),
        const SliverToBoxAdapter(child: _TituloSecao(titulo: 'Catálogo')),
        SliverPadding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
          sliver: SliverGrid(
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              crossAxisSpacing: 14,
              mainAxisSpacing: 16,
              childAspectRatio: 0.62,
            ),
            delegate: SliverChildBuilderDelegate(
              (context, index) {
                final midia = _exibidas[index];
                return MidiaCard(midia: midia, onTap: () => _abrirDetalhe(midia));
              },
              childCount: _exibidas.length,
            ),
          ),
        ),
      ],
    );
  }

  void _abrirDetalhe(Midia midia) {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => DetailView(midia: midia),
      ),
    );
  }
}

/// Grade 2 colunas reutilizavel (filtro e favoritos).
class _Grade extends StatelessWidget {
  final List<Midia> midias;
  final ValueChanged<Midia> onTap;

  const _Grade({required this.midias, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GridView.builder(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        crossAxisSpacing: 14,
        mainAxisSpacing: 16,
        childAspectRatio: 0.62,
      ),
      itemCount: midias.length,
      itemBuilder: (context, index) {
        final midia = midias[index];
        return MidiaCard(midia: midia, onTap: () => onTap(midia));
      },
    );
  }
}

/// Secao horizontal de destaque (Lancamentos / Populares).
class _SecaoHoriz extends StatelessWidget {
  final String titulo;
  final List<Midia> midias;
  final ValueChanged<Midia> onTap;

  const _SecaoHoriz({
    required this.titulo,
    required this.midias,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 4),
          child: Text(
            titulo,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w700,
                ),
          ),
        ),
        SizedBox(
          height: 210,
          child: ListView.builder(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16),
            itemCount: midias.length,
            itemBuilder: (context, index) {
              final midia = midias[index];
              return Padding(
                padding: const EdgeInsets.only(right: 12),
                child: SizedBox(
                  width: 120,
                  child: MidiaCard(midia: midia, onTap: () => onTap(midia)),
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}

class _TituloSecao extends StatelessWidget {
  final String titulo;

  const _TituloSecao({required this.titulo});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 20, 16, 4),
      child: Text(
        titulo,
        style: Theme.of(context).textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.w700,
            ),
      ),
    );
  }
}

/// Alternancia de aba: Catalogo / Favoritos.
class _AbaSelector extends StatelessWidget {
  final _Aba aba;
  final ValueChanged<_Aba> onSelecionada;

  const _AbaSelector({required this.aba, required this.onSelecionada});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 4),
      child: Row(
        children: [
          _botaoAba('Catálogo', _Aba.catalogo),
          const SizedBox(width: 8),
          ListenableBuilder(
            listenable: FavoritosService.instance,
            builder: (context, _) {
              final n = FavoritosService.instance.ids.length;
              return _botaoAba('Favoritos ($n)', _Aba.favoritos);
            },
          ),
        ],
      ),
    );
  }

  Widget _botaoAba(String rotulo, _Aba valor) {
    final selecionada = aba == valor;
    return Expanded(
      child: ChoiceChip(
        label: Text(rotulo),
        selected: selecionada,
        onSelected: (_) => onSelecionada(valor),
        selectedColor: AppColors.accent,
        backgroundColor: AppColors.surface,
        labelStyle: TextStyle(
          color: selecionada ? Colors.white : Colors.white70,
          fontWeight: FontWeight.w600,
        ),
        side: BorderSide.none,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      ),
    );
  }
}

/// Campo de busca por titulo.
class _CampoBusca extends StatelessWidget {
  final String valor;
  final ValueChanged<String> onChanged;

  const _CampoBusca({required this.valor, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return TextField(
      onChanged: onChanged,
      textInputAction: TextInputAction.search,
      style: const TextStyle(color: Colors.white),
      decoration: InputDecoration(
        hintText: 'Buscar por título...',
        hintStyle: const TextStyle(color: Colors.white38),
        prefixIcon: const Icon(Icons.search, color: Colors.white38),
        filled: true,
        fillColor: AppColors.surface,
        isDense: true,
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide.none,
        ),
      ),
    );
  }
}

/// Barra horizontal de filtros por tipo + botao de filtros avancados.
class _BarraFiltros extends StatelessWidget {
  final String selecionado;
  final ValueChanged<String> onSelecionado;
  final bool temFiltroAvancado;
  final VoidCallback onFiltros;
  final VoidCallback onLimpar;

  const _BarraFiltros({
    required this.selecionado,
    required this.onSelecionado,
    required this.temFiltroAvancado,
    required this.onFiltros,
    required this.onLimpar,
  });

  static const _filtros = <(String, String)>[
    ('todos', 'Todos'),
    ('filme', 'Filmes'),
    ('serie', 'Séries'),
    ('dorama', 'Doramas'),
  ];

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Row(
        children: [
          for (final (valor, rotulo) in _filtros)
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: ChoiceChip(
                label: Text(rotulo),
                selected: selecionado == valor,
                onSelected: (_) => onSelecionado(valor),
                selectedColor: AppColors.accent,
                backgroundColor: AppColors.surface,
                labelStyle: TextStyle(
                  color: selecionado == valor
                      ? Colors.white
                      : Colors.white70,
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                ),
                side: BorderSide.none,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(20),
                ),
              ),
            ),
          IconButton(
            onPressed: onFiltros,
            tooltip: 'Filtros avançados',
            icon: Icon(
              Icons.tune,
              color: temFiltroAvancado ? AppColors.accent : Colors.white70,
            ),
          ),
          if (temFiltroAvancado)
            TextButton.icon(
              onPressed: onLimpar,
              icon: const Icon(Icons.clear, size: 16),
              label: const Text('Limpar'),
            ),
        ],
      ),
    );
  }
}

/// Resultado do painel de filtros avançados.
class _FiltroResultado {
  final int? anoMin;
  final int? anoMax;
  final String? categoria;
  final int idadeMax;

  const _FiltroResultado({
    this.anoMin,
    this.anoMax,
    this.categoria,
    required this.idadeMax,
  });
}

/// Bottom sheet com filtros avancados (ano, categoria, classificacao etaria).
class _PainelFiltros extends StatefulWidget {
  final int anoMinimo;
  final int anoMaximo;
  final int? anoMin;
  final int? anoMax;
  final String? categoria;
  final List<String> categorias;
  final int idadeMax;

  const _PainelFiltros({
    required this.anoMinimo,
    required this.anoMaximo,
    required this.anoMin,
    required this.anoMax,
    required this.categoria,
    required this.categorias,
    required this.idadeMax,
  });

  @override
  State<_PainelFiltros> createState() => _PainelFiltrosState();
}

class _PainelFiltrosState extends State<_PainelFiltros> {
  late RangeValues _faixaAno;
  String? _categoria;
  late int _idadeMax;
  bool _usarFaixaAno = false;

  @override
  void initState() {
    super.initState();
    final lo = widget.anoMin ?? widget.anoMinimo;
    final hi = widget.anoMax ?? widget.anoMaximo;
    _usarFaixaAno = widget.anoMin != null || widget.anoMax != null;
    _faixaAno = RangeValues(lo.toDouble(), hi.toDouble());
    _categoria = widget.categoria;
    _idadeMax = widget.idadeMax;
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        left: 16,
        right: 16,
        top: 16,
        bottom: MediaQuery.of(context).viewInsets.bottom + 16,
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: Colors.white24,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 16),
            Text(
              'Filtros avançados',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
            ),
            const SizedBox(height: 16),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('Por ano'),
              value: _usarFaixaAno,
              activeTrackColor: AppColors.accent,
              onChanged: (v) => setState(() => _usarFaixaAno = v),
            ),
            if (_usarFaixaAno) ...[
              RangeSlider(
                values: _faixaAno,
                min: widget.anoMinimo.toDouble(),
                max: widget.anoMaximo.toDouble(),
                divisions: widget.anoMaximo - widget.anoMinimo > 0
                    ? widget.anoMaximo - widget.anoMinimo
                    : 1,
                activeColor: AppColors.accent,
                inactiveColor: Colors.white24,
                labels: RangeLabels(
                  '${_faixaAno.start.round()}',
                  '${_faixaAno.end.round()}',
                ),
                onChanged: (v) => setState(() => _faixaAno = v),
              ),
              Center(
                child: Text(
                  '${_faixaAno.start.round()} — ${_faixaAno.end.round()}',
                  style: const TextStyle(color: Colors.white70),
                ),
              ),
            ],
            const SizedBox(height: 12),
            Text(
              'Categoria',
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _chipCategoria(null, 'Todas'),
                for (final c in widget.categorias) _chipCategoria(c, c),
              ],
            ),
            const SizedBox(height: 16),
            Text(
              'Classificação etária máxima',
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: 4),
            SegmentedButton<int>(
              segments: const [
                ButtonSegment(value: 0, label: Text('Todas')),
                ButtonSegment(value: 10, label: Text('10')),
                ButtonSegment(value: 12, label: Text('12')),
                ButtonSegment(value: 14, label: Text('14')),
                ButtonSegment(value: 16, label: Text('16')),
                ButtonSegment(value: 18, label: Text('18')),
              ],
              selected: {_idadeMax},
              onSelectionChanged: (s) => setState(() => _idadeMax = s.first),
              style: const ButtonStyle(
                visualDensity: VisualDensity.compact,
              ),
            ),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: () => Navigator.of(context).pop(
                  _FiltroResultado(
                    anoMin: _usarFaixaAno ? _faixaAno.start.round() : null,
                    anoMax: _usarFaixaAno ? _faixaAno.end.round() : null,
                    categoria: _categoria,
                    idadeMax: _idadeMax,
                  ),
                ),
                child: const Text('Aplicar filtros'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _chipCategoria(String? valor, String rotulo) {
    final selecionada = _categoria == valor;
    return ChoiceChip(
      label: Text(rotulo),
      selected: selecionada,
      onSelected: (_) => setState(() => _categoria = valor),
      selectedColor: AppColors.accent,
      backgroundColor: Colors.transparent,
      labelStyle: TextStyle(
        color: selecionada ? Colors.white : Colors.white70,
        fontSize: 12,
      ),
      side: BorderSide(
        color: selecionada ? AppColors.accent : Colors.white24,
      ),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
    );
  }
}

/// Estado de erro com botao de tentar novamente.
class _ErroView extends StatelessWidget {
  final String erro;
  final VoidCallback onRetry;

  const _ErroView({required this.erro, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.cloud_off, size: 48, color: Colors.white24),
            const SizedBox(height: 12),
            Text(
              'Não foi possível carregar o catálogo',
              style: Theme.of(context).textTheme.titleMedium,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              erro,
              style: Theme.of(context)
                  .textTheme
                  .bodySmall
                  ?.copyWith(color: Colors.white54),
              textAlign: TextAlign.center,
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: const Text('Tentar novamente'),
            ),
          ],
        ),
      ),
    );
  }
}

/// Estado vazio.
class _VazioView extends StatelessWidget {
  final String mensagem;

  const _VazioView({required this.mensagem});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.video_library_outlined,
                size: 48, color: Colors.white24),
            const SizedBox(height: 12),
            Text(
              mensagem,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Colors.white54,
                  ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
