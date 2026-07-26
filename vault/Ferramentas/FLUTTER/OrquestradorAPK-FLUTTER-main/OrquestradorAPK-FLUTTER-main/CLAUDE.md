# Projeto: Flutter Build Orchestrator

## Missao

Automatizar o processo de build de aplicativos Flutter, gerando APK pronto para
instalacao com minima intervencao manual. Suporta CLI e GUI.

## Conhecimento Consolidado

Este documento captura padroes e decisoes de 3 projetos anteriores que se aplicam
diretamente a este orquestrador:

### 1. Android Pure SDK (Build Pipeline)

**Pipeline Completo de Build:**
- `aapt package` -> `javac` -> `jar` -> `d8` -> `aapt package (APK)` -> `aapt add` -> `zipalign` -> `apksigner`
- Cada step tem uma funcao dedicada com verificacao de erro explicita
- Steps falham rapido (fail fast) — se um step falha, nao adianta continuar

**Verificacao de APK:**
- `apksigner verify APK.apk` — verifica assinatura
- `apksigner verify --print-certs` — mostra certificados
- zipalign -v -c 4 — verifica alinhamento (obrigatorio no Android 11+)

**Erros Comuns de Build (mapeamento):**
| Erro | Causa Raiz | Correcacao |
|------|-----------|------------|
| `INSTALL_FAILED_INVALID_APK` | zipalign faltou ou falhou | Rodar zipalign antes de assinar |
| `INSTALL_FAILED_UPDATE_INCOMPATIBLE` | APK assinado com keystore diferente | Mesma keystore sempre |
| `Failure [INSTALL_FAILED_OLDER_SDK]` | targetSdkVersion < device OS | Atualizar targetSdkVersion |
| `cannot find symbol R` | R.java nao gerado | Verificar `aapt package -J` |
| `No resource found` | Resource XML referencia algo inexistente | Adicionar recurso ou corrigir referencia |

**Cache de Build:** Nao rebuildar se nada mudou (hash dos source files)

### 2. MP3Player (Multi-Source Fallback + Scoring)

**Multi-Source Fallback:** Tentar fontes em ordem de confianca:
1. Fonte primaria (mais rapida/confiavel)
2. Fallback com limiares mais baixos (RELAXED mode)
3. Fallback com query mais ampla (title-only, artist-only)

**Scoring Thresholds:** Cada resultado tem pontuacao:
- Match exato: aceita imediatamente
- Match parcial: aceita se acima do threshold
- Abaixo do threshold: rejeita e tenta proxima fonte

**Explicit Redirect Handling:** HTTP redirects (301/302) precisam de loop manual
porque `HttpURLConnection.followRedirects` nem sempre funciona

### 3. LER (Loop Engineering Runtime)

**Goal-Oriented Loop:** Cada operacao segue: analisar -> planejar -> executar -> validar -> aprender

**Stagnation Detection:** Nao loopar para sempre no mesmo problema. Se N iteracoes sem progresso, mudar de estrategia.

**Auto-Learning:** Toda operacao gera aprendizado:
- Sucesso -> registrar padrao bem-sucedido
- Falha -> registrar padrao de falha
- Aprendizado persiste em arquivo JSON

**Atomic Persistence:** Nunca escrever direto no arquivo final:
```python
with open(path + ".tmp", "w") as f:
    json.dump(data, f)
os.replace(path + ".tmp", path)  # atomico
```

**Evidence Collection:** Coletar logs, hashes, artefatos, decisoes, timing de cada build
Gerar relatorio JSON com tudo

**Result Caching:** Nao reexecutar se nada mudou (hash dos inputs)

**Supervisor Pattern:** Monitorar saude de cada modulo individualmente
Recuperacao isolada — nao derrubar o pipeline inteiro por um modulo falho

**Quality Gates:** Score ponderado antes de aceitar um resultado:
- Funcionamento 30%
- Requisitos 30%
- Testes 10%
- Evidencias 10%
- Auditoria 10%
- Threshold minimo: 95%

**User Feedback Loop:** Antes de concluir, perguntar ao usuario se o resultado e satisfatorio
Se nao, aprender e tentar de novo

## Arquitetura Atual

