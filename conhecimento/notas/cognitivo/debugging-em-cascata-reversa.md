---
tags: [caminho, cognitivo, conexao, debugging, entrada, inverso]
aliases: [Debugging em cascata reversa]
date: 2026-08-04
---

# Debugging em cascata reversa

**Dominio:** debugging

Quando um bug nao tem causa obvia, comeca pela saida (sintoma) e traca o caminho inverso ate a entrada. Para cada passo, pergunte: 'Se este componente funcionasse corretamente, o que eu veria?' Quando a resposta nao corresponde a realidade, voce encontrou o componente defeituoso. Mais eficiente que debugar pra frente porque elimina ramos inteiros da arvore de causas.

Quando metodo A falha, nao repetir A - descer para metodo B imediatamente. Ex: click() falhou? Tenta keyboard. Keyboard falhou? Tenta JS executor. JS falhou? Tenta OCR. Cada nivel e mais lento mas mais robusto

Quando um cliente diz connected mas ferramentas nao funcionam, o problema geralmente esta no handshake ou na violacao de protocolo - nao na conexao em si. Testar com sequencia manual (initialize -> notification -> tools/list) isola o problema.
## Conexoes

- [[cluster-hub-cognicao]]
- [[cognitivo-hub-cognitivo]]
- [[diagnostico-por-eliminacao-em-config-complexa]]
- [[encoding-aware-diagnostics]]
- [[hipotese-falsificacao-terminal]]
- [[principio-da-separacao-causa-efeito-temporal]]