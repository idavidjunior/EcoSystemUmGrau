# Habilidade: Navegação Perita — Internet, PC e Celular

- **Data:** 01/08/2026
- **Sessão:** Criação da habilidade de navegação perita com pesquisa de ferramentas no GitHub

## Resumo
Criada a habilidade `navegacao-perita` no catálogo do ecossistema (Habilidades/tecnicas/navegacao-perita/skill.md),
registrada no `manifesto_geral.json`, cobrindo as três frentes: navegador (internet), programas do PC (Windows)
e aplicativos de celular (Android). Baseada em pesquisa do estado da arte de ferramentas no GitHub (2026).

## Ferramentas pesquisadas e referenciadas

### Internet (web)
- **Playwright MCP** (`microsoft/playwright-mcp`) — padrão ouro para agentes: navega, clica, digita, screenshot via MCP.
- **Browser-Use** (`browser-use/browser-use`, ~78k★) — agente de navegação por linguagem natural, visão + multi-tab.
- **Stagehand** (`browserbase/stagehand`, ~20k★) — primitivas `act()`/`extract()`/`observe()`, usa accessibility tree.
- **Skyvern** (`Skyvern-AI/skyvern`) — RPA visual com visão computacional, anti-bot.

### Programas do PC (Windows)
- **FlaUI** (`FlaUI/FlaUI`, ~3k★) — UI Automation .NET (UIA2/UIA3): Win32, WinForms, WPF, Store Apps.
- **pywinauto** (`pywinauto/pywinauto`) — Python + UI Automation/MSAA, envio de teclado/mouse.
- **xa11y** (`crowecawcaw/xa11y`) — API estilo Playwright sobre accessibility tree (Win/macOS/Linux).
- **WinAppDriver** (`microsoft/WinAppDriver`) — driver WebDriver para apps Windows.

### Celular (Android)
- **Appium** (`appium/appium`, ~17k★) — black-box via WebDriver; driver `uiautomator2`.
- **Maestro** (`mobile-dev-inc/maestro`, ~15k★) — YAML flows, interage via accessibility layer, framework-agnostic.
- **maestro-runner** (`devicelab-dev/maestro-runner`) — alternativa open-source, single binary, ~5x mais rápido.
- **ADB** — controle direto: screencap, uiautomator dump, input tap/swipe/text, keyevent.

## Princípios fundamentais consolidados
1. **Sempre "ver" a tela antes de agir** — screenshot ou árvore de acessibilidade.
2. **Preferir árvore de acessibilidade ao screenshot** — mais estável e leve; screenshot é fallback (canvas/jogos).
3. **Hierarquia de seletores**: AutomationId/resource-id/testID → accessible name → role+texto → posição relativa → visão/OCR.
4. **Esperar o elemento pronto** — wait implicit/explícito com polling, nunca sleep cego.
5. **Re-resolver elementos a cada ação** — UI re-renderiza e substitui elementos.
6. **Verificar efeito após cada ação** — se falhou, re-analisar e usar fallback em cadeia.
7. **Fallback em cadeia**: principal → alternativo → teclado → OCR → pedir confirmação.

## Padrões técnicos notáveis
- Windows UIA: Control Patterns (Invoke/Value/Selection/Toggle/Window) + prefetch de subárvore via CacheRequest.
- Windows UIA tem 3 visões da árvore: Raw / Control / Content.
- SPA: navegação sem reload; esperar novo conteúdo, não a navegação.
- Android: teclado virtual bloqueia cliques (fechar antes); diálos de permissão MIUI/HyperOS; RecyclerView só tem itens visíveis.
- ADB direto é o caminho mais rápido para o celular Xiaomi (sem Appium): `adb shell uiautomator dump` + `input tap`.

## Habilidade registrada
- Catálogo: `Habilidades/tecnicas/navegacao-perita/skill.md`
- Manifesto: `Habilidades/manifesto_geral.json` (agora com 40 habilidades)
- Triggers: "navegar", "clicar", "automatizar", "reconhecer elemento", "ver a tela", "executar no navegador/pc/celular", "screenshot"
