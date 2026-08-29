---
name: google-drive
description: |
  Acesso ao Google Drive do usuario via Composio (MCP remoto). Listar pastas,
  buscar arquivos, ler metadados, criar pastas, mover, renomear e ver estrutura
  do Drive usando comandos simples do utilitario local drive_utils.py.
  Trigger phrases: "google drive", "drive", "minhas pastas", "meu drive",
  "arquivo no drive", "acessar drive", "pasta no drive".
allowed-tools: Bash
version: 1.0.0
---

# Google Drive — Acesso às Pastas do Usuário

## Objetivo
Dar ao ecossistema acesso real e simples às pastas e arquivos do Google Drive
do usuário, usando o Composio (servidor MCP remoto já integrado).

## Como usar
Use o utilitário local `scripts/drive_utils.py` (encapsula o fluxo Composio).
Toda chamada passa por `python scripts/drive_utils.py <comando> [args]`.

## Comandos

Listar conteúdo de uma pasta (default: raiz do Drive):
```
python scripts/drive_utils.py listar [folder_id]
```

Buscar arquivos/pastas por termo no nome:
```
python scripts/drive_utils.py buscar "termo"
```

Metadados de um arquivo/pasta (data, dono, link, tamanho):
```
python scripts/drive_utils.py info <file_id>
```

Criar pasta:
```
python scripts/drive_utils.py criar_pasta <nome> [parent_id]
```

Mover arquivo para outra pasta:
```
python scripts/drive_utils.py mover <file_id> <destino_id>
```

Renomear arquivo/pasta:
```
python scripts/drive_utils.py renomear <file_id> <novo_nome>
```

Árvore de pastas (até 3 níveis):
```
python scripts/drive_utils.py estrutura [folder_id] [max_depth]
```

Informações da conta/quota:
```
python scripts/drive_utils.py sobre
```

## Importável em Python
```python
from drive_utils import listar_pasta, buscar_arquivos, info_arquivo, \
    criar_pasta, mover_arquivo, renomear, estrutura, sobre
```

## Fluxo técnico (referência)
O utilitário chama o servidor local `scripts/mcp-composio-server.py`, que
encaminha ao endpoint `https://connect.composio.dev/mcp` autenticado com
`x-consumer-api-key` (chave em `scripts/.env`). Ferramentas usadas:
GOOGLEDRIVE_FIND_FILE, GET_FILE_METADATA, CREATE_FOLDER, MOVE_FILE,
UPDATE_FILE_PUT, GET_ABOUT.

## Regras de segurança
- GOOGLEDRIVE_DELETE_FILE remove PERMANENTE, sem passar pela lixeira.
  Nunca excluir sem autorização explícita do usuário.
- Operações destrutivas (excluir, mover em massa) sempre confirmar antes.
- Para arquivos de texto, o download retorna um link temporário (s3url).

## Padrões conhecidos
- Raiz do Drive é `root` como folder_id.
- O FIND_FILE pode retornar `data_preview` truncado quando a resposta é
  grande; o utilitário lê `data_preview.files` quando `data.files` ausente.
- Google Docs não têm campo `size`; usar createdTime/modifiedTime para
  comparar versões.