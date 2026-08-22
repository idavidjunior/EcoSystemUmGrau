# Botão Fundo de verdade + foco Uso do Eco

- **Tipo:** erro corrigido
- **Tags:** pywebview, win32, setwindowpos, topmost, cerebro-vivo, foco
- **Data:** 2026-08-22

## Contexto

O botão Fundo do widget Cerebro Vivo alternava o estado no log mas a janela
continuava visualmente na frente. O usuário reportou "não funcionou" e depois
"ainda está fixo em primeiro plano".

## Causa

SetWindowPos com HWND_NOTOPMOST (-2) apenas remove o privilégio WS_EX_TOPMOST.
A janela não muda de posição na fila Z até outra janela tomar a frente. Sem
janela sobrepondo, nada parece acontecer.

## Correção

Ao ir para fundo, segunda chamada SetWindowPos com HWND_BOTTOM (1) afunda a
janela imediatamente. Flags NOSIZE|NOMOVE|NOACTIVATE (0x13) para não redimensionar,
mover ou roubar foco.

Handle da janela: preferir webview.windows[0].native.Handle (identificador real)
com FindWindowW(None, "Cerebro Vivo") como fallback.

Persistência da camada em runtime/cerebro_janela.json: o vigia reaplica a camada
salva no primeiro ciclo pronto, sincroniza o rótulo do botão btTopo e inicializa
api._frente — sem isso o primeiro clique dessincroniza por um passo.

Prova externa: GetWindowLongW(GWL_EXSTYLE) mudou de 0x50008 (topmost ligado)
para 0x50000 (desligado).

## Bônus na mesma leva

Foco "Uso do Eco" no painel Foco: mapa ATIVOS alimenta-se de uso real
(cerebroEvento em edições e cerebroAtividade em toques); botão mostra só notas
usadas nos últimos 10 minutos; enquanto dialogo_vivo.json diz falando, um
heartbeat dispara anel branco e pulso forte por nota ativa a cada 620ms mesmo
com pulsos decorativos desligados.

## Impacto

Comando de janela que parecia quebrado funcionava; faltava afundar de fato.
Padrão reutilizável: qualquer controle de camada precisa do par NOTOPMOST+BOTTOM
e de persistência de estado sincronizada entre Python e JS.
