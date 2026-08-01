---
tags: [cognitivo, system_design]
aliases: [Padrao de escrita atomica para persistencia]
date: 2026-08-01
---

# Padrao de escrita atomica para persistencia

**Dominio:** system_design

NUNCA escreva diretamente no arquivo final. Escreva em um arquivo temporario (.tmp) e use rename atomico (os.replace() no Python, MoveFileEx on Windows, mv no Linux). O rename e atomico a nivel de sistema de arquivos em NTFS e ext4: ou o arquivo inteiro aparece, ou o antigo permanece. SEMPRE. Isso previne corrupcao por crash no meio da escrita. Leitura: se o .tmp existe e o final nao, ignore o .tmp (escrita abortada).
