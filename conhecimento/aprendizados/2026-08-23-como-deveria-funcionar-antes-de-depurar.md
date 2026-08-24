---
tipo: erro
tags: [vigilante, debug, metodologia, timers]
data: 2026-08-23
contexto: Automacao da destilacao (fase 5 Sinapses Vivas) precisava rodar periodica no vigilante; investiguei por tentativa e erro antes de entender o desenho.
decisao: Antes de depurar qualquer mecanismo, perguntar primeiro "como deveria funcionar?" — qual é o caminho feliz canônico, que prova existe de que ele já funcionou, e só depois comparar a realidade com esse desenho.
impacto: Economiza ciclos longos de reinicio/teste cego. No caso concreto, três verdades já estavam no log: (1) rotinas periódicas do vigilante são timers de evento Register-ObjectEvent — o molde do LEARN TIMER logou execução hoje mesmo; (2) processos lançados via wrapper Start-Process -Command morrem em ~2min neste ambiente — nenhum intervalo vence nesse tempo; (3) o canal oficial de launch é a tarefa agendada EcoSystemVigilante (Start-ScheduledTask), estável por horas.
---

# Como deveria funcionar? — lição de depuração do vigilante

## O erro de método
Para conectar a destilação ao vigilante eu tentei: Start-Process aninhado
(morreu silencioso), timer one-shot AutoReset=false (não chegou a vencer),
bloco dentro do while principal (desvio do design). Reiniciei o vigilante
quatro vezes caçando disparo em minutos.

## A pergunta certa
"Como as rotinas periódicas DEVERIAM funcionar aqui?"
Resposta estava no próprio arquivo: molde LEARN TIMER (timer System.Timers +
Register-ObjectEvent + flag de data/gate) — com execução provada no log às
08:45 do mesmo dia. E "como o vigilante deveria ser lançado?" — pela tarefa
agendada EcoSystemVigilante, não por wrappers improvisados.

## Por que meus testes falhavam
Não era o mecanismo de eventos. Era expectativa de tempo: processo vivendo
2 minutos nunca vê um timer de 1h/24h disparar. Quando lancei pela tarefa
oficial, o processo sobreviveu horas.

## Regra incorporada
Antes de mudar qualquer coisa em sistema existente: identificar o caminho
feliz canônico, achar UMA execução passada bem-sucedida dele nos logs, e só
então medir onde a realidade diverge. Mudança de design só com justificativa.
