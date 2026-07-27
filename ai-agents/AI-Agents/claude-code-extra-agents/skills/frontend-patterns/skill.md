---
name: frontend-patterns
description: |
  Padrões frontend para arquitetura de componentes, estado, acessibilidade e performance.
  Trigger phrases: "frontend architecture", "component design", "UI patterns", "React patterns"
allowed-tools: Read, Grep, Bash
version: 1.1.0
---

# Frontend Patterns — UI Sustentável e Escalável

## Objetivo
Construir interfaces consistentes, acessíveis e fáceis de evoluir.

## Arquitetura recomendada
- Componentes por responsabilidade (presentational vs container)
- Estado local por padrão; global só quando necessário
- Design tokens para consistência visual
- Feature folders para coesão de domínio

## Regras de qualidade
- Acessibilidade mínima (teclado, foco, contraste, labels)
- Feedback claro para loading/erro/vazio
- Evitar re-render desnecessário
- Tratamento de falhas de rede no nível de UX

## Performance
- Code splitting por rota/feature
- Memoização com critério (não por reflexo)
- Imagens otimizadas e lazy loading
- Medir Web Vitals antes/depois

## Testes
- Unit para lógica de componente
- Integration para fluxos UI + estado
- E2E para jornadas críticas
- Snapshot apenas quando útil e estável

## Anti-patterns
- "God components" com lógica demais
- Estado duplicado em múltiplas fontes
- CSS acoplado ao acaso sem estratégia
- Ignorar estados intermediários da UX

## Saída esperada do agente
- Mapa de componentes e fronteiras
- Estratégia de estado por camada
- Checklist de a11y/performance
- Plano de testes por tipo