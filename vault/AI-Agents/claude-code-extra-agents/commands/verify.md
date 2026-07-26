# /verify — Verificador de Código IA
Aciona o agente ai-code-verifier para revisar código gerado por IA antes do merge.

## Uso
`/verify`

## O que acontece
1. Analisa o código em busca de vulnerabilidades (SQL injection, XSS, secrets)
2. Detecta erros de lógica (null handling, race conditions, timezone)
3. Identifica alucinações (APIs inexistentes, imports errados)
4. Classifica achados: CRÍTICO, ALTO, MÉDIO, BAIXO
5. Sugere correção para cada achado

## Quando usar
- Código gerado por Copilot, ChatGPT, Claude ou similar
- PR com grandes blocos de código novo
- Antes de merge para main/master

## Exemplo
`/verify`
"Revise o arquivo payment-service.ts gerado pelo Copilot"
