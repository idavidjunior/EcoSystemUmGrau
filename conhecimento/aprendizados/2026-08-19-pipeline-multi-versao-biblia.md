---
tipo: padrao
tags: [biblia, versao, traducao, sqlite, android, pipeline]
data: 2026-08-19
contexto: Implementacao de multi-versao (ARC + ALM1911) no app BibliaEstudoCompleta.
decisao: Pipeline completo para adicionar novas traduções ao banco e ao app.
impacto: Proximas versoes seguem o mesmo pipeline sem retrabalho.
status: validado
---

# Como adicionar uma nova versão da Bíblia ao BibliaEstudoCompleta

Pipeline completo validado na adição da ALM1911 (domínio público) junto à ARC (SBB licenciada).

## 1. Origem dos dados

- Formato aceito: JSON com lista de livros contendo `abbrev` e `chapters` (arrays de versículos).
- Fontes: repositório damarals/biblias no GitHub releases (ALM1911.json, 4MB, 66 livros canônicos).
- Regra de licença: versões licenciadas (ARC/SBB) NÃO podem ser redistribuídas; versões de domínio público (ALM1911) podem.

## 2. Schema do banco (assets/databases/biblia_estudo.db)

- Tabela `verses`: coluna `translation_id TEXT NOT NULL DEFAULT 'arc'`.
- Constraint UNIQUE: `(book_id, chapter, verse_number, translation_id)` — permite a mesma referência em várias traduções.
- Tabela `translations`: `code (UNIQUE), name, language, license, is_default`.
- Índice: `idx_verses_translation (translation_id)`.
- FTS4: `verses_fts (text, book_id, chapter, verse_number)` — texto normalizado (sem acentos), filtro por tradução no outer query via `v.translation_id = ?`.

## 3. Script de injeção (scripts/add_alm1911.py)

- Faz backup do DB (`biblia_estudo.db.bak`) antes de alterar.
- Adiciona coluna `translation_id` se não existir (ALTER TABLE + UPDATE default 'arc').
- Reconstrói a tabela `verses` para trocar a constraint UNIQUE (nova versão precisa incluir translation_id).
- Registra as traduções na tabela `translations` (só se vazia).
- Mapeia os livros canônicos por `testament IN (1,2) ORDER BY book_order` — EVITAR normalização por abreviatura (colisão "Jó" vs "Jo" já ocorreu).
- Insere os versículos com `translation_id` da nova versão.
- Rebuild total do FTS (DROP + CREATE + INSERT com docid = rowid de verses e texto normalizado).
- `PRAGMA user_version = 7` no final.
- Ajusta `DatabaseManager.CURRENT_DB_VERSION` (agora 11) para forçar recópia do asset no device.

## 4. Código Android

Arquivos que conhecem tradução (todos precisam de `translation_id`):

- `BibleDatabaseHelper.java`: DATABASE_VERSION 7, TABLE_TRANSLATIONS, tabela verses com translation_id, índices, migração < 7.
- `DatabaseManager.java`: CURRENT_DB_VERSION 11, garante coluna translation_id e tabela translations em bancos antigos, FTS existente.
- `BibliaApplication.java`: KEY_TRANSLATION, DEFAULT_TRANSLATION='arc', getActiveTranslation/setActiveTranslation (SharedPreferences).
- `Verse.java`: campo translationId + getter/setter.
- `VerseDao.java`: todos os métodos com overload com translationId (getChapter, getVersesRange, getVerseCount).
- `BibleReaderActivity.java`: seletor de versão no toolbar (subtítulo clicável + AlertDialog), carrega capítulo com tradução ativa, mensagem "Capítulo não disponível nesta versão" para livros que não existem na tradução.
- `SearchEngine.java`: campo translationId, filtro em todas as buscas (word/phrase/book/topic) e fallback.
- `SearchActivity.java`: dropdown (Spinner) de versão integrado à tela de busca; troca chama setActiveTranslation e refaz a busca; onResume sincroniza tradução do engine ao voltar do reader.
- `HomeActivity`, `HighlightsActivity`, `ReferenceMapActivity`: usam tradução ativa.

## 5. Compilação e instalação

- Build: `powershell -ExecutionPolicy Bypass -File build.ps1` (aapt2 + javac + d8 + apksigner, 88 arquivos Java).
- Instalação: `adb install -r bin\BibliaEstudoCompleta.apk`.
- O app NÃO é debuggable e não tem root: validação via `adb shell uiautomator dump` + `dumpsys window` + logcat.
- Em MIUI o uiautomator dump pode mostrar hierarquia antiga; usar `adb exec-out uiautomator dump /dev/tty` (scripts/parse_ui_live.py).

## 6. Testes de regressão validados

1. Abrir leitor → toolbar mostra tradução ativa com ▾.
2. Trocar versão no leitor → texto muda (ARC: "No princípio, criou Deus" / ALM1911: "No principio creou Deus").
3. Persistência: matar app e reabrir mantém a versão escolhida.
4. Livro deuterocanônico (Tobias) na ALM1911 → "Capítulo não disponível nesta versão"; na ARC aparece normalmente.
5. Busca filtrada por tradução: "creou" retorna vazio na ARC e resultados na ALM1911.
6. Dropdown da busca troca a versão e refaz a busca na hora.

## 7. Armadilhas conhecidas

- Colisão de abreviaturas na normalização ("Jó" vs "Jo") → mapear por testament+book_order, nunca por abreviação.
- FTS fica sem translation_id de propósito; filtrar SEMPRE no outer query (JOIN books + WHERE v.translation_id = ?).
- Esquecer de subir CURRENT_DB_VERSION → device mantém banco antigo.
- Esquecer de reconstruir o FTS após inserir versículos → busca nova não retorna a nova versão.
- Esquecer de atualizar a tradução do SearchEngine ao voltar do reader → busca velha (resolvido com onResume).

## 8. Próximos passos sugeridos

- Adicionar NVI/ARA/King James Atualizada quando tiver licença.
- Exportar o pipeline como script parametrizado (scripts/add_translation.py --json X --code Y --name Z).
- Considerar adicionar translation_id ao FTS e usar FTS5 para busca diacrítica nativa.

## Conexoes

- [[elementos-culturalmente-intraduzíveis-humor-trocadilhos-prov]]
- [[estratégias-de-tradução-literal-semântica-adaptativa-e-quand]]
- [[falsos-cognatos-e-armadilhas-interlíngua-inglês-português]]
- [[fidelidade-x-naturalidade-quando-priorizar-cada-um]]
- [[pipeline-de-tradução-de-qualidade-análise-rascunho-revisão-e]]
- [[princípios-fundamentais-da-tradução-sentido-equivalência-e-f]]
- [[quando-adaptar-x-quando-manter-o-termo-original-estrangeiris]]
- [[tom-e-registro-formal-técnico-coloquial-como-detectar-e-mant]]