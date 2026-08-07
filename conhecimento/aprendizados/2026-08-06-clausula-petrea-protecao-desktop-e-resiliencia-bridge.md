---
tipo: decisao
tags: [resiliencia, watchdog, opencode, desktop, bridge, clausula-petrea, android]
data: 2026-08-06
contexto: "Usuario exigiu que nenhum processo automatico possa fechar o OpenCode desktop — apenas o usuario manualmente. Testes de resiliencia do bridge (que morria sem log) revelaram que o watchdog podia derrubar o desktop por erro de filtro."
decisao: "Corrigir watchdog.ps1 com protecao absoluta do desktop (clausula petrea) e robustez de instancia unica via lock de PID. Reestruturar saudacoes do bridge com estado persistente."
impacto: "Bridge e serve se auto-recuperam em <60s apos queda. Desktop OpenCode jamais e fechado automaticamente. Saudações variam entre primeira vez e reconexao."
---

# Clausula Petrea: protecao do OpenCode desktop + resiliencia da bridge

## Regra imutavel (clausula petrea)
**Em hipotese alguma, o Windows ou qualquer outro processo automatico pode fechar o
OpenCode desktop. Somente o usuario pode, manualmente.**

- O desktop roda como `OpenCode.exe` em `@opencode-aidesktop`.
- O CLI roda como `opencode.exe` (serve na porta 8767, run em sessoes).

## Bug critico encontrado
O filtro antigo de orfaos do watchdog matava qualquer `opencode.exe` cujo comando
NAO contivesse " serve":
```powershell
$cmd -match "opencode\.exe run" -or ($cmd -match "opencode\.exe" -and $cmd -notmatch " serve")
```
O desktop (`OpenCode.exe`) casa no segundo criterio (nao tem " serve" no comando),
entao o proprio watchdog poderia derrubar o desktop. **Corrigido** com protecao
explicita por caminho (`opencode-aidesktop`) e filtro restrito a `opencode run`.

## Melhorias no watchdog.ps1
1. **Instancia unica via lock de PID** (`watchdog.lock`): substitui o Mutex nomeado,
   que no Windows fica "abandoned" quando o processo dono e morto e NAO e re-adquirido
   — o que travava qualquer restart do watchdog.
2. **Health-check do bridge** (`Test-BridgeAlive`): verifica porta LISTENING + processo
   dono vivo. Detecta socket orfao (porta ocupada por processo morto) e limpa.
3. **Serve com health HTTP** (`/global/health` + Basic Auth): so considera saudavel se
   responde, nao apenas se a porta escuta.
4. **Log com limite de 2MB**: ao estourar, descarta a metade mais antiga.
5. **Filtro de orfaos seguro**: so mata `opencode.exe run` (CLI), nunca o desktop.

## Reestruturacao das saudacoes (jarvis_bridge.py)
- **Estado persistente** `saudacao_estado.json`: conexoes, saudoes_hoje (max 10),
  ultima_saudacao, ultima_saudacao_ts.
- **`_classificar_conexao()`**: distingue PRIMEIRA vez de RECONEXAO usando 3 fontes:
  (1) estado de saudoes (ja saudou hoje?), (2) atividade persistida via
  `_marcar_atividade()` (atualizada a cada mensagem real, cobre o caminho rapido),
  (3) mtime do conversa_unica.json.
- **Prompt do LLM diferenciado**: reconexao = retomada curta de conversa, sem briefing,
  sem "como posso ajudar", com lista de saudoes ja usadas para evitar repeticao.
- **Fallback variado**: reconexao usa frases de retomada ("De volta, senhor...");
  primeira vez usa o molde antigo com briefing.
- Timeout da saudacao: 25s -> 90s (evita timeout no cold start do modelo).

## Testes realizados (100%)
1. **Recuperacao do bridge**: derrubado -> watchdog restaurou em <60s (novo PID).
2. **Recuperacao do serve**: derrubado -> watchdog restaurou em <60s (novo PID).
3. **Desktop intocado**: 8 processos `OpenCode.exe` permaneceram apos as quedas.
4. **Saudacoes**: 3 conexoes seguidas geraram 3 saudações distintas; a reconexao
   retornou "De volta, senhor. Continuando de onde paramos." e "Voltou. Sistemas
   seguem quentes, é só falar." — reconhecendo a retomada.
5. **Watchdog duplicado**: lock de PID impede duas instancias concorrentes.

## Monitoramento
- Log do watchdog: `scripts/watchdog_log.txt` (limitado a 2MB).
- Log do bridge: `scripts/bridge_log.txt`.
- Estado de saudoes: `scripts/saudacao_estado.json`.
- Estado do bridge: `scripts/bridge_estado.json`.
