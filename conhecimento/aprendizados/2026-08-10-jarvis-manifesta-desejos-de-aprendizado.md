---
tipo: padrao
tags: [jarvis, voz, proatividade, aprendizado, autonomia, memoria, ciclo]
data: 2026-08-10
contexto: "Usuário pediu que o Jarvis 'dissesse ou manifestasse, de vez em quando, o que gostaria de aprender, com base em suas experiências ou descobertas'. Não existia mecanismo de manifestação proativa de desejos de aprendizado."
decisao: "Criado scripts/desejo_aprendizado.py (gerador determinístico de desejos com anti-repetição) + scripts/desejos_loop.py (loop periódico com quiet hours) + desejos_start.bat. Sinais reais: (1) erros recorrentes em memories.json (peso = access_count + strength); (2) padrões em formação na skill auditoria (recorrencias>=2 fora do checklist); (3) descobertas recentes em conhecimento/aprendizados/; (4) domínios sub-cobertos no manifesto_geral.json. Manifestação TTS via vox_audio.py falar. Histórico em runtime/desejos_aprendizado.json com dedup de assinatura e janela de 3 manifestações."
impacto: "Jarvis ganhou voz proativa para sugerir o próprio aprendizado, fechando o ciclo de autonomia informada. Manifestação roda na janela 9h-22h a cada 45min (configurável via env DESEJOS_*). Anti-repetição validada em teste real (6 sinais únicos rotacionando). Sanitização JSON permanece limpa."
---

# Aprendizado: Jarvis manifesta o que quer aprender

## Resumo

Jarvis agora fala periodicamente o que gostaria de aprender, baseado em
experiências reais do ecossistema.

## Mecanismo

- `scripts/desejo_aprendizado.py` — coleta 4 sinais, escolhe até 3 (fora da
  janela das últimas 3 manifestações), persiste histórico e fala via TTS.
- `scripts/desejos_loop.py` — loop em background (intervalo 45min, janela
  9h-22h), configurável por env `DESEJOS_INTERVALO/INICIO/FIM`.
- `scripts/desejos_start.bat` — inicia o loop em background.

## Lições

- Proatividade de voz precisa de base real (memória/recorrências/cobertura) e
  anti-repetição (assinatura + janela), senão vira ruído.
- Quiet hours evitam manifestação em horário inoportuno.

## Próximos passos

- Iniciar loop em background quando o usuário quiser voz ativa.
- Integrar sugestões ao pipeline de aprendizado (o desejo manifestado pode virar
  uma tarefa de estudo registrada no runtime).

## Conexoes

- [[2026-08-04-foco-vocal-via-jarvis-voz-orienta-o-grafo-do-conh]]
- [[2026-08-04-labels-ocultas-por-padrão-botão-de-ocultar-menus-]]
- [[2026-08-04-malha-viva-onda-viajante-de-profundidade-giro-3d-]]
- [[2026-08-04-pseudo-3d-vivo-profundidade-sem-webgl-pedido-para]]
- [[2026-08-04-tamanho-por-uso-real-iniciar-gui-com-pythonw-impl]]
- [[aprendizado-2026-07-31-horas-faladas-corretamente-no-tts-do-]]
- [[grafo-movimento-organico-vis-network-usuario-pediu-refinamen]]