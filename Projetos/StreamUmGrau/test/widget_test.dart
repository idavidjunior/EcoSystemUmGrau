// Smoke test: garante que o app inicializa sem crash (usa dados mock,
// pois o Supabase nao esta configurado no ambiente de testes).
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:stream_um_grau/core/services/favoritos_service.dart';
import 'package:stream_um_grau/core/services/mock_midia_repository.dart';
import 'package:stream_um_grau/main.dart';

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
}
