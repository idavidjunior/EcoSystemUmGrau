import 'package:url_launcher/url_launcher.dart';

/// Ponte para o app "Web Video Cast" (InstantBits) — envia video para a TV
/// (Chromecast/Roku/Fire TV/DLNA).
///
/// O StreamUmGrau nao embute reprodutor nem busca de fontes: apenas delega
/// para o Web Video Cast, que faz a ponte com a TV.
///
/// Integracao oficial: https://www.webvideocaster.com/integrations
class WebVideoCastBridge {
  WebVideoCastBridge._();

  static const String _package = 'com.instantbits.cast.webvideo';
  static const String _playStoreUrl =
      'https://play.google.com/store/apps/details?id=com.instantbits.cast.webvideo';

  /// Abre o Web Video Cast para assistir a obra na TV.
  ///
  /// Se [videoUrl] for informada, envia esse video direto ao WVC.
  /// Caso contrario (catalogo de metadados), abre o app para o usuario
  /// escolher a fonte/busca dentro do WVC.
  static Future<bool> assistirNaTv({
    String? titulo,
    String? videoUrl,
  }) async {
    // 1) Com URL de video: scheme oficial do WVC (funciona em Android/iOS).
    if (videoUrl != null && videoUrl.isNotEmpty) {
      final url = Uri.parse(
        'wvc-x-callback://open?url=${Uri.encodeComponent(videoUrl)}'
        '${titulo != null && titulo.isNotEmpty ? '&title=${Uri.encodeComponent(titulo)}' : ''}',
      );
      if (await _tryLaunch(url)) return true;
    }

    // 2) Sem URL (ou falha no scheme): abre o app do WVC diretamente pelo
    //    pacote Android (intent) para o usuario buscar a obra.
    if (await _tryLaunch(_appIntent())) return true;

    // 3) App nao instalado: leva para a Play Store.
    return launchUrl(
      Uri.parse(_playStoreUrl),
      mode: LaunchMode.externalApplication,
    );
  }

  /// Intent Android que abre o Web Video Cast pelo pacote.
  static Uri _appIntent() {
    final fallback = Uri.encodeComponent(_playStoreUrl);
    return Uri.parse(
      'intent:#Intent;'
      'action=android.intent.action.MAIN;'
      'category=android.intent.category.LAUNCHER;'
      'package=$_package;'
      'S.browser_fallback_url=$fallback;'
      'end',
    );
  }

  static Future<bool> _tryLaunch(Uri url) async {
    try {
      if (await canLaunchUrl(url)) {
        return await launchUrl(url, mode: LaunchMode.externalApplication);
      }
    } catch (_) {
      return false;
    }
    return false;
  }
}
