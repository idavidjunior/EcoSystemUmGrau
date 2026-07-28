# 2026-07-27 - Unificacao completa do ecossistema

## Problemas resolvidos
1. **LER fora do repo**: movido ~/.ler/ → ler-runtime/ com junction. Tudo versionado.
2. **Polling ineficiente**: vigilante agora usa FileSystemWatcher + debounce 300ms.
3. **Sync so push**: agora faz pull antes de push (bidirecional).
4. **Sem comando central**: ecosystem.ps1 criado (sync, scan, status).
5. **LER remoto separado**: deletado github.com/idavidjunior/LER, conhecimento unificado.

## Decisoes
- LER runtime vira subdiretorio do EcoSystemUmGrau (nao repo separado)
- OpenCode = interface, LER = engine, bridge via 11-ler-executor
- FileSystemWatcher > polling para deteccao de arquivos
- Git sync: pull primeiro, depois commit+push (evita conflitos)
- ecosystem.ps1 como CLI unificada (sync, scan, status)

## Padroes
- Junction NTFS para compatibilidade retroativa (~/.ler/ → ler-runtime/)
- Template com {{USERPROFILE}} + geracao via setup.bat
- Timer para operacoes periodicas (git sync a cada 5 min)
