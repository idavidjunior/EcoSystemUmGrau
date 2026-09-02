# Jurisprudências do Ecossistema

Regras que sobreviveram ao teste de evidência temporal e aguardam promoção a cláusula pétrea.

Critérios de promoção (ciclo de governança):
- REGRA EXPERIMENTAL → JURISPRUDÊNCIA: 14+ dias sem violação, métricas monitoradas, correção automática de desvios demonstrada.
- JURISPRUDÊNCIA → CLÁUSULA PÉTREA: 30+ dias adicionais como jurisprudência, aprovação do Conselho Permanente (ou 3 agentes especialistas independentes), violação causando dano comprovado.
- REBAIXAMENTO: 2+ violações em 7 dias → rebaixa para experimental. Cláusula pétrea em revisão (não rebaixa automaticamente).

---

## 1. Ponto Único de Persistência (Gate)

**Status:** JURISPRUDÊNCIA
**Data de origem:** 2026-08-31 (cláusula pétrea na Constituição)
**Data de auditoria:** 2026-09-02 (correção do ecosystem.ps1)
**Evidência:**
- Adesão monitorada via `adherence_audit.py` (gate_persistencia_min)
- Última violação: 2026-09-02 06:43 (commit [ecosystem learn] fora do gate, hash 3173e01eb)
- Correção aplicada: ecosystem.ps1 repair/learn delegam ao gate (commit aca2e0997)
- Dias sem violação desde a correção: 0 (corrigido hoje)
- Exceção documentada: compiladorAPK (CI de build, push forçado em TempDir efémero)

**Critérios de manutenção:**
- adherence_audit.py rodando diariamente
- gate_persistencia_min >= 1.0 por 14+ dias consecutivos
- Qualquer desvio gera alerta automático e correção

**Observações:**
- O gate já existia como cláusula pétrea na Constituição antes da auditoria
- A auditoria de 2026-09-02 revelou que a cláusula não era seguida integralmente (ecosystem.ps1)
- A correção restaurou a integridade da cláusula
- Este precedente documenta o ciclo completo: cláusula → falha → detecção → correção → evidência → jurisprudência
