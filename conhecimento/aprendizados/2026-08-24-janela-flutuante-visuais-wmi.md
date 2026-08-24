---
tipo: padrao
tags: [visual, janela-flutuante, wmi, chrome-app, bug-fechamento]
data: 2026-08-24
contexto: David reportou que a janela do visual abria e fechava sozinha e pediu visual sem navegador, tipo janela flutuante
decisao: chrome.exe --app como motor de janela + WMI Win32_Process.Create para o processo sobreviver; implementado no gerador_visual.py --mostrar (memoria #511)
impacto: Visuais abrem em janela flutuante independente que nao morre com a sessao; nenhum aplicativo precisa ser criado
---

# Janela flutuante para visuais (sem navegador)

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
Correcao da associacao depende de decisao dele (configuracao pessoal).
O gerador de visuais nao depende mais dessa associacao.
