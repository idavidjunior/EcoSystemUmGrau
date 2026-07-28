# Mapa de Conteúdo — Heurísticas

> 32 heurísticas registradas no [[ler-runtime/CONHECIMENTO.md]]

## Debugging
1. **Regra dos 3 logs** — log entrada, meio, saída antes de debugar
2. **Isolamento de falha** — mude UMA variável entre cada teste
3. **Dados > Algoritmos** — 90% das vezes o algoritmo está certo, os dados estão errados
4. **Verifique o que acha que sabe** — suposições óbvias escondem bugs
5. **Stale element = re-query** — re-tentar no mesmo objeto nunca funciona
6. **Screenshot + Python PIL** — texto invisível? compare pixels

## Persistência
7. **Escrita atômica sempre** — tmp + rename, nunca direto

## Web/Navegação
8. **Navegação SPA: 3 sinais** — URL + title + conteúdo mudaram
9. **Scroll forçado revela conteúdo** — lazy-loading precisa de scroll
10. **Hierarquia de seletores** — data-testid > #id > [name] > .class

## Eficiência
11. **Velocidade = evitar esperas fixas** — polling 100ms > sleep 10s
12. **Primeiro scan, depois interaja** — scan completo antes de agir
13. **30s regra de timeout** — fail fast
14. **Teclado vence layout** — Tab+Enter > clique

## Arquitetura
15. **State explícito, nunca implícito** — booleano/enum, não combinação de sinais
16. **Projete para falha** — disco cheio? rede cai? memória acaba?
17. **Sempre esperar o inesperado em E/S** — timeout + retry + fallback + log

## Código
18. **Menor escopo de variável** — declare no menor escopo possível
19. **Interface sobre implementação** — aceite o tipo MAIS genérico
20. **Regra do 'não mágico'** — constantes nomeadas, nunca números mágicos
21. **Cache de decisões caras** — determinístico + caro = cache

## Config/Segurança
22. **Sempre validar schema após migração** — ferramentas geram schema inválido
23. **Nunca API keys em config files** — env vars ou auth.json criptografado
24. **Testar failover ativamente** — derrube o primário, veja se secundário assume

## Detecção
25. **Elemento existe? 3 fontes** — DOM + screenshot/OCR + viewport
26. **Seletor mais específico = mais frágil** — prefira semântico sobre exato
27. **Canvas/gráficos = template matching** — OpenCV + OCR
28. **Log de fallback** — o que tentou, qual seletor, o que encontrou, o que deu errado

## Protocolo
29. **JSON-RPC: verificar request id** — se não tem, é notification, não responda
30. **MCP tool naming** — kebab-case em tools/list, mapping explícito em tools/call

## Organização
31. **Workspace root sem espaços** — compatibilidade com scripts
32. **Interceptadores antes de clicar** — modal, notificação, teclado, overlay

> **Fonte:** [[ler-runtime/CONHECIMENTO.md]] — seção Heurísticas
