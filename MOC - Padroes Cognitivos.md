# Mapa de Conteúdo — Padrões Cognitivos

> 22 padrões registrados no [[ler-runtime/CONHECIMENTO.md]]

## Debugging
1. **Cascata reversa** — comece pela saída, trace caminho inverso até a entrada
2. **Hipótese-falsificação terminal** — execute o experimento MAIS RÁPIDO que FALSIFICA a hipótese
3. **Causa-efeito-temporal** — em sistemas async, a CAUSA pode ter ocorrido muito antes do EFEITO
4. **Diagnóstico por eliminação** — isolar cada camada em config complexa

## Design de Sistemas
5. **Postel aplicado** — conservador no output, liberal no input
6. **Fallback em cadeia** — Chain of Responsibility: melhor resultado, não primeiro
7. **Escrita atômica** — tmp + rename, atomicidade garantida pelo FS
8. **Loop autônomo** — planejar → executar → verificar → corrigir
9. **Scoring multi-resultado** — thresholds por modo, melhor score, null se nenhum atingir

## Testes
10. **Teste o erro, não o acerto** — entrada vazia, limite, fora de domínio, estado inconsistente

## UI/UX
11. **Pattern matching por estrutura** — header+body+footer = modal, thead+tbody = tabela
12. **Digitalização por zonas** — topo=header, esquerda=sidebar, centro=conteudo, fundo=modais
13. **Elementos-chave de estado** — spinner=loading, "Nenhum resultado"=empty, vermelho=erro

## Web
14. **Modelo mental de DOM virtual** — SPAs têm DOM virtual ≠ DOM real
15. **Reconhecimento instantâneo de framework** — #root=React, #app=Vue, <app-root>=Angular
16. **Antecipação de comportamento adaptativo** — interfaces mudam layout, nunca assuma posição
17. **Mapa mental de navegadores** — multi-processo: browser + renderer + GPU

## Planejamento
18. **Pre-compilação de estratégia** — sequence complete + barreiras antes de agir
19. **Ciclo OODA** — Observe → Orient → Decide → Act (<1s familiar, <3s desconhecido)
20. **Heurística de densidade** — tela densa = info escondida em accordion/tab/modal

## Performance
21. **Espera adaptativa por recurso** — HTML (rede) > CSS (parse) > JS (execute) > imagens (não-bloq)

## Meta
22. **Lei de Postel** — seja conservador no output, liberal no input
