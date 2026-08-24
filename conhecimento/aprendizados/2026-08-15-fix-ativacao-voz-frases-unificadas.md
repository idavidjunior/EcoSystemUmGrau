---
tipo: padrao
tags: [jarvis, widget, voz, frases, anti-repeticao, autoevolutivo, unificacao, bridge]
data: 2026-08-15
contexto: "Usuário ativou a voz e o Jarvis narrou histórico passado (bug: narrador não resetava posição). Também queria frases variadas na ativação/desativação, feedback de voz em ações do widget (mic, interromper, minimizar, topo/trás), e unificação com o sistema de saudações da bridge."
decisao: "1) Reset de posição do narrador ao ativar voz (narrador_posicao.json = timestamp atual). 2) Sistema de frases variadas autoevolutivo para ativação, desativação e 6 ações do widget. 3) Módulo unificado frases_manager.py compartilhado entre widget e bridge. 4) Anti-repetição por dia + aprendizado de novas frases + persistência atômica."
impacto: "Voz ativada não narra mais histórico; frases variam naturalmente; widget fala feedback em todas as ações; bridge e widget compartilham lógica de saudações e classificação de conexão."
---

# Fix ativação de voz + Sistema de frases unificado

## Problemas resolvidos

### 1. Narrador falava histórico passado ao ativar voz
**Causa**: `narrador_desktop.py` lê `narrador_posicao.json` (último timestamp processado). Ao ativar voz, continuava de onde parou.
**Fix**: `cmd_voz(True)` agora chama `_resetar_posicao_narrador()` que grava `ultimo_ts = now()` em ms no `narrador_posicao.json`. Narrador passa a ler apenas mensagens **novas** a partir da ativação.

### 2. Frase fixa "Voz ativada" repetitiva
**Fix**: Pool de 8 frases base + aprendizado automático. Não repete no dia (`usadas_hoje`). Persiste em `runtime/frases_ativacao.json`.

### 3. Sem feedback de voz nas ações do widget
**Fix**: 6 ações ganharam frases variadas:
- `mic_on` / `mic_off` — microfone
- `interromper` — parar fala
- `minimizar` — esconder janela
- `topo` / `tras` — Z-order

### 4. Duplicação de lógica anti-repetição (widget vs bridge)
**Fix**: Módulo unificado `scripts/frases_manager.py`:
- `FraseManager` — classe genérica para qualquer ação
- Estado compartilhado `saudacao_estado.json` (bridge + widget)
- `classificar_conexao()` — 3 fontes: saudações hoje, atividade recente, mtime conversa
- `registrar_saudacao()`, `obter_saudacoes_hoje()`, `marcar_atividade()`

## Arquivos criados/modificados

### Novo: `scripts/frases_manager.py`
Gerenciador centralizado de frases. Instâncias pré-configuradas:
```python
frases_ativacao, frases_desativacao, frases_mic_on, frases_mic_off,
frases_interromper, frases_minimizar, frases_topo, frases_tras
```

### Modificado: `scripts/widget_controle_jarvis.py`
- Importa de `frases_manager` (removeu ~200 linhas de código duplicado)
- `_resetar_posicao_narrador()` chamado em `cmd_voz(True)`
- `_falar_acao(acao)` em: `cmd_interromper_fala`, `cmd_mic`, `_minimizar`, `_fixar_no_topo`, `_enviar_para_tras`
- Aliases de compatibilidade: `_escolher_frase_ativacao()`, `_escolher_frase_desativacao()`, `_escolher_frase_acao()`, `_aprender_frase_*()`

## Padrão de uso (para novas ações)

```python
from frases_manager import FraseManager

minha_acao = FraseManager("minha_acao", ["Opção 1", "Opção 2", "Opção 3"])

# Usar:
frase = minha_acao.escolher()
minha_acao.aprender("Nova frase do usuário")
estado = minha_acao.estado()  # debug
```

## Persistência
- Um JSON por ação em `runtime/frases_<acao>.json`
- Escrita atômica (tmp + replace) — sem corrupção
- Reset diário automático via campo `ultima_data`
- Histórico global (`historico`) aprende frases novas (max 50)

## Validação
```bash
# Teste frases_manager
python -c "from frases_manager import frases_ativacao; [print(frases_ativacao.escolher()) for _ in range(5)]"

# Teste widget integração
python -c "from widget_controle_jarvis import _escolher_frase_ativacao, _escolher_frase_acao; print(_escolher_frase_ativacao(), _escolher_frase_acao('mic_on'))"

# Compilação
python -m py_compile scripts/widget_controle_jarvis.py scripts/frases_manager.py
```

## Memórias relacionadas
- #302 (padrao): Fix ativação de voz: reset posição narrador + frases variadas
- #131 (padrao): Saudacoes inteligentes (reconexao vs primeira vez) — base do `saudacao_estado.json`

## Conexoes

- [[2026-08-04-tamanho-por-uso-real-iniciar-gui-com-pythonw-impl]]
- [[aprendizado-2026-07-31-horas-faladas-corretamente-no-tts-do-]]