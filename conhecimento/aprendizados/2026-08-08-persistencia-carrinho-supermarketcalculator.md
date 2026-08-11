---
tipo: erro
tags: [android, persistencia, sharedpreferences, lifecycle, activity, build, apk, build.ps1, release, keystore]
data: 2026-08-08
fonte: tarefa
contexto: SupermarketCalculator (Android SDK puro, Java). Usuário relatou que ao bloquear a tela com uma lista de compras em construção, todos os dados do carrinho se perdiam.
decisao: Causa raiz: o carrinho `items` (ArrayList<CartItem>) vivia apenas em memória — `setupCalculator()` criava `new ArrayList<>()` e não havia nenhuma persistência (sem onSaveInstanceState, sem onPause, sem SharedPreferences). Quando a Activity é recriada (bloqueio de tela, mudança de config, processo morto), o carrinho zerava. Solução: persistência imediata em SharedPreferences via JSON — `saveCartState()` chamado a TODA mutação (addOrUpdateItem, clearCart, clearCartAfterFinish, loadStructuredListIntoCart, onIncrement/onDecrement/onRemove/onNameChanged) + `onPause()` como rede de segurança; `loadCartState()` no onCreate após setupCalculator. Também registra unnamedCounter, budgetLimit e currentQty. Na sequência: release keystore criada (release.keystore, alias supermarket, senha opencode), versão incrementada para 1.3.0 (versionCode 4), APK release assinado, instalado e testado.
impacto: Carrinho agora sobrevive a bloqueio de tela, rotação, morte de processo e navegação. APK v1.3.0 release assinado, instalado via ADB e testado no Redmi Note 11 — app abre, onCreate OK, sem crash. Guia operacional em Projetos/SupermarketCalculator/RELEASE.md. Da v1.3.0 em diante, atualizações usam adb install -r com a MESMA release keystore (preserva dados).
---

# 2026-08-08: Persistência do carrinho do SupermarketCalculator e build.ps1 resiliente

## Problema
Lista de compras em construção era perdida ao bloquear a tela do celular.

## Causa raiz
- `MainActivity` mantém o carrinho em `ArrayList<CartItem>` somente em memória.
- Não existia `onSaveInstanceState`, `onPause` nem gravação em disco/prefs para o carrinho ativo.
- Ao bloquear a tela o sistema recria a Activity → `items = new ArrayList<>()` → tudo zerado.

## Correção (MainActivity.java)
1. `saveCartState()` — serializa itens (name/unitPrice/quantity) + unnamedCounter + budgetLimit + currentQty em JSON no SharedPreferences (`prefs` "settings", chave `cart_state`), via `apply()`.
2. Chamado em toda mutação do carrinho: `addOrUpdateItem`, `clearCart`, `clearCartAfterFinish`, `loadStructuredListIntoCart`, botão "Adicionar todos", e listeners `onIncrement`, `onDecrement`, `onRemove`, `onNameChanged`.
3. `loadCartState()` no `onCreate` logo após `setupCalculator()` e antes de `updateTotal()`.
4. `onPause()` → `saveCartState()` como rede de segurança (padrão METODOLOGIA.md).

