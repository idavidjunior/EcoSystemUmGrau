---
tags: [arquivos, cognitivo, ext4, ntfs, sistema, systemdesign]
aliases: [Padrao de escrita atomica para persistencia]
date: 2026-08-03
---

# Padrao de escrita atomica para persistencia

**Dominio:** system_design

NUNCA escreva diretamente no arquivo final. Escreva em um arquivo temporario (.tmp) e use rename atomico (os.replace() no Python, MoveFileEx on Windows, mv no Linux). O rename e atomico a nivel de sistema de arquivos em NTFS e ext4: ou o arquivo inteiro aparece, ou o antigo permanece. SEMPRE. Isso previne corrupcao por crash no meio da escrita. Leitura: se o .tmp existe e o final nao, ignore o .tmp (escrita abortada).
## Conexoes

- [[cache-de-decisoes-caras]]
- [[cluster-hub-cognicao]]
- [[cognitivo-hub-cognitivo]]
- [[estrategia-de-fallback-em-cadeia-chain-of-responsibility]]
- [[estrategia-de-loop-autonomo-planejar-executar-verificar-corr]]
- [[sempre-esperar-o-inesperado-em-es]]