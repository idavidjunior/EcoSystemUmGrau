import 'package:flutter/material.dart';

import '../core/services/supabase_service.dart';
import '../models/midia_model.dart';
import '../widgets/midia_card.dart';

/// Tela inicial: catalogo de midias em grade de 2 colunas (tema escuro).
class HomeView extends StatefulWidget {
  const HomeView({super.key});

  @override
  State<HomeView> createState() => _HomeViewState();
}

class _HomeViewState extends State<HomeView> {
  late Future<List<Midia>> _futureMidias;

  @override
  void initState() {
    super.initState();
    _futureMidias = SupabaseService.instance.fetchMidias();
  }

  void _recarregar() {
    setState(() {
      _futureMidias = SupabaseService.instance.fetchMidias();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Catálogo'),
        actions: [
          IconButton(
            onPressed: _recarregar,
            tooltip: 'Atualizar',
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: FutureBuilder<List<Midia>>(
        future: _futureMidias,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return _ErroView(
              erro: snapshot.error.toString(),
              onRetry: _recarregar,
            );
          }
          final midias = snapshot.data ?? const [];
          if (midias.isEmpty) {
            return const _VazioView();
          }
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
              return MidiaCard(midia: midia);
            },
          );
        },
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

/// Estado exibido quando nao ha registros na tabela.
class _VazioView extends StatelessWidget {
  const _VazioView();

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
            'Catálogo vazio\nAdicione mídias na tabela "midias" do Supabase.',
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