## Correção build.ps1 (necessária para compilar/instalar/testar)
O build.ps1 original hardcodava build-tools 36.0.0 e android-36 (inexistentes na máquina) e quebrava com espaços no caminho do projeto ("Default Project"). Reescrito:
- **Auto-deteção** do build-tools e platform mais recentes instalados (35.0.0 / android-35).
- **javac com argfile** usando caminhos relativos (sem espaços) para evitar problemas de quote.
- **DEX na raiz do APK**: `aapt add` precisa rodar com cwd = pasta do dex (`Push-Location build\dex`) senão adiciona `build\dex\classes.dex` no APK → `INSTALL_FAILED_INVALID_APK: code is missing`.
- d8.bat/apksigner.bat estão em `build-tools\<ver>\`, não em cmdline-tools.

## Erros de instalação encontrados e resolvidos
- `INSTALL_FAILED_UPDATE_INCOMPATIBLE` → assinatura anterior diferente → desinstalar e reinstalar (autorizado pelo usuário).
- `INSTALL_FAILED_INVALID_APK: code is missing` → DEX não estava na raiz (corrigido acima).
- `INSTALL_FAILED_USER_RESTRICTED` → `adb install -r -t` resolveu.

## Resultado
- APK v1.2.0 compilado, instalado via ADB no Redmi Note 11 e testado (app abre, `onCreate called`, processo ativo, sem crash no logcat).
- Próximo passo para o usuário: adicionar itens → bloquear tela → desbloquear → confirmar que o carrinho persiste.

## Padrões/Heurísticas acionados
- `metodo-dos-5-porques-5-why` (perda de dados → Activity recriada → nada persistido → sem ciclo de vida)
- `projete-para-falha-nao-para-sucesso` (onPause como rede de segurança)
- Protocolo obrigatório do ecossistema: **compilar → instalar no celular via ADB → testar** (todo APK).

## Release v1.3.0 (2026-08-08)

- **versionCode 4 / versionName 1.3.0** no AndroidManifest.xml (incremento sempre obrigatório).
- **release.keystore criada** (RSA 2048, alias `supermarket`, storepass/keypass `opencode`,
  DN `CN=Supermarket Calculator, OU=UmGrau, O=EcoSystemUmGrau, L=Belem, ST=Para, C=BR`,
  SHA-256 `20b1693cd2ccdbe62294e83bb990599e77762618a774842850f0e73e29026562`).
  ⚠️ Guardar/backup da keystore — sem ela, próximas versões não sobem por cima (perda de dados).
- Build: `.\build.ps1 -Release -OutputName "SupermarketCalculator-v1.3.0"`.
- Instalação: desinstalar a debug (assinatura antiga) → instalar release → `am start`.
  Próximas atualizações: `adb install -r` (mesma assinatura preserva dados).
- APK publicado: `releases/SupermarketCalculator-v1.3.0.apk`.
- **Guia operacional:** `Projetos/SupermarketCalculator/RELEASE.md` (compilar/versionar/assinar/instalar).

## Release v1.4.0 (2026-08-08) — Som no botão Adicionar

- **versionCode 5 / versionName 1.4.0**.
- **3 sons pré-carregados** em `res/raw/`: `som_caixa.wav` (caixa registradora, sintetizado), `som_pop.wav`, `som_bip.wav`.
  `aapt package -S res` empacota `res/raw/` automaticamente — sem mudança no build.ps1.
- **Reprodução via SoundPool** (`SoundPool.Builder().setMaxStreams(1)`), sons carregados no `onCreate`
  (`soundPool.load(this, R.raw.som_caixa, 1)`), liberados no `onDestroy` (evita vazamento nativo).
- **Config:** Config → Som do botão Adicionar (RadioGroup `soundGroup`; RadioButtons `soundCashRegister`/`soundPop`/`soundBeep`).
  Preferência em SharedPreferences `settings`, chave `KEY_SOUND = "add_sound"` (int: 0=caixa, 1=pop, 2=bip). Ao trocar, toca o som como prévia.
- **Gatilho:** `playAddSound()` em `addOrUpdateItem` após a validação do preço (só toca quando o item é de fato adicionado).
- **Decisão de design:** SoundPool (e não MediaPlayer) para efeitos curtos repetidos — pré-carrega em memória e tem baixa latência.
- Build: `.\build.ps1 -Release -OutputName "SupermarketCalculator-v1.4.0"`; instalado com `adb install -r` (update por cima da v1.3.0, dados preservados — mesma assinatura).
- APK publicado: `releases/SupermarketCalculator-v1.4.0.apk`.
- **Nota de teste:** depurar o app instalado (release) com APK debug falha com `INSTALL_FAILED_UPDATE_INCOMPATIBLE` (assinaturas diferentes). Sempre gerar release para testes de funcionalidade sobre a versão instalada.
