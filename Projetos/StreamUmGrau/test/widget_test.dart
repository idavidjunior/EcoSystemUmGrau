// Smoke test: garante que o app inicializa sem crash (usa dados mock,
// pois o Supabase nao esta configurado no ambiente de testes).
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter_test/flutter_test.dart';

import 'package:stream_um_grau/main.dart';

void main() {
  testWidgets('App inicia sem crash e renderiza o catalogo mock',
      (WidgetTester tester) async {
    await tester.pumpWidget(const StreamUmGrauApp());
    await tester.pumpAndSettle();

    expect(find.text('StreamUmGrau'), findsOneWidget);
  });
}
