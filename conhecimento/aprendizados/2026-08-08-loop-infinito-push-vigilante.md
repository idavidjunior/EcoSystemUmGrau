---
tipo: bug
tags: [vigilante, github, git-sync, loop-infinito, memory-engine, push, automacao]
data: 2026-08-08
contexto: Usuário relatou receber emails do GitHub a cada minuto — algo estava subindo constantemente
decisao: Remover log de git-sync do loop do vigilante + excluir EcoSystemUmGrau da auto-descoberta de projetos
impacto: Sem pushes automáticos a cada 30-60s; vigilante volta a sincronizar só quando há mudança real (cooldown 5min)
---

# Loop infinito de push no Vigilante (emails do GitHub a cada minuto)

## Sintoma
Emails de notificação do GitHub chegando a cada ~1 minuto. Push automáticos no repo
`EcoSystemUmGrau` a cada 30-60s, contínuos, sem mudança real de código.

## Causa raiz (loop de auto-alimentação)
1. `scripts/vigilante.ps1` rodava git sync a cada 30s (`$gitTimer`).
2. Após cada push do Eco, chamava `memory_engine.py log "git-sync: EcoSystemUmGrau"`
   (linha 283) — que **faz append de 1 linha** em `conhecimento/memoria/sessions/YYYYMMDD.jsonl`
   (arquivo DENTRO do repositório).
3. Esse append disparava o FileSystemWatcher do próprio repo — que tinha sido
   **auto-descoberto como "projeto"** (bug: `EcoSystemUmGrau` tem git remote + `.git`,
   então o filtro de descoberta o pegou como se fosse um projeto Android).
4. Watcher → novo sync → novo commit + push → novo `log` → **loop infinito**.

Prova: cada commit automático tinha exatamente `sessions/20260808.jsonl | 1 +`; o arquivo
acumulou 353 linhas em um único dia.

## Correção aplicada
1. Removidas as chamadas `memory_engine.py log "git-sync: ..."` do loop do vigilante
   (o log de git-sync era ruído puro: task="git-sync", sem dados úteis).
2. Auto-descoberta de projetos agora **exclui o próprio `$ecoDir`** e `ler-runtime`
   (`$_.FullName -ne $ecoDir -and $_.Name -ne "ler-runtime"`).
3. Corrigido erro de sintaxe PowerShell na primeira tentativa de edição (atribuição
   `$remote = ...` dentro de expressão `-and` — inválido no PS 5.1).

## Verificação
- Vigilante reiniciado (PID 7588): log não mostra mais "monitora N projetos: EcoSystemUmGrau".
- Após o fix: **zero** novos commits/pushes em >5min (antes: 2/min).
- `git status` limpo exceto gitlinks "dirty" pré-existentes de submódulos com trabalho não commitado.

## Lições
- **Nunca** escrever logs do próprio processo de sync dentro do diretório versionado que o watcher monitora.
- Watcher de arquivos + repo com remote = risco de feedback loop; excluir o repo principal da auto-descoberta.
- Validar sintaxe PowerShell com `[Parser]::ParseFile` antes de reiniciar script em produção.
