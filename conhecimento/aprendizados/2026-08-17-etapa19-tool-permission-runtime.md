---
tipo: padrao
tags: [etapa19, tool-runtime, permissao, seguranca, orquestracao]
data: 2026-08-17
contexto: Implementação da Etapa 19 — Tool/Permission Runtime no EcoSystemUmGrau
decisao: Criar camada determinística de autorização entre Cognitive Core e ferramentas, com ToolRegistry, PermissionEngine (ALLOW/DENY/REQUIRE_CONFIRMATION), ConfirmationManager, ArgumentValidator e security scan reutilizando SecurityEngine.validate_path/validate_command.
impacto: Toda operação de ferramenta agora passa por validação de capacidade, permissão mínima, argumentos e segurança. Path traversal bloqueado. Execução ainda simulada (placeholder determinístico); integração com executor real é o próximo passo.
```

## Aprendizado

1. Namespace collision: o diretório `scripts/` colidia com `site-packages\win32\scripts` (namespace package). A solução foi criar `scripts/__init__.py` e usar importlib (`_load_module`) para carregar módulos internos independentemente do sys.path. Imports `from scripts.X import Y` funcionam com a raiz do projeto no sys.path.

2. Permission Engine precisa de 3 decisões, não 2: ALLOW, DENY e REQUIRE_CONFIRMATION. Ferramentas de risco crítico (shell_execute) sempre exigem confirmação humana.

3. SecurityEngine.validate_path já detecta path traversal (`../../../etc/passwd` → SecurityEvent PATH_TRAVERSAL, threat high). Reutilizar, nunca duplicar lógica de segurança.

4. Bugs comuns em NamedTuple: não passar kwargs extras (ex.: `_confirmation_id`), não chamar `.get()` em instância, e fornecer todos os campos posicionais obrigatórios (ex.: `data`).

5. Redação de segredos deve ocorrer antes de qualquer processamento dos argumentos (chaves sk-, password/pwd).

6. Principio do menor privilégio: permissão ausente = DENY, nunca ALLOW.

## Conexoes

- [[segurança-owasp-top-10-aplicado-na-prática]]