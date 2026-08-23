---
tags: [engenharia, features, menor, novas, padrao, terreno]
aliases: [Engenharia: refactoring seguro]
date: 2026-08-23
---

# Engenharia: refactoring seguro

**Fonte:** engenharia

Refactoring é mudar a estrutura interna do código **sem mudar seu comportamento observável**, com objetivo de melhorar legibilidade, manutenibilidade ou preparar terreno para novas features. Segurança vem de disciplina, não de coragem.

### Pré-requisito absoluto: rede de segurança
Nunca refatore sem conseguir detectar regressão. A **characterization test** captura o comportamento atual quando não há testes:
```
# antes de tocar, registre o comportamento real
for caso in gerar_entradas():          # inclua casos bizarros e válidos
    snapshot.append((caso, funcao(caso)))  # valores, exceções, efeitos
```
Rode, salve o snapshot, refatore, rode de novo: a diferença indica regressão.

### Estratégia em pequenos passos
Cada passo deve ser **combinável, testável e reversível**:
1. Escolha UMA transformação de cada vez (extrair método, renomear, mover, substituir condição por polimorfismo, extrair constante).
2. Rode os testes após cada passo (devem ficar verdes).
3. Se algo quebrar, reverta o último passo e reduza a mudança.

### Transformações comuns (refactoring catalog)
- **Extract Method / Inline Method**: isolar blocos com responsabilidade única.
- **Rename**: nomes que dizem o que fazem e por quê.
- **Introduce Parameter / Extract Variable**: remover números mágicos e expressões repetidas.
- **Replace Conditional with Polymorphism**: eliminar `if/switch` de tipo para distribuir comportamento.
- **Separate Query from Modifier**: funções que só leem vs funções que só escrevem.
- **Replace Magic Number with Constant / Enum**.

### Regras que salvam o dia
- **Não misture refactor com feature**: um diff que reestrutura e muda comportamento é impossível de revisar e difícil de debugar.
- **Refatore o código que vai ser tocado**, não por hobby: foco em hotspots (complexidade ciclomática alta, bugs recorrentes).
- **Commits pequenos** com mensagens do tipo “refactor: extrai validação de senha em PasswordPolicy.validate”.
- Use ferramentas automáticas (IDE rename, language server, codemods) sempre que possível — reduzem erro humano.
- Respeite o “rule of three”: abstraia na terceira ocorrência da mesma duplicação.

### Quando NÃO refatorar
- Sem testes de segurança disponíveis e sem condição de criá-los (legado morto).
- Em momento de pressão de prazo sem margem de reversão.
- Código que será reescrito/removido em breve.

**Métrica**: o bom refactor é invisível — nenhum teste muda de resultado, o comportamento externo permanece idêntico e o diff de features fica menor.
## Conexoes

- [[cluster-hub-programacao]]
- [[engenharia-code-review-eficaz]]
- [[engenharia-documentação-que-não-vira-lixo-adr-readme-vivo-co]]
- [[engenharia-dívida-técnica-e-manutenibilidade]]
- [[engenharia-requisitos-e-definição-de-escopo]]
- [[padrao-hub-padroes]]