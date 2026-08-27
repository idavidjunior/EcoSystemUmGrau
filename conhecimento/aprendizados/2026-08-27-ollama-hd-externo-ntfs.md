---
tipo: decisao
tags: [ollama, hd-externo, ntfs, exfat, reconstrucao]
data: 2026-08-27
contexto: HD externo E: estava com exFAT corrompido (leituras inconsistentes), bloqueando o Ollama.
decisao: Reformatar E: para NTFS e reconstruir o Ollama + espelhar o EcoSystemUmGrau.
impacto: Ollama 100% no E: com 5 modelos; espelho do ecossistema no E:.
---

## Reconstrução do Ollama no HD Externo (NTFS)

Causa raiz: o exFAT do E: tinha corrupção estrutural de diretório — cada leitor
(PowerShell, Python, Go do ollama) enxergava estados diferentes dos mesmos
arquivos.

Resolução: reformatei o E: para NTFS e reconstruí tudo:

1. Binários do Ollama instalados no C: e copiados para E:\Ollama\bin
2. Modelos copiados de C:\Users\David Jr\.ollama\models_bak para E:\Ollama\models via robocopy
3. Servidor confirma os 5 modelos (tinyllama, qwen2.5:3b, llama3.2:3b, phi3:mini, gemma2:2b) e inferência funciona
4. EcoSystemUmGrau espelhado de C: para E:\Default Project\EcoSystemUmGrau (35.482 arquivos, 0 falhas)

Scripts criados: E:\Ollama\start.bat e E:\Ollama\listar-modelos.bat

Lição: para HDs externos com muitos arquivos grandes + acesso concorrente,
NTFS é mais robusto que exFAT no Windows.
