"""pronunciar_termos.py — Identifica e marca termos técnicos em inglês para pronúncia correta.

Uso:
  python scripts/pronunciar_termos.py "texto com Docker e Python"
  python scripts/pronunciar_termos.py --list  # lista todos os termos

Este script:
  1. Carrega o glossário de termos técnicos
  2. Identifica termos em inglês no texto
  3. Retorna o texto com marcadores para TTS pronunciar em inglês
"""
import json
import os
import re
import sys
from pathlib import Path

BASE = str(Path(__file__).resolve().parent.parent)
GLOSSARIO_PATH = os.path.join(BASE, 'config', 'glossario_tecnico.json')

# Cache do glossário
_glossario_cache = None


def carregar_glossario():
    """Carrega o glossário de termos técnicos."""
    global _glossario_cache
    if _glossario_cache is not None:
        return _glossario_cache

    try:
        with open(GLOSSARIO_PATH, encoding='utf-8') as f:
            data = json.load(f)
        # Extrair todos os termos de todas as categorias
        todos_termos = set()
        for categoria, termos in data.items():
            if categoria.startswith('_'):
                continue
            if isinstance(termos, list):
                for termo in termos:
                    todos_termos.add(termo.lower())
                    # Adicionar variações (plural, etc.)
                    todos_termos.add(termo)
        _glossario_cache = todos_termos
        return todos_termos
    except Exception:
        _glossario_cache = set()
        return set()


def identificar_termos(texto):
    """Identifica termos técnicos em inglês no texto.

    Retorna lista de tuplas (termo, posicao_inicio, posicao_fim).
    """
    glossario = carregar_glossario()
    termos_encontrados = []

    # Buscar termos do glossário no texto (case-insensitive)
    for termo in glossario:
        # Usar regex para encontrar termos como palavras inteiras
        padrao = r'\b' + re.escape(termo) + r'\b'
        for match in re.finditer(padrao, texto, re.IGNORECASE):
            termos_encontrados.append((match.group(), match.start(), match.end()))

    # Ordenar por posição
    termos_encontrados.sort(key=lambda x: x[1])

    return termos_encontrados


def marcar_para_tts(texto, formato="ssml"):
    """Marca termos técnicos para pronúncia em inglês no TTS.

    Formatos suportados:
      - "ssml": Usa SSML <lang xml:lang="en-US"> para Azure/neural TTS
      - "phonetic": Adiciona nota fonética entre parênteses
      - "simple": Apenas indica quais termos são inglês

    Retorna texto marcado.
    """
    termos = identificar_termos(texto)

    if not termos:
        return texto

    if formato == "ssml":
        # Marcar termos com SSML para pronúncia em inglês
        resultado = []
        pos_atual = 0
        for termo, inicio, fim in termos:
            # Adicionar texto antes do termo
            resultado.append(texto[pos_atual:inicio])
            # Marcar termo com lang tag
            resultado.append(f'<lang xml:lang="en-US">{termo}</lang>')
            pos_atual = fim
        # Adicionar texto restante
        resultado.append(texto[pos_atual:])
        return ''.join(resultado)

    elif formato == "phonetic":
        # Adicionar indicação fonética
        resultado = []
        pos_atual = 0
        for termo, inicio, fim in termos:
            resultado.append(texto[pos_atual:inicio])
            resultado.append(f'{termo} [en]')
            pos_atual = fim
        resultado.append(texto[pos_atual:])
        return ''.join(resultado)

    elif formato == "simple":
        # Apenas listar termos encontrados
        termos_unicos = list(set(t[0] for t in termos))
        return {
            "texto_original": texto,
            "termos_en": termos_unicos,
            "quantidade": len(termos_unicos)
        }

    return texto


def eh_termo_ingles(palavra):
    """Verifica se uma palavra é um termo técnico em inglês."""
    glossario = carregar_glossario()
    return palavra.lower() in glossario


def listar_termos():
    """Lista todos os termos do glossário agrupados por categoria."""
    try:
        with open(GLOSSARIO_PATH, encoding='utf-8') as f:
            data = json.load(f)

        print("=== GLOSSÁRIO DE TERMOS TÉCNICOS EM INGLÊS ===\n")
        total = 0
        for categoria, termos in data.items():
            if categoria.startswith('_'):
                continue
            if isinstance(termos, list):
                print(f"--- {categoria.upper().replace('_', ' ')} ---")
                for termo in sorted(termos):
                    print(f"  {termo}")
                total += len(termos)
                print()

        print(f"Total: {total} termos")
    except Exception as e:
        print(f"Erro ao carregar glossário: {e}")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        listar_termos()
        return

    if len(sys.argv) < 2:
        print("Uso:")
        print("  python pronunciar_termos.py \"texto com Docker e Python\"")
        print("  python pronunciar_termos.py --list")
        sys.exit(1)

    texto = " ".join(sys.argv[1:])

    # Modo padrão: marcar para TTS (SSML)
    resultado = marcar_para_tts(texto, formato="ssml")
    print("=== TEXTO MARCADO PARA TTS ===")
    print(resultado)
    print()

    # Mostrar termos encontrados
    termos = identificar_termos(texto)
    if termos:
        termos_unicos = list(set(t[0] for t in termos))
        print(f"=== TERMOS EM INGLÊS DETECTADOS ({len(termos_unicos)}) ===")
        for t in sorted(termos_unicos):
            print(f"  - {t}")
    else:
        print("Nenhum termo técnico em inglês detectado.")


if __name__ == "__main__":
    main()