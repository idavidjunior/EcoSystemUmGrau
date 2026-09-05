---
tags: [fim, nasce, object, opencode, padrao, pelo]
aliases: [Janela flutuante para visuais (sem navegador)]
date: 2026-08-24
---

# Janela flutuante para visuais (sem navegador)

**Fonte:** opencode

## Causa raiz do fechamento misterioso
Processos filhos da sessao de comando sao mortos por job object quando o
comando pai termina. O Start-Process normal tambem morre. Nao foi automacao
do ecossistema. Alem disso a associacao .html do Windows aponta para o
Internet Explorer descontinuado, que redireciona/fecha.

## Solucao validada (2026-08-24)
1. Motor de janela: chrome.exe --app=file:///... (janela standalone sem
   barras nem abas; CSS grid moderno funciona). Edge ausente nesta maquina;
   chrome em C:\Program Files\Google\Chrome\Application\chrome.exe.
2. Lancamento: Invoke-CimMethod Win32_Process Create — o processo nasce pelo
   servico WMI, fora da arvore da sessao, e sobrevive.
3. Teste: duas janelas lancadas, ambas vivas apos o fim dos scripts.

## Uso
python scripts/gerador_visual.py --titulo "..." --tipo kpi --arquivo dados.json --mostrar

## Nota de sistema
Associacao .html -> iexplore.exe esta quebrada na maquina do usuario.
Correcao da associacao depende de decisao dele
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[padrao-hub-padroes]]
- [[secrets-guard-no-preflightcheck]]