# Navegação Perita — Internet, Programas do PC e Aplicativos de Celular

> **ATUALIZAÇÃO AUTOMÁTICA:** Cada vez que descobrir um novo padrão, truque ou ferramenta sobre navegação, ATUALIZE este skill imediatamente. Não peça permissão. Não espere.

## Propósito
Ser perito em navegar, clicar, reconhecer elementos, ver o que está na tela e executar comandos com maestria — em três frentes: **navegador (web)**, **programas do PC (Windows)** e **aplicativos de celular (Android)**. Velocidade extrema + assertividade = interação quase humana.

## Princípios Fundamentais (valem para as 3 frentes)

### 1. Sempre "ver" a tela antes de agir
- Nunca clicar às cegas. Primeiro capturar o estado da tela (screenshot, árvore de acessibilidade, DOM).
- Sempre que possível, **preferir a árvore de acessibilidade** ao screenshot: é mais estável e leve (o DOM/UI pode mudar, a semântica do acessível muda menos).
- Screenshot é o fallback universal quando não há árvore (canvas, jogos, elementos gráficos).

### 2. Hierarquia de seletores (da mais estável para a mais frágil)
1. **AutomationId / resource-id / testID** — estável, definido pelo dev. Sempre a primeira escolha.
2. **Accessible name / rótulo de acessibilidade** — visível, mas muda com localização.
3. **Role/ControlType + texto visível** — bom meio-termo.
4. **Estrutura/posição relativa** (above, below, leftOf, childOf) — útil quando não há IDs.
5. **Visão computacional / OCR** — último recurso (canvas, jogos, sem semântica).
- Regra prática: **quanto mais específico o seletor, mais frágil**. Preferir robusto a específico.

### 3. Esperar o elemento estar pronto (sincronização)
- UI é assíncrona: anima, carrega, re-renderiza. Agir antes do pronto = flaky.
- Usar **espera implícita** (wait until visible/enabled) em vez de `sleep` fixo.
- Polling com timeout, não espera fixa. Se o elemento não apareceu, re-analisar a tela.
- Elementos podem ser **substituídos a cada re-render** (frame novo = elemento novo). Re-resolver a cada ação.

### 4. Verificação após cada ação
- Após clicar/digitar, **confirmar o efeito**: a tela mudou? apareceu o esperado?
- Se falhou: capturar nova screenshot, analisar a diferença, tentar rota alternativa.
- Não repetir o mesmo clique em loop — isso é sintoma de que algo mudou.

### 5. Fallback em cadeia
- 1º: caminho principal (seletor estável). 2º: caminho alternativo (texto/posição).
- 3º: teclado (shortcuts universais, tab, enter). 4º: OCR/visão. 5º: pedir confirmação.
- Sempre registrar qual fallback foi usado (útil para diagnóstico).

## FRENTE 1 — NAVEGADOR (Internet)

### Ferramentas de referência (GitHub)
| Ferramenta | Repo | Papel |
|-----------|------|-------|
| Playwright MCP | `microsoft/playwright-mcp` | O padrão ouro p/ agentes: navega, clica, digita, screenshots via MCP |
| Browser-Use | `browser-use/browser-use` (78k★) | Agente de navegação por linguagem natural, visão + multi-tab |
| Stagehand | `browserbase/stagehand` (20k★) | `act()` / `extract()` / `observe()` — usa accessibility tree |
| Playwright CLI | `microsoft/playwright` | Automação determinística, cross-browser |
| Puppeteer | `puppeteer/puppeteer` | Chrome/Chromium específico |
| Skyvern | `Skyvern-AI/skyvern` | RPA visual com visão computacional, anti-bot |

### Workflow perito no navegador
1. **`browser_navigate`** para a URL.
2. **`browser_snapshot`** (accessibility snapshot) — ver o que está na tela.
3. Identificar o alvo pela hierarquia: role + accessible name (ex: `button "Entrar"`).
4. **`browser_click`** / `browser_fill` / `browser_type` com o ref do elemento.
5. **`browser_snapshot`** novamente — confirmar que o estado mudou.
6. Se precisar ver visualmente: **screenshot** (full page ou elemento).
7. Multi-tab: `browser_new_tab`, alternar com contexto. Popups e iframes: entrar no frame correto antes.
8. Shadow DOM: **penetrar o shadow root** (Playwright `locator` atravessa shadow DOM automaticamente).

