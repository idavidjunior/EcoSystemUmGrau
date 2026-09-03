---
tipo: decisao
tags: [supermarket-calculator, android, calculadora, feature, sdk-puro]
data: 2026-09-03
contexto: Usuario pediu uma quinta aba com calculadora simples no SupermarketCalculator (SDK puro, Java, sem Gradle). A aba "Calculadora" existente e a calculadora de compras do mercado; a nova e uma calculadora comum.
decisao: Adicionar a 5a aba "Simples" (id tabSimpleCalc, indice 4 no switchTab) com uma pagina simpleCalcPage contendo display + teclado (0-9, virgula, %, limpar, apagar, +, -, x, /, =). Logica implementada em setupSimpleCalc() no MainActivity em SDK puro (sem AndroidX). Reutiliza os drawables btn_numpad/btn_action e as cores existentes do tema. versionCode 13->14, versionName 1.5.7->1.5.8.
impacto: Novo painel simplesCalcPage dentro do FrameLayout; tabBar ganhou um 5o botao; switchTab estendido para gerenciar visibilidade/alpha/background do indice 4. Nenhuma aba existente teve o indice alterado (posicao anexada no fim para minimo impacto). Ressources novos gerados via aapt (R.java nao editado manualmente).
aprendizado: Para adicionar tab nova em layout FrameLayout com abas, basta acrescentar um LinearLayout filho com visibility gone e manipula-lo no switchTab. Operadores muti-caracter (x, /) sao tratados como simbolos literais nas comparacoes. Percentual e acao imediata (divide por 100), nao operador binario.
