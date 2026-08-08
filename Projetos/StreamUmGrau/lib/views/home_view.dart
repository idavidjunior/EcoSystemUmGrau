import 'package:flutter/material.dart';

import '../core/config/app_config.dart';
import '../core/services/midia_repository.dart';
import '../core/services/mock_midia_repository.dart';
import '../core/services/supabase_service.dart';
import '../core/theme/app_theme.dart';
import '../models/midia_model.dart';
import '../widgets/midia_card.dart';
import 'detail_view.dart';

/// Tela inicial: catalogo de midias em grade de 2 colunas (tema escuro),
/// com busca por titulo e filtro por tipo.
class HomeView extends StatefulWidget {
  const HomeView({super.key});

  @override
  State<HomeView> createState() => _HomeViewState();
}

class _HomeViewState extends State<HomeView> {
  late final MidiaRepository _repository;
  List<Midia> _todas = const [];
  List<Midia> _exibidas = const [];
  bool _carregando = true;
  String? _erro;

  String _filtroTipo = 'todos';
  String _busca = '';

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
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _erro = e.toString();
        _carregando = false;
      });
    }
  }

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
    _exibidas = lista;
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(AppConfig.appName),
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
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 4, 16, 8),
            child: _CampoBusca(
              valor: _busca,
              onChanged: _onBusca,
            ),
          ),
          _BarraFiltros(
            selecionado: _filtroTipo,
            onSelecionado: _onTipoSelecionado,
          ),
          Expanded(child: _corpo()),
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
    if (_exibidas.isEmpty) {
      return _VazioView(
        temFiltro: _filtroTipo != 'todos' || _busca.isNotEmpty,
      );
    }
    return GridView.builder(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        crossAxisSpacing: 14,
        mainAxisSpacing: 16,
        childAspectRatio: 0.62,
      ),
      itemCount: _exibidas.length,
      itemBuilder: (context, index) {
        final midia = _exibidas[index];
        return MidiaCard(
          midia: midia,
          onTap: () => _abrirDetalhe(midia),
        );
      },
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

/// Barra horizontal de filtros por tipo.
class _BarraFiltros extends StatelessWidget {
  final String selecionado;
  final ValueChanged<String> onSelecionado;

  const _BarraFiltros({required this.selecionado, required this.onSelecionado});

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
        ],
      ),
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

/// Estado vazio: sem registros ou filtro sem resultados.
class _VazioView extends StatelessWidget {
  final bool temFiltro;

  const _VazioView({required this.temFiltro});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.video_library_outlined,
              size: 48, color: Colors.white24),
          const SizedBox(height: 12),
          Text(
            temFiltro
                ? 'Nenhum resultado para o filtro aplicado.'
                : 'Catálogo vazio\nAdicione mídias na tabela "midias" do Supabase.',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Colors.white54,
                ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}
