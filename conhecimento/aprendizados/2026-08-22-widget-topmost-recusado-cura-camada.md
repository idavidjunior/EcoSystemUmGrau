---
tipo: padrao
tags: [widget, win32, topmost, z-order, vigia, autoreparo]
data: 2026-08-22
contexto: Cerebro Vivo (pywebview) — botao Frente logava execucao mas a janela nao grudava na frente; SetWindowPos HWND_TOPMOST retornava falso com winerror 0 mesmo com janela unica, Medium IL e em primeiro plano; SetWindowLongW de estilo aceitava retorno sem aplicar.
decisao: Nao confiar em retorno de API de janela. camada_aplicar le o bit WS_EX_TOPMOST apos aplicar; se nao grudar, escala tentativas (ctypes direto, ctypes + SWP_SHOWWINDOW, Form.TopMost nativo do .NET na thread da janela). vigia compara camada desejada (runtime/cerebro_janela.json) contra bit real a cada ciclo de 12s e reafirma com log quando ha deriva.
impacto: Janela agora trava na frente de forma verificada e autorreparavel. Prova empirica: estilo 0x50008 estavel em tres probes com intervalos de ate 14s apos boot frente. Padrao generalizavel para qualquer automacao de janelas Win32 neste ecossistema: verificar por leitura, escalar metodo, curar por loop.
---

# TopMost negado silenciosamente e cura de camada

O Windows pode recusar HWND_TOPMOST sem erro visivel. A direcao NOTOPMOST/BOTTOM sempre funcionou; a direcao TOPMOST falhou tanto de processo externo quanto no clique interno, sem rastro. A cura nao foi descobrir a causa unica, foi eliminar a classe do problema: verificacao por leitura apos cada aplicacao, retentativas escalonando metodo, e um vigia que corrige deriva sozinho a cada ciclo.

Memoria relacionada: #438 (fundo verdadeiro), #439 (cura de camada).