### Heurísticas web
- SPA (React/Vue/Angular): a navegação não recarrega a página. Detectar por: DOM que muda sem `page load`, hash routes (`#/`), `history.pushState`. Após clicar, **esperar o novo conteúdo** (não a navegação).
- Elementos lazy-loaded: só existem após scroll. `scrollIntoView` antes de interagir.
- Elementos `stale`: nunca reutilizar referência antiga — re-consultar o DOM.
- Anti-bot: reduzir padrão robótico, humanizar velocidade, respeitar a semântica (não spam click).
- Formulários rich-text (contenteditable/iframe): selecionar o iframe, depois digitar no editor.

## FRENTE 2 — PROGRAMAS DO PC (Windows)

### Ferramentas de referência (GitHub)
| Ferramenta | Repo | Papel |
|-----------|------|-------|
| FlaUI | `FlaUI/FlaUI` (3k★) | UI Automation .NET (UIA2/UIA3) — Win32, WinForms, WPF, Store |
| pywinauto | `pywinauto/pywinauto` | Python + UI Automation/MSAA, envio de teclado/mouse |
| xa11y | `crowecawcaw/xa11y` | API estilo Playwright sobre accessibility tree (Win/macOS/Linux) |
| FlaUI Inspect / Accessibility Insights | Microsoft | Inspecionar elementos: AutomationId, Name, ControlType, patterns |
| WinAppDriver | `microsoft/WinAppDriver` | Driver WebDriver p/ apps Windows |

### Fundamentos UIA (Windows)
- Todo controle expõe um **AutomationElement** com: Name, AutomationId, ControlType, e **Control Patterns**:
  - `InvokePattern` → clicar (`button.Invoke()`)
  - `ValuePattern` → ler/definir texto (`input.SetValue(...)`)
  - `SelectionPattern` → lista/combobox (`item.Select()`)
  - `TogglePattern` → checkbox (`checkbox.Toggle()`)
  - `WindowPattern` → maximizar/minimizar/fechar
- Árvore UIA tem 3 visões: **Raw** (tudo), **Control** (controles), **Content** (conteúdo útil). Usar Control/Content para interagir.
- Windows UIA permite **prefetch de toda a subárvore numa chamada** (`FindAllBuildCache` + `CacheRequest`) — muito rápido.

### Workflow perito no Windows
1. Localizar o app: `Application.Launch("notepad.exe")` ou anexar a processo existente.
2. Pegar a janela principal: `app.GetMainWindow(automation)`.
3. Inspecionar elementos — pela ordem: **AutomationId → Name → ControlType+índice**.
4. Interagir com os patterns (Invoke/Value/Selection/Toggle).
5. Esperas explícitas: desktop não tem rede p/ esperar. Poll até condição (`WaitUntilEnabled`), com timeout.
6. Verificação: janela nova? título mudou? controle habilitado?

### Heurísticas desktop
- Diálogos modais: **verificar modais antes de cada interação** — botões podem estar ocultos atrás.
- Apps com layout custom (canvas, GPU): sem árvore de acessibilidade → OCR/template matching + coordenadas.
- Coordenadas: usar **relativas (%)** quando possível, nunca absolutas fixas (resoluções mudam).
- Menu dropdown: abrir, esperar o menu, depois clicar no item (2 operações separadas).
- Teclado vence layout: shortcuts (`Ctrl+N`, `Tab`, `Enter`) funcionam mesmo quando seletor falha.

## FRENTE 3 — APLICATIVOS DE CELULAR (Android)

### Ferramentas de referência (GitHub)
| Ferramenta | Repo | Papel |
|-----------|------|-------|
| Appium | `appium/appium` (17k★) | Black-box, WebDriver. Driver `uiautomator2` p/ Android |
| Maestro | `mobile-dev-inc/maestro` (15k★) | YAML flows, interage via accessibility layer, framework-agnostic |
| maestro-runner | `devicelab-dev/maestro-runner` | Alternativa open-source, single binary, ~5x mais rápido |
| UIAutomator2 | `appium/appium-uiautomator2-driver` | Driver nativo do Google p/ automação Android |
| ADB | Google | Controle de dispositivo, input tap/swipe/text, uiautomator dump |

