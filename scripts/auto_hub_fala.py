#!/usr/bin/env python3
"""Auto-Hub de Fala: mantém o hub de fala atualizado com novos neurônios.

Critérios rigorosos para adicionar um nó:
1. Deve ser uma nota real (arquivo .md no vault)
2. Deve conter pelo menos 2 keywords primárias de fala no título/conteúdo
3. Não pode ser hub, índice, temporário ou arquivo de sistema
4. Deve ter tamanho mínimo (evitar notas vazias/mínimas)

O script:
- Escaneia o vault por notas com keywords de fala
- Verifica se já estão no hub
- Adiciona novas com wikilink
- Remove links para notas que não existem mais
- Mantém formatação consistente
"""

import json
import re
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent
VAULT = BASE / "conhecimento" / "notas"
HUB = VAULT / "_hubs" / "fala-hub.md"
VAULT_CACHE = BASE / "runtime" / "cerebro_dados.json"

# Critérios de neuronio de fala
KEYWORDS_PRIMARIAS = {"voz", "tts", "fala", "speech", "microfone", "microfono", 
                       "dialogo", "diálogo", "compreensao", "compreensão",
                       "stt", "transcricao", "transcrição", "narração", "narracao",
                       "ssml", "fonação", "fonacao"}

KEYWORDS_SECUNDARIAS = {"audio", "áudio", "sound", "volume", "playback",
                         "media", "midia", "mídia", "player"}

# Exceções: notas que mencionam "audio" mas NÃO são sobre fala
EXCECOES_AUDIO = {"mp3player", "audio-stops-eq", "audioprocessor", 
                   "renderersfactory", "lib/PyAudio", "lib/torchaudio",
                   "eq-distorts", "voxaudioplayer-temp"}

MIN_TAMANHO_NOTA = 200  # bytes mínimos para considerar nota real
MAX_LINKS_POR_CICLO = 10  # limite de adições por execução

def slug_from_path(path: Path) -> str:
    """Extrai slug do arquivo (sem extensão)."""
    return path.stem

def load_hub_links() -> set:
    """Carrega slugs já presentes no hub."""
    if not HUB.exists():
        return set()
    
    content = HUB.read_text(encoding="utf-8")
    # Extrai wikilinks [[slug]]
    links = set(re.findall(r'\[\[([^\]]+)\]\]', content))
    return links

def is_fala_neuron(path: Path) -> bool:
    """Verifica se uma nota é um neurônio de fala válido.
    
    Critérios (deve satisfazer TODOS):
    1. Arquivo .md no vault (não hub, não índice)
    2. Tamanho mínimo (evitar notas vazias)
    3. Pelo menos 2 keywords primárias OU 1 primária + 1 secundária
    4. Não está na lista de exceções
    """
    slug = slug_from_path(path)
    
    # Exceções conhecidas
    if slug in EXCECOES_AUDIO:
        return False
    
    # Evitar hubs, índices, temporários
    if "_hubs" in str(path) or "hub" in slug.lower():
        return False
    if "index" in slug.lower() or "tmp" in slug.lower():
        return False
    
    # Tamanho mínimo
    if path.stat().st_size < MIN_TAMANHO_NOTA:
        return False
    
    # Ler conteúdo (título + primeiras linhas)
    try:
        content = path.read_text(encoding="utf-8")
    except:
        return False
    
    # Normalizar para busca
    content_lower = content.lower()
    titulo = path.stem.lower()
    
    # Contar keywords primárias
    primarias = sum(1 for kw in KEYWORDS_PRIMARIAS if kw in titulo or kw in content_lower[:500])
    
    # Contar keywords secundárias (só contam se houver primária)
    secundarias = sum(1 for kw in KEYWORDS_SECUNDARIAS if kw in titulo or kw in content_lower[:500])
    
    # Critério: 2+ primárias OU 1 primária + 1 secundária
    return primarias >= 2 or (primarias >= 1 and secundarias >= 1)

def get_vault_notes() -> list:
    """Retorna todas as notas .md do vault (exceto hubs)."""
    notes = []
    for md in VAULT.rglob("*.md"):
        if "_hubs" not in str(md):
            notes.append(md)
    return notes

def update_hub(new_slugs: list, remove_stale: bool = True):
    """Atualiza o hub com novos slugs e remove links quebrados."""
    if not HUB.exists():
        print(f"[AUTO-HUB] Hub não existe: {HUB}")
        return
    
    content = HUB.read_text(encoding="utf-8")
    
    # Adicionar novos (sem duplicatas)
    existing = load_hub_links()
    added = 0
    for slug in new_slugs:
        if slug not in existing and added < MAX_LINKS_POR_CICLO:
            # Adicionar antes da linha final (ou criar seção)
            link = f"- [[{slug}]]"
            if "- [[" in content:
                content = content.rstrip() + "\n" + link + "\n"
            else:
                content += "\n## Neuronios de fala\n\n" + link + "\n"
            added += 1
    
    # Remover links quebrados (notas que não existem mais)
    removed = 0
    if remove_stale:
        lines = content.split("\n")
        new_lines = []
        for line in lines:
            match = re.search(r'\[\[([^\]]+)\]\]', line)
            if match:
                slug = match.group(1)
                # Verificar se nota existe
                exists = any(p.stem == slug for p in VAULT.rglob("*.md"))
                if exists:
                    new_lines.append(line)
                else:
                    removed += 1
            else:
                new_lines.append(line)
        content = "\n".join(new_lines)
    
    # Atualizar data no frontmatter
    content = re.sub(
        r'date: \d{4}-\d{2}-\d{2}',
        f'date: {datetime.now().strftime("%Y-%m-%d")}',
        content
    )
    
    # Salvar
    HUB.write_text(content, encoding="utf-8")
    
    return added, removed

def auto_hub_fala():
    """Executa o ciclo de auto-hub."""
    print(f"[AUTO-HUB] Iniciando扫描 do vault...")
    
    # Carregar links existentes
    existing = load_hub_links()
    print(f"[AUTO-HUB] Links existentes no hub: {len(existing)}")
    
    # Escanear vault
    notes = get_vault_notes()
    print(f"[AUTO-HUB] Notas no vault: {len(notes)}")
    
    # Filtrar neurônios de fala
    new_neurons = []
    for note in notes:
        slug = slug_from_path(note)
        if slug not in existing and is_fala_neuron(note):
            new_neurons.append(slug)
    
    print(f"[AUTO-HUB] Novos neurônios de fala encontrados: {len(new_neurons)}")
    
    if new_neurons:
        # Atualizar hub
        added, removed = update_hub(new_neurons)
        print(f"[AUTO-HUB] Adicionados: {added}, Removidos (stale): {removed}")
        
        # Registrar aprendizado se significativo
        if added > 0:
            print(f"[AUTO-HUB] Hub atualizado com {added} novos neurônios de fala")
    else:
        print(f"[AUTO-HUB] Nenhum novo neurônio de fala encontrado")
    
    return len(new_neurons)

if __name__ == "__main__":
    auto_hub_fala()
