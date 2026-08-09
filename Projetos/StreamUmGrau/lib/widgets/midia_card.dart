import 'package:flutter/material.dart';

import '../core/services/favoritos_service.dart';
import '../models/midia_model.dart';

/// Card vertical do catalogo: capa arredondada, titulo e tags.
class MidiaCard extends StatelessWidget {
  final Midia midia;
  final VoidCallback? onTap;

  const MidiaCard({
    super.key,
    required this.midia,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: Stack(
                fit: StackFit.expand,
                children: [
                  _Capa(midia: midia),
                  _BotaoFavorito(midia: midia),
                ],
              ),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            midia.titulo,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: theme.textTheme.bodyMedium?.copyWith(
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 4),
          Row(
            children: [
              Expanded(
                child: _Tag(
                  texto: midia.tagFormato,
                  cor: _corTag(midia.tipo),
                ),
              ),
              const SizedBox(width: 6),
              Text(
                '${midia.ano}',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: Colors.white70,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Color _corTag(String tipo) {
    switch (tipo.toLowerCase()) {
      case 'filme':
        return Colors.redAccent;
      case 'serie':
        return Colors.blueAccent;
      case 'dorama':
        return Colors.pinkAccent;
      default:
        return Colors.grey;
    }
  }
}

/// Botao de coracao no canto superior direito da capa (favoritar/desfavoritar).
class _BotaoFavorito extends StatelessWidget {
  final Midia midia;

  const _BotaoFavorito({required this.midia});

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.topRight,
      child: ListenableBuilder(
        listenable: FavoritosService.instance,
        builder: (context, _) {
          final ehFavorito = FavoritosService.instance.ehFavorito(midia.id);
          return Material(
            color: Colors.black54,
            shape: const CircleBorder(),
            child: InkWell(
              customBorder: const CircleBorder(),
              onTap: () => FavoritosService.instance.toggle(midia.id),
              child: Padding(
                padding: const EdgeInsets.all(6),
                child: Icon(
                  ehFavorito ? Icons.favorite : Icons.favorite_border,
                  size: 18,
                  color: ehFavorito ? Colors.redAccent : Colors.white70,
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

/// Imagem de capa com fallback para quando a URL nao carrega.
class _Capa extends StatelessWidget {
  final Midia midia;

  const _Capa({required this.midia});

  @override
  Widget build(BuildContext context) {
    if (!midia.temCapa) return const _PlaceholderCapa();

    return Image.network(
      midia.capaUrl,
      fit: BoxFit.cover,
      loadingBuilder: (context, child, loadingProgress) {
        if (loadingProgress == null) return child;
        return const _PlaceholderCapa(loading: true);
      },
      errorBuilder: (context, error, stackTrace) =>
          const _PlaceholderCapa(loading: false),
    );
  }
}

class _PlaceholderCapa extends StatelessWidget {
  final bool loading;

  const _PlaceholderCapa({this.loading = false});

  @override
  Widget build(BuildContext context) {
    return Container(
      color: const Color(0xFF1E1E24),
      alignment: Alignment.center,
      child: loading
          ? const CircularProgressIndicator(
              strokeWidth: 2,
              color: Colors.grey,
            )
          : const Icon(
              Icons.movie_outlined,
              size: 40,
              color: Colors.white24,
            ),
    );
  }
}

class _Tag extends StatelessWidget {
  final String texto;
  final Color cor;

  const _Tag({required this.texto, required this.cor});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: cor.withValues(alpha: 0.18),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(
        texto,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
        style: TextStyle(
          color: cor,
          fontSize: 10,
          fontWeight: FontWeight.bold,
          letterSpacing: 0.3,
        ),
      ),
    );
  }
}
