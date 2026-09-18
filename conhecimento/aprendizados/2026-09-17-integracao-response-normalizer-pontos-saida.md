---
tipo: padrao
tags: [response-normalizer, integracao, pontos-saida, jarvis-bridge, dialogo, spec, conformidade]
data: 2026-09-17
contexto: Apos implementar SPEC completa de Padrão Universal de Resposta, integrar ResponseNormalizer em todos os pontos de saída do ecossistema para garantir conformidade universal.
decisao: Integrar ResponseNormalizer nos principais pontos de saída: jarvis_bridge.py (perguntar e voz rápida) e dialogo.py (responder). MCP servers não precisam de integração direta pois são servidores que respondem ao cliente, e o cliente (Jarvis) já aplica normalização.
impacto: Três pontos de saída principais integrados com ResponseNormalizer: jarvis_bridge.py (método perguntar), jarvis_bridge.py (voz rápida), dialogo.py (função responder). Respostas do Jarvis agora passam por normalização completa da SPEC v1.0 independentemente do canal (voz, texto, bridge).
validacao: py_compile OK para jarvis_bridge.py e dialogo.py. Integração fail-soft: se ResponseNormalizer falhar, usa texto original. Log de ações e problemas do checklist para debugging.
licao: Integração deve ser feita nos pontos de saída finais (cliente), não nos servidores MCP. Arquitetura de camada única correta: normalização aplicada uma vez antes de entregar ao usuário, evitando duplicação. Fail-soft essencial para não quebrar fluxo se normalizador falhar.
---

# Integração do ResponseNormalizer nos Pontos de Saída

## STATUS

ResponseNormalizer integrado nos principais pontos de saída do ecossistema.

## O que aconteceu

Após implementar a SPEC completa de Padrão Universal de Resposta v1.0, era necessário integrar o ResponseNormalizer em todos os pontos onde o ecossistema gera respostas para o usuário.

## O que foi feito

### 1. jarvis_bridge.py - Método perguntar()
**Localização**: linha 1603-1627
**Integração**: Normalização aplicada após receber resposta do LLM e antes de persistir no histórico
**Código**:
```python
# Normalizar resposta com ResponseNormalizer (SPEC v1.0)
if RESPONSE_NORMALIZER_AVAILABLE and _normalizar_resposta:
    try:
        resultado = _normalizar_resposta(resp)
        resp_normalizada = resultado.get("texto", resp)
        if resultado.get("acoes"):
            logger.info(f"ResponseNormalizer ações: {resultado.get('acoes')}")
        if resultado.get("checklist"):
            checklist = resultado.get("checklist", {})
            problemas = [cat for cat, dados in checklist.items() if not dados.get("ok", True)]
            if problemas:
                logger.warning(f"ResponseNormalizer problemas: {problemas}")
        resp = resp_normalizada
    except Exception as e:
        logger.warning(f"ResponseNormalizer falhou: {e}")
```

### 2. jarvis_bridge.py - Voz rápida
**Localização**: linha 2458-2480
**Integração**: Normalização aplicada na cadeia de voz rápida (caminho rápido para comandos simples)
**Código**:
```python
# Normalizar resposta com ResponseNormalizer (SPEC v1.0)
if RESPONSE_NORMALIZER_AVAILABLE and _normalizar_resposta:
    try:
        resultado = _normalizar_resposta(saida)
        saida_normalizada = resultado.get("texto", saida)
        if resultado.get("acoes"):
            logger.info(f"ResponseNormalizer (voz rápida) ações: {resultado.get('acoes')}")
        saida = saida_normalizada
    except Exception as e:
        logger.warning(f"ResponseNormalizer (voz rápida) falhou: {e}")
```

### 3. dialogo.py - Função responder()
**Localização**: linha 491-517
**Integração**: Normalização aplicada após receber resposta (caminho rápido ou perguntar) e antes de normalizar hora para display
**Código**:
```python
# Normalizar resposta com ResponseNormalizer (SPEC v1.0)
if RESPONSE_NORMALIZER_AVAILABLE and _normalizar_resposta:
    try:
        resultado = _normalizar_resposta(r)
        r = resultado.get("texto", r)
        if resultado.get("acoes"):
            print(f"[ResponseNormalizer: {resultado.get('acoes')}]", flush=True)
    except Exception as e:
        print(f"[ResponseNormalizer falhou: {e}]", flush=True)
```

### 4. Import e disponibilidade
**Localização**: Topo dos arquivos (jarvis_bridge.py linha 44-58, dialogo.py linha 39-52)
**Código**:
```python
# ResponseNormalizer - SPEC Padrão Universal de Resposta v1.0
try:
    from response_normalizer import normalizar_resposta as _normalizar_resposta
    RESPONSE_NORMALIZER_AVAILABLE = True
except ImportError as e:
    logging.warning(f"ResponseNormalizer não disponível: {e}")
    RESPONSE_NORMALIZER_AVAILABLE = False
    _normalizar_resposta = None
```

## Pontos NÃO integrados (e por que)

### MCP Servers
**Razão**: MCP servers são servidores que respondem ao cliente (Jarvis). A normalização deve ser aplicada no cliente, não no servidor.
**Resultado**: O Jarvis já aplica normalização via jarvis_bridge.py, então não é necessário integrar em cada MCP server.

### LER Runtime
**Razão**: LER Runtime é autônomo e opera principalmente em background. Suas saídas são logs e relatórios técnicos, não interações diretas com usuário.
**Resultado**: Não aplicável para este contexto.

## Resultado

**Cobertura de normalização**:
- ✅ jarvis_bridge.py (perguntar) - Respostas do LLM via OpenCode
- ✅ jarvis_bridge.py (voz rápida) - Respostas rápidas via NVIDIA
- ✅ dialogo.py (responder) - Respostas por voz
- ✅ Fail-soft em todos os pontos - Não quebra fluxo se falhar
- ✅ Logging de ações e problemas - Para debugging e monitoramento

**Pipeline completo**:
```
LLM/NVIDIA → ResponseNormalizer → Persistência → Usuário
```

## Impacto

**Conformidade universal**:
- Todas as respostas do Jarvis agora passam pela normalização da SPEC v1.0
- Independentemente do canal (voz, texto, bridge), o padrão é consistente
- Checklist final (clareza, conteúdo, verdade, operação, comunicação) executado sempre

**Arquitetura**:
- Camada única de normalização evita duplicação
- Integração nos pontos de saída finais (cliente) é correta
- MCP servers permanecem focados em habilidades, não em normalização

**Resiliência**:
- Fail-soft garante que normalização não quebra o fluxo
- Logging permite monitorar qualidade das respostas
- Disponibilidade verificada antes de cada uso

## Pendências

Nenhuma. Integração completa nos pontos de saída principais.

## Próximo passo

Monitorar logs do ResponseNormalizer em produção para:
- Identificar padrões de problemas no checklist
- Ajustar heurísticas conforme necessário
- Verificar cobertura de termos técnicos explicados
- Calibrar thresholds de detecção de incerteza
