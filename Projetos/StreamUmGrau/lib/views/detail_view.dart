import 'package:flutter/material.dart';

import '../core/services/favoritos_service.dart';
import '../core/services/web_video_cast_bridge.dart';
import '../core/theme/app_theme.dart';
import '../models/midia_model.dart';

/// Tela de detalhes de uma midia: banner, titulo, tags e sinopse.
class DetailView extends StatelessWidget {
  final Midia midia;

  const DetailView({super.key, required this.midia});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: CustomScrollView(
        slivers: [
          SliverAppBar(
            expandedHeight: 280,
            pinned: true,
            backgroundColor: AppColors.background,
            leading: const BackButton(color: Colors.white),
            actions: [
              ListenableBuilder(
                listenable: FavoritosService.instance,
                builder: (context, _) {
                  final ehFavorito =
                      FavoritosService.instance.ehFavorito(midia.id);
                  return IconButton(
                    onPressed: () => FavoritosService.instance.toggle(midia.id),
                    tooltip: ehFavorito ? 'Remover dos favoritos' : 'Favoritar',
                    icon: Icon(
                      ehFavorito ? Icons.favorite : Icons.favorite_border,
                      color: ehFavorito ? Colors.redAccent : Colors.white,
                    ),
                  );
                },
              ),
            ],
            flexibleSpace: FlexibleSpaceBar(
              background: _Banner(midia: midia),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
            sliver: SliverList(
              delegate: SliverChildListDelegate([
                Text(
                  midia.titulo,
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
                const SizedBox(height: 10),
                _InfoRow(midia: midia),
                const SizedBox(height: 20),
                _BotaoAssistirNaTv(titulo: midia.titulo),
                const SizedBox(height: 24),
                Text(
                  'Sinopse',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                ),
                const SizedBox(height: 8),
                Text(
                  midia.sinopse.isNotEmpty
                      ? midia.sinopse
                      : 'Sinopse não disponível para esta obra.',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: Colors.white70,
                        height: 1.5,
                      ),
                ),
                if (midia.temBanner) ...[
                  const SizedBox(height: 28),
                  Text(
                    'Banner',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.w600,
                        ),
                  ),
                  const SizedBox(height: 10),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(12),
                    child: Image.network(
                      midia.bannerUrl,
                      height: 160,
                      width: double.infinity,
                      fit: BoxFit.cover,
                      errorBuilder: (context, error, stackTrace) =>
                          const _BannerFundo(),
                    ),
                  ),
                ],
              ]),
            ),
          ),
        ],
      ),
    );
  }
}

/// Banner superior com gradiente escuro para legibilidade.
class _Banner extends StatelessWidget {
  final Midia midia;

  const _Banner({required this.midia});

  @override
  Widget build(BuildContext context) {
    return Stack(
      fit: StackFit.expand,
      children: [
        if (midia.temBanner)
          Image.network(
            midia.bannerUrl,
            fit: BoxFit.cover,
            errorBuilder: (context, error, stackTrace) => const _BannerFundo(),
          )
        else
          const _BannerFundo(),
        const DecoratedBox(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [Colors.transparent, AppColors.background],
              stops: [0.5, 1.0],
            ),
          ),
        ),
      ],
    );
  }
}

class _BannerFundo extends StatelessWidget {
  const _BannerFundo();

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.surface,
      child: const Icon(Icons.movie_outlined, size: 72, color: Colors.white24),
    );
  }
}

/// Linha de metadados: tipo • ano • classificação etária • categoria.
class _InfoRow extends StatelessWidget {
  final Midia midia;

  const _InfoRow({required this.midia});

  @override
  Widget build(BuildContext context) {
    final chips = <Widget>[
      _ChipInfo(rotulo: '${midia.ano}'),
      const SizedBox(width: 8),
      _ChipInfo(rotulo: midia.tagFormato),
    ];
    if (midia.classificacaoEtaria > 0) {
      chips
        ..add(const SizedBox(width: 8))
        ..add(_ChipInfo(rotulo: '${midia.classificacaoEtaria} anos'));
    }
    if (midia.categoria.isNotEmpty) {
      chips
        ..add(const SizedBox(width: 8))
        ..add(_ChipInfo(rotulo: midia.categoria));
    }
    if (midia.popularidade > 0) {
      chips
        ..add(const SizedBox(width: 8))
        ..add(_ChipInfo(rotulo: '★ ${midia.popularidade}'));
    }
    return Wrap(spacing: 0, runSpacing: 8, children: chips);
  }
}

class _ChipInfo extends StatelessWidget {
  final String rotulo;

  const _ChipInfo({required this.rotulo});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: AppColors.surfaceAlt,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        rotulo,
        style: const TextStyle(color: Colors.white, fontSize: 12),
      ),
    );
  }
}

/// Botao principal que delega ao Web Video Cast o envio da obra para a TV.
class _BotaoAssistirNaTv extends StatelessWidget {
  final String titulo;

  const _BotaoAssistirNaTv({required this.titulo});

  Future<void> _assistir(BuildContext context) async {
    final messenger = ScaffoldMessenger.of(context);
    final abriu = await WebVideoCastBridge.assistirNaTv(titulo: titulo);
    if (!abriu) {
      messenger.showSnackBar(
        const SnackBar(
          content: Text('Não foi possível abrir o Web Video Cast.'),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      height: 48,
      child: FilledButton.icon(
        onPressed: () => _assistir(context),
        icon: const Icon(Icons.cast),
        label: const Text(
          'Assistir na TV',
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
        ),
      ),
    );
  }
}
