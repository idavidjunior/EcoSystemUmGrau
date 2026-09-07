---
tipo: episodio
tags: [spec, eco-client, runtime, python]
data: 2026-09-07
contexto: pedido de spec para cliente Python embutido sem mudar a UI
decisao: spec proposta em specs/eco-client-python.spec.md com API via import direto e stdlib pura
impacto: base pronta para implementar scripts/eco_client.py com reuso total do runtime
---

O runtime já tinha peças isoladas mas sem cliente único.
O maestro_client cobre só o maestro e os scripts exigem subprocesso.
A spec nova define EcoClient com boot e estado e memória e contexto.
Ela exige reuso por import direto e falha suave e sem git direto.
Ela está bem formada com onze seções e frontmatter válido.
Falta implementar o módulo e o teste de fumaça.

## Conexoes

- [[cluster-hub-programacao]]
- [[python-decoradores-e-metaprogramação]]
- [[python-gil-e-concorrência]]
- [[python-idioms-e-boas-práticas]]
- [[python-sintaxe-e-núcleo-da-linguagem]]