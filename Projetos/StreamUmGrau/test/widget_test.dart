// Smoke test: garante que o app inicializa sem crash (usa dados mock,
// pois o Supabase nao esta configurado no ambiente de testes).
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:stream_um_grau/core/services/favoritos_service.dart';
import 'package:stream_um_grau/core/services/mock_midia_repository.dart';
import 'package:stream_um_grau/main.dart';
import 'package:stream_um_grau/models/midia_model.dart';
import 'package:stream_um_grau/views/detail_view.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  testWidgets('App inicia sem crash e renderiza o catalogo mock',
      (WidgetTester tester) async {
    await FavoritosService.instance.init();
    await tester.pumpWidget(const StreamUmGrauApp());
    await tester.pumpAndSettle();

    expect(find.text('StreamUmGrau'), findsOneWidget);
  });

  test('Mock espelhado carrega o catalogo real completo (61 obras)',
      () async {
    final midias = await const MockMidiaRepository().fetchMidias();

    expect(midias, hasLength(61));
    final tipos = midias.map((m) => m.tipo).toSet();
    expect(tipos, containsAll(['filme', 'serie', 'dorama']));
    // IDs estaveis (UUID v5) e sem duplicidade.
    final ids = midias.map((m) => m.id).toList();
    expect(ids.toSet(), hasLength(61));
    // Favoritos nao podem quebrar se o espelho for regenerado:
    // nenhum id pode ser vazio.
    expect(ids.where((id) => id.isEmpty), isEmpty);
  });

  test('FavoritosService persiste e alterna por id', () async {
    final service = FavoritosService.instance;
    await service.init();

    expect(service.ehFavorito('id-1'), isFalse);
    await service.toggle('id-1');
    expect(service.ehFavorito('id-1'), isTrue);

    // Persistencia: um novo init carrega do disco.
    await service.init();
    expect(service.ehFavorito('id-1'), isTrue);

    await service.toggle('id-1');
    expect(service.ehFavorito('id-1'), isFalse);
  });

  testWidgets('DetailView exibe o botao "Assistir na TV" (ponte Web Video Cast)',
      (WidgetTester tester) async {
    const midia = Midia(
      id: 'teste-1',
      titulo: 'O Filme Teste',
      tipo: 'filme',
      categoria: 'Aventura',
      sinopse: 'Sinopse de teste.',
      capaUrl: '',
      bannerUrl: '',
      ano: 2024,
      idiomaTipo: 'LEG',
      classificacaoEtaria: 12,
    );

    await tester.pumpWidget(
      const MaterialApp(home: DetailView(midia: midia)),
    );
    await tester.pumpAndSettle();

    // Botao principal de cast deve estar presente na ficha.
    expect(find.text('Assistir na TV'), findsOneWidget);
    expect(find.byIcon(Icons.cast), findsOneWidget);
  });

  testWidgets(
      'Botao "Assistir na TV" tenta abrir o Web Video Cast (via url_launcher)',
      (WidgetTester tester) async {
    const midia = Midia(
      id: 'teste-2',
      titulo: 'Outro Filme',
      tipo: 'serie',
      categoria: 'Drama',
      sinopse: 'Sinopse.',
      capaUrl: '',
      bannerUrl: '',
      ano: 2023,
      idiomaTipo: 'DUB',
      classificacaoEtaria: 14,
    );

    // Mock do canal do url_launcher para capturar a URL aberta pelo botao.
    const channel = MethodChannel('plugins.flutter.io/url_launcher');
    final urlsAbertas = <String>[];
    tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(
      channel,
      (call) async {
        if (call.method == 'canLaunch') return true;
        if (call.method == 'launch') {
          final args = call.arguments as Map<dynamic, dynamic>;
          urlsAbertas.add(args['url'] as String);
          return true;
        }
        return null;
      },
    );

    await tester.pumpWidget(
      const MaterialApp(home: DetailView(midia: midia)),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('Assistir na TV'));
    await tester.pumpAndSettle();

    // Sem videoUrl no catalogo, deve tentar abrir o app pelo pacote do WVC
    // (intent://) com fallback para a Play Store embutido.
    expect(urlsAbertas, isNotEmpty);
    expect(urlsAbertas.first, startsWith('intent:'));
    expect(
      urlsAbertas.first,
      contains('com.instantbits.cast.webvideo'),
    );
  });
}
