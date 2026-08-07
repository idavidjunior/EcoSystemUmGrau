# Política de Retenção e Exclusão de Dados — EcoSystemUmGrau

**Cláusula Pétrea de Deveres Externos, Art. 7:** dados são mantidos apenas pelo tempo necessário, com plano de retenção e mecanismo de exclusão efetivo.

**Versão:** 1.0
**Status:** Obrigatória

---

## 1. Princípios

1. **Mínimo necessário:** coleta-se apenas o que é indispensável para a função.
2. **Finalidade limitada:** dados são usados somente para a finalidade informada.
3. **Retenção mínima:** dados são apagados assim que a finalidade se esgota.
4. **Exclusão garantida:** todo dado deve ter mecanismo efetivo de exclusão.

## 2. Categorias de dados e prazos de retenção

| Categoria | Exemplos | Prazo máximo | Ação ao esgotar |
|-----------|----------|--------------|-----------------|
| **Logs operacionais** | eventos.jsonl, health reports, guardian.log | 30 dias | Apagar/rotacionar automaticamente |
| **Sessões de conversa** | sessions/*.jsonl | 90 dias | Anonimizar ou apagar |
| **Memórias de trabalho** | memories.json, aprendizado | 180 dias | Revisar e consolidar; apagar obsoletas |
| **Áudio (voz/TTS/STT)** | gravações, transcrições temporárias | 7 dias | Apagar após transcrição, salvar apenas texto |
| **Configurações locais** | bridge_config.json, .env | Enquanto ativo | Apagar ao desativar o serviço |
| **Credenciais** | auth.json, keys/ | Enquanto válidas | Rotacionar e apagar revogadas |
| **Dados biométricos** | (se existir) | Proibido por padrão | Não coletar |
| **Dados de crianças** | (se existir) | Proibido por padrão | Não coletar |

## 3. Mecanismos de exclusão

### Rotação automática de logs
```bash
# Executar diariamente (ou via watchdog):
python scripts/preflight_etica.py --data-inventory   # re-mapa dados
python scripts/rotacao_dados.py                      # aplica prazos acima
```

### Exclusão manual
```powershell
# Apagar dados antigos por categoria
Remove-Item connectivity/bridge/health/*.json -Force          # reports
Remove-Item connectivity/bridge/events.jsonl -Force           # eventos
Remove-Item "conhecimento/memoria/sessions/*.jsonl" -Force    # sessões antigas
```

## 4. Direitos do titular (LGPD Art. 18)

- **Acesso:** permitido sempre que solicitado.
- **Correção:** dados incorretos são corrigidos imediatamente.
- **Exclusão:** o titular pode solicitar exclusão a qualquer momento.
- **Oposição:** o titular pode se opor ao processamento.
- **Portabilidade:** exportar em formato aberto sob pedido.

## 5. Incidentes de dados

Todo vazamento, uso indevido ou acesso não autorizado deve ser:
1. Registrado na memória como `erro` (via `memory_engine.py`).
2. Tratado com prioridade máxima (mesma de uma falha crítica).
3. Informado ao titular afetado quando houver risco relevante.

## 6. Conformidade

- Brasil: **LGPD** (Lei 13.709/2018).
- União Europeia: **GDPR** (Regulamento 2016/679) quando aplicável.

Esta política é auditada pelo `preflight_etica.py` em toda entrega.