### Workflow perito no Android (sem Appium — via ADB direto)
1. Conectar: `adb connect <ip>:5555` (ou via Tailscale).
2. Ver a tela: `adb exec-out screencap -p > tela.png`.
3. Dump da árvore UI: `adb shell uiautomator dump` → XML com `resource-id`, `text`, `bounds`, `class`, `content-desc`.
4. Tocar: `adb shell input tap X Y` (coordenadas do `bounds`).
5. Digitar: `adb shell input text "..."` (unicode pode precisar `input keyevent` ou ADBKeyboard).
6. Swipe/scroll: `adb shell input swipe X1 Y1 X2 Y2 duração`.
7. Voltar/Home: `adb shell input keyevent 4` (back) / `3` (home).
8. Confirmar: novo `screencap` + `uiautomator dump`.

### Hierarquia de seletores Android
1. `resource-id` (o mais estável)
2. `content-desc` (acessibilidade)
3. `text` visível
4. `class` + `bounds` (posição)
5. Visão computacional sobre o screenshot

### Heurísticas mobile
- **Teclado virtual bloqueia cliques**: sempre fechar o teclado antes do próximo clique (esp. em MIUI/HyperOS).
- **Diálogos de permissão MIUI/HyperOS** bloqueiam instalação e primeiro uso — detectar e clicar "Permitir".
- RecyclerView: itens só existem quando visíveis. `scrollUntilVisible`/swipe para trazer o item.
- Apps em Compose: IDs auto-gerados mudam a cada build — preferir texto/content-desc.
- Emulador ≠ dispositivo real: status bar, fontes e gestos diferem. Testar no real (Redmi Note 11).
- Widgets/estado: apps Android podem rodar em background; verificar se o app está em foreground (`adb shell dumpsys window`).

## Scripts Úteis do Ecossistema
- `scripts/android_diagnostics.py --json` → diagnóstico completo do dispositivo via ADB.
- `Habilidades/tecnicas/android-diagnostics/skill.md` → manutenção remota do app Android.
- ADB path: `C:\Users\David Jr\AppData\Local\Android\platform-tools\platform-tools\adb.exe`.
- Dispositivo: `adb connect 100.64.71.9:5555`, pacote `com.voxumgrau.app`.

## Revisão rápida (antes de cada tarefa de navegação)
- [ ] Vi a tela (screenshot/árvore)?
- [ ] Seletor na ordem certa (id → nome → role → posição → visão)?
- [ ] Esperei o elemento ficar pronto (não sleep cego)?
- [ ] Vou confirmar o efeito após a ação?
- [ ] Tenho um fallback se o principal falhar?

## Known Issues & Fixes
| Issue | Causa | Correção |
|-------|-------|----------|
| Elemento não encontrado em Shadow DOM | Shadow root bloqueia seletor | Atravessar shadow root / usar locator que penetra |
| Elemento "stale" após ação | DOM/UI re-renderizou | Re-consultar o elemento antes de cada ação |
| Dropdown/select não responde a click | Menu precisa abrir antes | Abrir → esperar menu → clicar item |
| Teclado virtual bloqueia botão (Android) | Teclado sobrepõe UI | Fechar teclado antes do clique |
| Seletor quebrou após redesign | UI mudou de estrutura | Trocar para texto visível / content-desc / visão |
| App Android não em foreground | Rodando em background | `adb shell am start` do pacote antes de agir |
| Click acerta lugar errado em resolução diferente | Coordenadas absolutas | Usar coordenadas relativas (%) ou seletores |

## Referências (GitHub)
- https://github.com/microsoft/playwright-mcp
- https://github.com/browser-use/browser-use
- https://github.com/browserbase/stagehand
- https://github.com/FlaUI/FlaUI
- https://github.com/pywinauto/pywinauto
- https://github.com/appium/appium
- https://github.com/mobile-dev-inc/maestro
- https://github.com/devicelab-dev/maestro-runner
- https://github.com/Skyvern-AI/skyvern
