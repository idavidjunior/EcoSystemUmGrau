# Habilidade: Perfil Adaptativo do Usuário

## Visão Geral
Sistema de perfil que aprende preferências do usuário implicitamente a partir das interações e adapta automaticamente o comportamento dos agentes (formato, verbosidade, tom, nível técnico).

## Arquivos
- `scripts/user_profile.py` — Core do perfil (persistência, aprendizado, config)
- `scripts/profile_hook.py` — Hook para aplicar preferências nas respostas
- `runtime/user_profile.json` — Persistência do perfil
- `runtime/user_interactions.jsonl` — Log de interações para análise

## Configuração Padrão (aprendida do usuário)
```json
{
  "style": {
    "verbosity": "direct",
    "format": "plain",
    "tables": false,
    "lists": "dash",
    "code_blocks": false
  },
  "tone": {
    "technical_level": "intermediate",
    "formality": "casual",
    "language": "pt-BR"
  }
}
```

## Como os Agentes Devem Usar

### 1. No início de cada resposta, consultar o perfil
```python
from scripts.profile_hook import get_response_config
config = get_response_config()
# config contém: use_markdown, use_tables, verbosity, technical_level, etc.
```

### 2. Aplicar preferências na resposta
```python
from scripts.profile_hook import format_response_for_profile
response = format_response_for_profile(raw_response, config)
```

### 3. Registrar interação para aprendizado
```python
from scripts.profile_hook import record_interaction
record_interaction(user_text, agent_response, metadata={"task": "..."})
```

### 4. Aplicar correções explícitas do usuário
```python
from scripts.profile_hook import apply_correction
apply_correction("no_markdown")  # ou "direct_only", "technical", "simple", etc.
```

## Correções Suportadas
- `no_markdown` → desativa markdown, code_blocks, tables
- `direct_only` → verbosity=direct, format=plain
- `technical` → technical_level=advanced
- `simple` → technical_level=basic
- `formal` / `casual` → ajusta formalidade
- `no_code_announcement` → não anunciar blocos de código

## Aprendizado Implícito
O perfil detecta automaticamente:
- Correções do usuário ("não use markdown", "sem formatação", "direto")
- Comandos frequentes (/comando, @comando)
- Tópicos de interesse (palavras-chave técnicas)
- Formatos rejeitados (marcados quando usuário corrige)

## Comandos Disponíveis
```bash
/perfil stats          # estatísticas do perfil
/perfil config         # configuração atual de resposta
/perfil correct X      # aplica correção (ex: no_markdown)
python scripts/user_profile.py stats
python scripts/user_profile.py config
python scripts/user_profile.py correct no_markdown
```

## Integração com Agentes
Todo agente DEVE:
1. Consultar `get_response_config()` antes de responder
2. Aplicar `format_response_for_profile()` na resposta final
3. Chamar `record_interaction()` após cada troca
4. Respeitar correções do usuário imediatamente via `apply_correction()`

## Persistência
- Perfil salvo em `runtime/user_profile.json` (atomic write)
- Log de interações em `runtime/user_interactions.jsonl`
- Sincronizado via `persistencia.ps1` (gate único)

## Próximos Passos
- [ ] Integração automática no loop de agentes do opencode
- [ ] Dashboard visual do perfil (`/perfil dashboard`)
- [ ] Export/import de perfil entre máquinas
- [ ] Detecção de mudança de contexto (projeto/tarefa)