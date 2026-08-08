/// Configuracoes centralizadas do aplicativo.
///
/// As credenciais do Supabase sao injetadas em tempo de compilacao via
/// --dart-define para nao ficarem versionadas no codigo:
///
///   flutter run --dart-define=SUPABASE_URL=https://xxxx.supabase.co \
///               --dart-define=SUPABASE_ANON_KEY=eyJhbGciOi...
///
/// Voce tambem pode criar um arquivo `lib/core/config/.env` (nao versionado)
/// ou editar os valores padrao abaixo apenas para desenvolvimento local.
class AppConfig {
  AppConfig._();

  /// Nome da tabela que guarda o catalogo de midias no Supabase.
  static const String midiasTable = 'midias';

  /// URL do projeto Supabase.
  static const String supabaseUrl = String.fromEnvironment(
    'SUPABASE_URL',
    defaultValue: 'https://SEU_PROJETO.supabase.co',
  );

  /// Chave anonima publica do projeto Supabase (apenas RLS).
  static const String supabaseAnonKey = String.fromEnvironment(
    'SUPABASE_ANON_KEY',
    defaultValue: 'SUA_CHAVE_ANON_AQUI',
  );
}
