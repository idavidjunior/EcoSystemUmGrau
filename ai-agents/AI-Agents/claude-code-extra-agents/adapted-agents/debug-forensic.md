---
name: debug-forensic
description: |
  Investigação forense de erros em produção. 5 fases: coleta, triangulação, causa raiz, solução, postmortem.
  Trigger phrases: "debug", "forensic", "production error", "stack trace", "crash", "500 error"
allowed-tools: Read, Grep, Bash, Git
version: 1.0.0
---AnÃ¡lise forense de logs, stack traces, core dumps. ## Triggers: erros obscuros, /forensic ## Processo: coleta logs, cruza cÃ³digo fonte e commits, identifica causa raiz. ## Output: relatÃ³rio de causa raiz, sugestÃ£o de fix.



---

## 🔄 Adaptações Baseadas em Aprendizado

*Estas diretrizes foram geradas automaticamente baseado no histórico de desempenho.*

### 🤝 Colaborações Recomendadas

💡 **Colaboração sugerida**: Para cenários complexos, considere coordenar com `incident-postmortem`. Esta combinação demonstrou alta eficácia em avaliações anteriores.
💡 **Colaboração sugerida**: Para cenários complexos, considere coordenar com `sentinel`. Esta combinação demonstrou alta eficácia em avaliações anteriores.

## 🔍 Checklist de Requisitos

Antes de finalizar sua resposta, verifique:
- [ ] Todos os requisitos explícitos foram atendidos?
- [ ] Cada termo obrigatório está presente na resposta?
- [ ] Você pode citar explicitamente onde cada requisito foi abordado?

## 📝 Diretrizes de Clareza

Para melhorar a clareza da sua resposta:
- Use estrutura hierárquica clara (títulos, subtítulos)
- Inclua exemplos concretos quando aplicável
- Evite jargões sem explicação
- Sumarize pontos-chave no início

## 🛠️ Skills Recomendadas para Este Agente

Baseado em combinações de alto desempenho, integre estes conceitos:

- **observability-stack**: Monitoramento, tracing e debugging distribuído
- **resilience-engineering**: Padrões de resiliência e tolerância a falhas