```
flutter_orchestrator.py          # CLI unificada (entry point principal)
flutter_build_orchestrator.py     # Wrapper thin que redireciona para a CLI
flutter_orchestrator_gui.py       # Entry point thin para a GUI
gui/
  __init__.py                     # Package marker
  app.py                          # GUI principal (BuildOrchestratorGUI)
  logger.py                       # Logger thread-safe com fila
  checklist.py                    # Verificacao de pre-requisitos
  knowledge_base.py               # Base de correcoes conhecidas (known_fixes.json)
  gemini_fixer.py                 # Correcacao via API Gemini
  project_source.py               # Gerencia codigo fonte, pubspec, permissoes
orchestrator/
  __init__.py
  flutter_orchestrator.py         # Implementacao modular (FlutterOrchestrator async)
  timeout_manager.py              # AdaptiveTimeoutManager com historico
  ia_response_validator.py        # Validacao de respostas de IA
  model_manager.py                # Gerenciamento de modelos de IA (IntelligentModelManager)
  kotlin_fixer.py                 # Correcacao automatica de Kotlin/Gradle
  knowledge_base_learner.py       # Aprendizado de erros e solucoes
  build_provenance.py             # [ADICIONADO] Coleta de evidencias de build
known_fixes.json                  # Knowledge base de erros e correcoes
knowledge_base.json               # Base de conhecimento aprendida
model_performance.json            # Performance dos modelos de IA
orchestrator_config.yaml          # Configuracao principal
timeout_config.json               # Configuracao de timeouts adaptativos
consolidate_build_pipeline.py     # Pipeline de build consolidada (BuildPipelineArchitecture)
examples/
  mp3_player_fixed.dart           # Exemplo de app corrigido automaticamente
tests/
  test_orchestrator.py            # Testes unitarios do orchestrator
  test_smoke.py                   # Testes de fumaca (imports)
```

## CLI Usage

```bash
python flutter_orchestrator.py /caminho/do/projeto
python flutter_orchestrator.py /caminho/do/projeto --debug --skip-tests
python flutter_orchestrator.py /caminho/do/projeto --build-number 42
python flutter_orchestrator.py /caminho/do/projeto --auto-install
python flutter_orchestrator.py /caminho/do/projeto --verify-apk  # verifica APK apos build
```

## GUI Usage

```bash
python flutter_orchestrator_gui.py
```

## Padroes de Codigo

- Python 3.7+, tipagem com type hints
- Respeitar single-responsibility: cada classe/arquivo um proposito
- Evitar hardcoding de URLs (usar lookup dinamico via API)
- Tratar PyYAML como opcional com fallback gracioso
- Protecao contra path traversal na extracao de archives
- Testes em tests/ com pytest
- **Escrita atomica** em todos os arquivos JSON (tmp + os.replace)
- **Nao usar except: sem especificar excecao** — except especifico sempre

## Pipeline de Build (Goal-Oriented)

Cada etapa segue: EXECUTAR -> VALIDAR -> COLETAR EVIDENCIA -> APRENDER

1. **Pre-requisitos** — Verifica Flutter, Git, Java (checklist)
2. **Validacao** — Confirma projeto Flutter valido
3. **Dependencias** — `flutter pub get`
4. **Analise** — `flutter analyze` (com scoring de warnings)
5. **Testes** — `flutter test` (opcional, com cache por hash)
6. **Build** — `flutter build apk --release` ou --debug
7. **Verificacao** — Verifica APK gerado (tamanho, hash, assinatura)
8. **Copy** — Copia APK para output com timestamp
9. **Relatorio** — Gera build_report.json + evidence.json
10. **Aprendizado** — knowledge_base_learner.learn_from_build()

## Estrategia de Fallback (Multi-Source)

Para correcao de erros de build, usar fallback em cascata:

1. **Known Fixes** (`known_fixes.json`) — match exato de erro -> solucao conhecida
2. **Knowledge Base** (`knowledge_base.json`) — erro similar visto antes -> solucao com confianca
3. **IA Modelo Primario** — modelo configurado no YAML (ex: deepseek-ai/deepseek-v4-flash)
4. **IA Modelo Fallback** — segundo modelo (ex: meta/llama-3.1-70b-instruct)
5. **IA Modelo Terciario** — terceiro modelo (ex: mistralai/mixtral-8x7b-instruct)
6. **Falha Assumida** — reportar erro e sugerir acao manual

Cada fallback deve:
- Registrar o resultado (sucesso/falha, tempo de resposta)
- Atualizar model_performance.json
- Se taxa de sucesso do modelo < 50%, trocar ordem de prioridade

## Auto-Learning

Apos cada build (sucesso ou falha):
1. `KnowledgeBaseLearner.learn_from_build()` — extrai padrao do erro, registra solucao
2. Se sucesso: registrar padrao bem-sucedido (acao, descricao, duracao, timestamp)
3. Se falha: registrar padrao de falha, tentar solucao alternativa
4. `AdaptiveTimeoutManager.record_attempt()` — ajusta timeout baseado em historico
5. Gerar evidence.json com:
   - Logs do build
   - SHA256 do APK gerado
   - Resultado de cada etapa
   - Decisoes tomadas (qual fallback usado, qual solucao aplicada)
   - Timing de cada etapa

## Evidence Collection (build_provenance.py)

Cada build gera um dossie de evidencias:
- `evidence.json` — dados estruturados
- `evidence.md` — relatorio legivel
- SHA256 de cada artefato (APK, mapping file, relatorio)
- Log de cada comando executado
- Decisoes tomadas durante o build
- Modelo de IA usado e performance

## Git / Commits

- Commitar sempre na branch `main`
- Mensagens em portugues (idioma do projeto)
- Usar conventional commits: `fix:`, `feat:`, `refactor:`, `docs:`, `test:`

## CI/CD

Workflow em `.github/workflows/compile.yml`:
- Lint com ruff
- Testes com pytest
- Verificacao de imports dos modulos
- Smoke tests
