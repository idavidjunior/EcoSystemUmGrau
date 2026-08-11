# Habilidade: NavegaÃ§Ã£o Perita â€” Internet, PC e Celular

- **Data:** 01/08/2026
- **SessÃ£o:** CriaÃ§Ã£o da habilidade de navegaÃ§Ã£o perita com pesquisa de ferramentas no GitHub

## Resumo
Criada a habilidade `navegacao-perita` no catÃ¡logo do ecossistema (Habilidades/tecnicas/navegacao-perita/skill.md),
registrada no `manifesto_geral.json`, cobrindo as trÃªs frentes: navegador (internet), programas do PC (Windows)
e aplicativos de celular (Android). Baseada em pesquisa do estado da arte de ferramentas no GitHub (2026).

## Ferramentas pesquisadas e referenciadas

### Internet (web)
- **Playwright MCP** (`microsoft/playwright-mcp`) â€” padrÃ£o ouro para agentes: navega, clica, digita, screenshot via MCP.
- **Browser-Use** (`browser-use/browser-use`, ~78kâ˜…) â€” agente de navegaÃ§Ã£o por linguagem natural, visÃ£o + multi-tab.
- **Stagehand** (`browserbase/stagehand`, ~20kâ˜…) â€” primitivas `act()`/`extract()`/`observe()`, usa accessibility tree.
- **Skyvern** (`Skyvern-AI/skyvern`) â€” RPA visual com visÃ£o computacional, anti-bot.

### Programas do PC (Windows)
- **FlaUI** (`FlaUI/FlaUI`, ~3kâ˜…) â€” UI Automation .NET (UIA2/UIA3): Win32, WinForms, WPF, Store Apps.
- **pywinauto** (`pywinauto/pywinauto`) â€” Python + UI Automation/MSAA, envio de teclado/mouse.
- **xa11y** (`crowecawcaw/xa11y`) â€” API estilo Playwright sobre accessibility tree (Win/macOS/Linux).
- **WinAppDriver** (`microsoft/WinAppDriver`) â€” driver WebDriver para apps Windows.

### Celular (Android)
- **Appium** (`appium/appium`, ~17kâ˜…) â€” black-box via WebDriver; driver `uiautomator2`.
- **Maestro** (`mobile-dev-inc/maestro`, ~15kâ˜…) â€” YAML flows, interage via accessibility layer, framework-agnostic.
- **maestro-runner** (`devicelab-dev/maestro-runner`) â€” alternativa open-source, single binary, ~5x mais rÃ¡pido.
- **ADB** â€” controle direto: screencap, uiautomator dump, input tap/swipe/text, keyevent.

## PrincÃ­pios fundamentais consolidados
1. **Sempre "ver" a tela antes de agir** â€” screenshot ou Ã¡rvore de acessibilidade.
2. **Preferir Ã¡rvore de acessibilidade ao screenshot** â€” mais estÃ¡vel e leve; screenshot Ã© fallback (canvas/jogos).
3. **Hierarquia de seletores**: AutomationId/resource-id/testID â†’ accessible name â†’ role+texto â†’ posiÃ§Ã£o relativa â†’ visÃ£o/OCR.
4. **Esperar o elemento pronto** â€” wait implicit/explÃ­cito com polling, nunca sleep cego.
5. **Re-resolver elementos a cada aÃ§Ã£o** â€” UI re-renderiza e substitui elementos.
6. **Verificar efeito apÃ³s cada aÃ§Ã£o** â€” se falhou, re-analisar e usar fallback em cadeia.
7. **Fallback em cadeia**: principal â†’ alternativo â†’ teclado â†’ OCR â†’ pedir confirmaÃ§Ã£o.

## PadrÃµes tÃ©cnicos notÃ¡veis
- Windows UIA: Control Patterns (Invoke/Value/Selection/Toggle/Window) + prefetch de subÃ¡rvore via CacheRequest.
- Windows UIA tem 3 visÃµes da Ã¡rvore: Raw / Control / Content.
- SPA: navegaÃ§Ã£o sem reload; esperar novo conteÃºdo, nÃ£o a navegaÃ§Ã£o.
- Android: teclado virtual bloqueia cliques (fechar antes); diÃ¡los de permissÃ£o MIUI/HyperOS; RecyclerView sÃ³ tem itens visÃ­veis.
- ADB direto Ã© o caminho mais rÃ¡pido para o celular Xiaomi (sem Appium): `adb shell uiautomator dump` + `input tap`.

## Habilidade registrada
- CatÃ¡logo: `Habilidades/tecnicas/navegacao-perita/skill.md`
- Manifesto: `Habilidades/manifesto_geral.json` (agora com 40 habilidades)
- Triggers: "navegar", "clicar", "automatizar", "reconhecer elemento", "ver a tela", "executar no navegador/pc/celular", "screenshot"
