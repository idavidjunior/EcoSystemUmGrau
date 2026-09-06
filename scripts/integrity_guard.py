#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""integrity_guard.py — Guarda de integridade de dados do ecossistema.

Monitora arquivos de dados (JSON, markdown) em busca de corrupção reversível
(mojibake UTF-8 lido como CP1252/Latin-1, JSON inválido, truncamento) e aplica
correção segura com backup + escrita atômica + relatório.

Estratégia de correção (confiança alta apenas):
  1. Round-trip completo: s.encode('cp1252').decode('utf-8') quando a string
     inteira é codificável e o resultado difere — corrige mojibake 100%.
  2. Substituição direcionada: pares inequívocos de mojibake em pt-BR quando a
     string contém caracteres legítimos (ex: em-dash) que impedem o round-trip.
  Nunca apaga conteúdo, nunca adivinha, sempre cria backup antes de modificar.

Uso:
  python scripts/integrity_guard.py --check            # verifica (sem alterar)
  python scripts/integrity_guard.py --fix              # verifica + corrige (com rollback)
  python scripts/integrity_guard.py --audit            # audita scripts (prevenção)
  python scripts/integrity_guard.py --audit --fix      # corrige escritas perigosas
  python scripts/integrity_guard.py --check --targets arquivo.json  # alvo único
  Exit: 0 = limpo, 1 = achou corrupção (e corrigiu em --fix, mas ver --json).

Guardião estrutural (knowledge_graph.json):
  eventos 2026-09-05 (conflito dual-git) provaram que mojibake e JSON inválido
  não bastam: o gráfico também sofre TRUNCAMENTO (contagens despencam, chaves
  somem, estado volta a passar). Este guardião agora mantém baseline aprendido
  (runtime/integrity_guard_state.json), discerne intenção (legítima vs truncamento)
  e, em --fix, auto-restaura do backup .bak_* mais saudável com rollback.

Saída:
  Em stdout, texto legível (check) ou JSON (--json). O vigilante.ps1 consome
  a saída JSON para registro e comunicação.
"""
import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

BASE = str(Path(__file__).resolve().parent.parent)
RUNTIME_DIR = os.path.join(BASE, 'runtime')
BACKUP_DIR = os.path.join(RUNTIME_DIR, 'backups', 'integrity_guard')
LOG_FILE = os.path.join(RUNTIME_DIR, 'integrity_guard.log')

# --- Guardião estrutural do knowledge_graph ---------------------------------
GRAPH_FILENAME = 'knowledge_graph.json'
GRAPH_SCHEMA_KEYS = [
    'version', 'last_updated', 'projects', 'patterns', 'decisions',
    'bug_fixes', 'cognitive_patterns', 'heuristics', 'frameworks',
    'tool_knowledge', 'skill_references', 'mission_learnings',
]
# Mínimos por lista principal (base sanada 05/09: 301/103/52/81/32/10/3/134).
# Limiares conservadores: acusam truncamento, sem falso positivo em evolução.
GRAPH_MIN_COUNTS = {
    'patterns': 250,
    'decisions': 85,
    'bug_fixes': 40,
    'cognitive_patterns': 60,
    'heuristics': 20,
    'frameworks': 5,
    'skill_references': 2,
    'mission_learnings': 100,
    'projects': 2,
}
GRAPH_STATE_FILE = os.path.join(RUNTIME_DIR, 'integrity_guard_state.json')
GRAPH_BACKUP_PREFIX = GRAPH_FILENAME + '.bak_'
# ----------------------------------------------------------------------------

# Pastas/alvos padrão: dados estruturados do ecossistema + fontes de reindex
# (as notas .md alimentam o índice semântico; mojibake nelas se propaga)
DEFAULT_TARGETS = [
    os.path.join(BASE, 'ler-runtime', 'knowledge', 'knowledge_graph.json'),
    os.path.join(BASE, 'conhecimento', 'memoria', 'memories.json'),
    os.path.join(BASE, 'conhecimento', 'memoria', 'index.json'),
    os.path.join(BASE, 'conhecimento', 'memoria', 'tfidf_meta.json'),
    os.path.join(BASE, 'conhecimento', 'memoria', 'tfidf_acesso.json'),
    os.path.join(BASE, 'conhecimento', 'episodios.json'),
    os.path.join(BASE, 'conhecimento', 'projetos-irmaos.json'),
    os.path.join(BASE, 'conhecimento', 'skill_vault_map.json'),
    os.path.join(BASE, 'conhecimento', 'android_manutencao.json'),
    os.path.join(BASE, 'conhecimento', 'aprendizados', 'cluster_mapper.json'),
    os.path.join(BASE, 'conhecimento', 'etica', 'inventario_dados.json'),
    os.path.join(BASE, 'conhecimento', 'etica', 'niveis_etica.json'),
    os.path.join(BASE, 'runtime', 'state.json'),
    # Fontes do reindex semântico: mojibake aqui propaga para tfidf_meta
    os.path.join(BASE, 'conhecimento', 'notas'),
    os.path.join(BASE, 'conhecimento', 'aprendizados'),
    os.path.join(BASE, 'docs'),
    os.path.join(BASE, 'documentos'),
]

# Pares inequívocos de mojibake em pt-BR (UTF-8 lido como CP1252).
# "Ã" (U+00C3) seguido de vogal/cedilha minúscula só ocorre como corrupção.
SUBST_PAIRS = [
    ('\u00c3\u00a1', '\u00e1'),  # Ã¡ -> á
    ('\u00c3\u00a9', '\u00e9'),  # Ã© -> é
    ('\u00c3\u00ad', '\u00ed'),  # Ã­ -> í
    ('\u00c3\u00b3', '\u00f3'),  # Ã³ -> ó
    ('\u00c3\u00ba', '\u00fa'),  # Ãº -> ú
    ('\u00c3\u00a3', '\u00e3'),  # Ã£ -> ã
    ('\u00c3\u00b5', '\u00f5'),  # Ãµ -> õ
    ('\u00c3\u00a2', '\u00e2'),  # Ã¢ -> â
    ('\u00c3\u00aa', '\u00ea'),  # Ãª -> ê
    ('\u00c3\u00b4', '\u00f4'),  # Ã´ -> ô
    ('\u00c3\u00a7', '\u00e7'),  # Ã§ -> ç
    ('\u00c3\u00a0', '\u00e0'),  # Ã  -> à
    ('\u00c3\u00a8', '\u00e8'),  # Ã¨ -> è
    ('\u00c3\u00ac', '\u00ec'),  # Ã¬ -> ì
    ('\u00c3\u00b9', '\u00f9'),  # Ã¹ -> ù
    ('\u00c3\u00b6', '\u00f6'),  # Ã¶ -> ö
    ('\u00c3\u00bc', '\u00fc'),  # Ã¼ -> ü
    ('\u00c3\u00ab', '\u00eb'),  # Ã« -> ë
    ('\u00c3\u00af', '\u00ef'),  # Ã¯ -> ï
    ('\u00c3\u00bf', '\u00ff'),  # Ã¿ -> ÿ
    # Maiúsculas (segundo byte alto de CP1252)
    ('\u00c3\u0192', '\u00c3'),  # Ãƒ -> Ã
    ('\u00c3\u2021', '\u00c7'),  # Ã‡ -> Ç
    ('\u00c3\u2020', '\u00c6'),  # Ã† -> Æ
    ('\u00c3\u02c6', '\u00c8'),  # Ãˆ -> È
    ('\u00c3\u2030', '\u00c9'),  # Ã‰ -> É
    ('\u00c3\u0160', '\u00ca'),  # ÃŠ -> Ê
    ('\u00c3\u2039', '\u00cb'),  # Ã‹ -> Ë
    ('\u00c3\u0152', '\u00cc'),  # ÃŒ -> Ì
    ('\u00c3\u017d', '\u00ce'),  # ÃŽ -> Î
    ('\u00c3\u2018', '\u00d1'),  # Ã‘ -> Ñ
    ('\u00c3\u2019', '\u00d2'),  # Ã’ -> Ò
    ('\u00c3\u201c', '\u00d3'),  # Ã“ -> Ó
    ('\u00c3\u201d', '\u00d4'),  # Ã” -> Ô
    ('\u00c3\u2022', '\u00d5'),  # Ã• -> Õ
    ('\u00c3\u2013', '\u00d6'),  # Ã– -> Ö
    ('\u00c3\u2014', '\u00d7'),  # Ã— -> ×
    ('\u00c3\u02dc', '\u00d8'),  # Ã˜ -> Ø
    ('\u00c3\u2122', '\u00d9'),  # Ã™ -> Ù
    ('\u00c3\u0161', '\u00da'),  # Ãš -> Ú
    ('\u00c3\u203a', '\u00db'),  # Ã› -> Û
    ('\u00c3\u0153', '\u00dc'),  # Ãœ -> Ü
    ('\u00c3\u017e', '\u00de'),  # Ãž -> Þ
    ('\u00c3\u0178', '\u00df'),  # ÃŸ -> ß
    ('\u00c3\u201e', '\u00c4'),  # Ã„ -> Ä
    ('\u00c3\u2026', '\u00c5'),  # Ã… -> Å
    # Sequências 3 bytes (E2 80 ...) lidas como CP1252
    ('\u00e2\u20ac\u201d', '\u2014'),  # â€” -> —  (em dash)
    ('\u00e2\u20ac\u201c', '\u2013'),  # â€“ -> –  (en dash)
    ('\u00e2\u20ac\u2122', '\u2019'),  # â€™ -> '  (apostrofo)
    ('\u00e2\u20ac\u0153', '\u201c'),  # â€œ -> "  (aspas esquerdas)
    ('\u00e2\u20ac\u0152', '\u201d'),  # â€ -> "  (aspas direitas)
    ('\u00e2\u20ac\u00a6', '\u2026'),  # â€¦ -> …  (reticencias)
]

# Caracteres que indicam candidato a mojibake (gatilho de detecção)
TRIGGER_CHARS = ('\u00c3', '\u00e2\u20ac')

# Pasta de código auditada para prevenção (escrita de arquivos sem UTF-8)
AUDIT_DIRS = ['scripts']

# Padrões de escrita perigosa (prevenção). Cada entrada:
#   (regex_de_abertura, tipo, mensagem, marcador)
# Se o bloco da chamada (abertura até parênteses balanceado) não contém o
# marcador, é risco. 'encoding' -> precisa encoding="utf-8";
# 'ensure_ascii' -> precisa ensure_ascii=False.
PADROES_RISCO = [
    (re.compile(r'\.write_text\s*\('), 'encoding',
     'write_text() sem encoding="utf-8" (risco de mojibake)', 'encoding='),
    (re.compile(r'\bopen\s*\(\s*[^,)]*,\s*["\'](?:w|w\+|a|a\+)["\']'),
     'encoding',
     'open() em modo escrita sem encoding="utf-8" (risco de mojibake)', 'encoding='),
    (re.compile(r'\bjson\.dump\s*\('), 'ensure_ascii',
     'json.dump() sem ensure_ascii=False (grava \\u escapes)', 'ensure_ascii='),
]


def _dentro_de_string(linha, pos):
    """True se a posição está dentro de uma string literal (aspas não escapadas)."""
    em_string = None
    i = 0
    while i < len(linha) and i < pos:
        c = linha[i]
        if em_string:
            if c == '\\':
                i += 2
                continue
            if c == em_string:
                em_string = None
        else:
            if c in ('"', "'"):
                em_string = c
        i += 1
    return em_string is not None


def _bloco_chamada(linhas, idx):
    """Retorna o texto do bloco de chamada iniciado na linha idx (abre em '(')."""
    texto = ''
    nivel = 0
    em_string = None
    inicio = linhas[idx].find('(')
    if inicio < 0:
        return ''
    for j in range(idx, len(linhas)):
        linha = linhas[j]
        texto += linha[inicio if j == idx else 0:]
        inicio = 0
        for k, c in enumerate(linha):
            if em_string:
                if c == '\\':
                    continue
                if c == em_string:
                    em_string = None
            else:
                if c in ('"', "'"):
                    em_string = c
                elif c == '(':
                    nivel += 1
                elif c == ')':
                    nivel -= 1
                    if nivel == 0:
                        return texto
        if j >= idx + 6:
            break
    return texto


def _log(msg):
    """Registra no log do guard (e imprime em stdout no modo verbose)."""
    linha = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
    try:
        os.makedirs(RUNTIME_DIR, exist_ok=True)
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(linha + '\n')
    except Exception:
        pass
    return linha


# ---------------------------------------------------------------------------
# Guardião estrutural do knowledge_graph
# ---------------------------------------------------------------------------

def _contagem_listas(dados):
    """Conta itens por chave-coleção do gráfico (para baseline e comparação)."""
    return {k: len(v) for k, v in dados.items() if isinstance(v, (list, dict))}


def _ler_estado_graph():
    """Lê o baseline lenrado pelo guardião (contagens por arquivo)."""
    try:
        with open(GRAPH_STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def _gravar_estado_graph(estado):
    """Grava o baseline de forma atômica."""
    try:
        os.makedirs(RUNTIME_DIR, exist_ok=True)
        atomic_write_json(GRAPH_STATE_FILE, estado, indent=2)
        return True
    except Exception:
        return False


def _baseline_para(path):
    """Retorna contagens baseline de um arquivo (sobrescrevendo ruído antigo)."""
    estado = _ler_estado_graph()
    rel = os.path.relpath(path, BASE).replace('\\', '/')
    return estado.get(rel) or {}


def _contagem_estrutura_ok(dados):
    """Valida schema canônico do gráfico. Retorna (ok, erros[])."""
    erros = []
    faltando = [k for k in GRAPH_SCHEMA_KEYS if k not in dados]
    if faltando:
        erros.append(f'schema: faltam chaves {faltando}')
    for k, minimo in GRAPH_MIN_COUNTS.items():
        n = len(dados.get(k, []))
        if n < minimo:
            erros.append(f'truncamento: {k} tem {n}, minimo {minimo}')
    return (not erros), erros


def _compara_baseline(dados, baseline_contagens, nome='knowledge'):
    """Compara contagens atuais vs baseline aprendido.

    Regra (discernimento de intenção):
      - Atual >= 95% do baseline  -> evolução legítima.
      - Atual < 95% do baseline   -> queda suspeita (perda/truncamento).
    Retorna (ok, delta_pct, detalhe).
    """
    if not baseline_contagens:
        return True, 0.0, 'sem baseline'
    atuais = _contagem_listas(dados)
    base_total = sum(baseline_contagens.get(k, 0) for k in GRAPH_MIN_COUNTS)
    atual_total = sum(atuais.get(k, 0) for k in GRAPH_MIN_COUNTS)
    if base_total == 0:
        return True, 0.0, 'baseline vazio'
    porcento = (atual_total / base_total) * 100.0
    if porcento >= 95.0:
        return True, porcento, f'{nome}: {atual_total} vs baseline {base_total} ({porcento:.0f}%)'
    return False, porcento, (
        f'{nome}: {atual_total} vs baseline {base_total} ({porcento:.0f}%) '
        f'- perda suspeita, nao parece evolucao legitima')


def _atualiza_baseline(path, dados):
    """Registra contagens atuais como baseline (so apos validacao OK)."""
    estado = _ler_estado_graph()
    rel = os.path.relpath(path, BASE).replace('\\', '/')
    estado[rel] = {
        'contagens': _contagem_listas(dados),
        'atualizado': datetime.now().isoformat(timespec='seconds'),
    }
    _gravar_estado_graph(estado)


def _achou_graph_bak(path):
    """Procura backups .bak_* do gráfico na mesma pasta. Lista (mais novo 1o)."""
    d = os.path.dirname(path)
    try:
        cands = [os.path.join(d, f) for f in os.listdir(d)
                 if f.startswith(GRAPH_BACKUP_PREFIX)]
        return sorted(cands, key=os.path.getmtime, reverse=True)
    except OSError:
        return []


def _restaura_graph(path, rel_arquivo):
    """Auto-restaura o gráfico do backup .bak_* mais saudável (com rollback).

    Critério de escolha: o backup que valida o schema canônico com o maior
    total de contagens. Antes de restaurar, cria backup do estado atual. Após
    restaurar, re-valida; se falhar, restaura o estado pré-tentativa.
    Retorna (ok, mensagem).
    """
    cands = _achou_graph_bak(path)
    if not cands:
        return False, 'nenhum .bak_* do grafico na pasta para auto-restauro'
    melhor = None
    melhor_total = -1
    for cand in cands:
        try:
            with open(cand, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            ok, _ = _contagem_estrutura_ok(dados)
            if not ok:
                continue
            total = sum(_contagem_listas(dados).values())
            if total > melhor_total:
                melhor, melhor_total = cand, total
        except (OSError, ValueError):
            continue
    if not melhor:
        return False, 'backups .bak_* existem, mas nenhum valida o schema'
    # backup do estado atual antes de mexer
    bak_atual = make_backup(path)
    if not bak_atual:
        return False, 'falhou ao criar backup do estado atual'
    try:
        import shutil
        shutil.copy2(melhor, path)
        # pós-validação: se quebrou, rollback imediato
        with open(path, 'r', encoding='utf-8') as f:
            dados_pos = json.load(f)
        ok, _ = _contagem_estrutura_ok(dados_pos)
        if not ok:
            src = os.path.join(BASE, bak_atual)
            if os.path.exists(src):
                shutil.copy2(src, path)
            return False, 'pos-validacao falhou, estado anterior restaurado'
        _atualiza_baseline(path, dados_pos)
        return True, f'restaurado de {os.path.basename(melhor)}' \
                     f' (backup do estado truncado: {bak_atual})'
    except (OSError, ValueError) as e:
        src = os.path.join(BASE, bak_atual)
        if os.path.exists(src):
            try:
                shutil.copy2(src, path)
            except OSError:
                pass
        return False, f'falhou durante restauro (rollback aplicado): {e}'


def _scan_graph_estrutura(path):
    """Varredura estrutural dedicada ao knowledge_graph.

    Retorna relatório com intencao (legitima/truncamento), contagens e erros.
    Não altera o arquivo (decisão de restaurar fica no run/fix).
    """
    rel = {'arquivo': os.path.relpath(path, BASE), 'ok': True, 'erros': [],
           'intencao': 'legitima', 'contagens': {}, 'mojibake': False}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            dados = json.load(f)
    except (OSError, UnicodeDecodeError, ValueError) as e:
        rel['ok'] = False
        rel['erros'].append(f'leitura/parse: {e}')
        return rel
    ok, erros = _contagem_estrutura_ok(dados)
    if not ok:
        rel['ok'] = False
        rel['erros'].extend(erros)
        rel['intencao'] = 'truncamento'
        # discernimento: compara com baseline aprendido para dar contexto
        base = _baseline_para(path).get('contagens') or {}
        _, pct, detalhe = _compara_baseline(dados, base)
        if detalhe != 'sem baseline':
            rel['erros'].append(detalhe)
    rel['contagens'] = _contagem_listas(dados)
    return rel


def detecta_mojibake(s):
    """True se a string tem chance de conter mojibake reversível.

    Usa gatilhos conservadores: qualquer dos pares SUBST_PAIRS presentes, ou
    'Ã'/'â€' como indicação. NÃO é prova — a prova é fix_mojibake retornar
    resultado válido diferente.
    """
    if not isinstance(s, str):
        return False
    for bad, _ in SUBST_PAIRS:
        if bad in s:
            return True
    return False


def fix_mojibake(s):
    """Corrige mojibake reversível. Retorna (corrigido, novo_texto).

    Estratégia:
      1. Round-trip CP1252->UTF-8 se a string inteira é codificável em CP1252
         e o resultado difere (cobre strings 100% corrompidas).
      2. Substituição direcionada dos pares inequívocos para strings mistas
         (mojibake + texto legítimo, ex: com em-dash real).
    Nunca altera se não houver confiança.
    """
    if not isinstance(s, str) or not detecta_mojibake(s):
        return False, s
    original = s
    # 1. Round-trip completo
    try:
        b = s.encode('cp1252')
        r = b.decode('utf-8')
        if r != s:
            s = r
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    # 2. Substituição direcionada (apenas pares inequívocos)
    for bad, good in SUBST_PAIRS:
        s = s.replace(bad, good)
    return (s != original), s


def fix_mojibake_texto(texto):
    """Aplica fix_mojibake a um texto inteiro. Retorna (n_substituicoes, novo_texto)."""
    if not isinstance(texto, str) or not detecta_mojibake(texto):
        return 0, texto
    n = 0
    for bad, good in SUBST_PAIRS:
        n += texto.count(bad)
    _, novo = fix_mojibake(texto)
    if novo == texto:
        n = 0
    return n, novo


def fix_json(obj):
    """Corrige mojibake recursivamente num objeto JSON. Retorna (n_corrigidos)."""
    n = 0
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            if isinstance(v, str):
                ok, novo = fix_mojibake(v)
                if ok:
                    obj[k] = novo
                    n += 1
            elif isinstance(v, (dict, list)):
                n += fix_json(v)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if isinstance(v, str):
                ok, novo = fix_mojibake(v)
                if ok:
                    obj[i] = novo
                    n += 1
            elif isinstance(v, (dict, list)):
                n += fix_json(v)
    return n


def scan_json(path):
    """Verifica/corrige um arquivo JSON. Retorna relatório.

    Relatório: {arquivo, ok, erros[], corrigidos, backup}
    Para o knowledge_graph delega ao guardião estrutural (_scan_graph_estrutura),
    que adiciona intencao/contagens e detecta truncamento por schema + baseline.
    """
    if os.path.basename(path) == GRAPH_FILENAME:
        return _scan_graph_estrutura(path)
    rel = {'arquivo': os.path.relpath(path, BASE), 'ok': True, 'erros': [],
           'corrigidos': 0, 'backup': None, 'mojibake': False}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            texto = f.read()
        try:
            dados = json.loads(texto)
        except json.JSONDecodeError as e:
            rel['ok'] = False
            rel['erros'].append(f'JSON invalido: {e}')
            return rel
        # Verificação de mojibake
        if detecta_mojibake(texto):
            rel['mojibake'] = True
            n = fix_json(dados)
            if n:
                rel['corrigidos'] = n
        return rel
    except OSError as e:
        rel['ok'] = False
        rel['erros'].append(f'leitura: {e}')
        return rel


def scan_md(path, fix=False):
    """Verifica um arquivo markdown (mojibake reversível). Aplica correção se fix."""
    rel = {'arquivo': os.path.relpath(path, BASE), 'ok': True, 'erros': [],
           'corrigidos': 0, 'backup': None, 'mojibake': False}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            texto = f.read()
    except (OSError, UnicodeDecodeError) as e:
        rel['ok'] = False
        rel['erros'].append(f'leitura: {e}')
        return rel
    n, novo = fix_mojibake_texto(texto)
    if n:
        rel['mojibake'] = True
        rel['corrigidos'] = n
        if fix:
            try:
                bak = make_backup(path)
                tmp = path + '.tmp'
                with open(tmp, 'w', encoding='utf-8') as f:
                    f.write(novo)
                os.replace(tmp, path)
                # Pós-validação: re-lê; se ainda houver mojibake reversível,
                # restaura o backup
                with open(path, 'r', encoding='utf-8') as f:
                    texto_pos = f.read()
                n_pos, _ = fix_mojibake_texto(texto_pos)
                if n_pos:
                    src = os.path.join(BASE, bak)
                    if os.path.exists(src):
                        os.replace(src, path)
                    rel['ok'] = False
                    rel['erros'] = [f'pos-validacao falhou, backup restaurado']
                    rel['corrigidos'] = 0
                else:
                    rel['backup'] = bak
                    rel['ok'] = True
            except Exception as e:
                rel['ok'] = False
                rel['erros'].append(f'correcao: {e}')
    return rel


def atomic_write_json(path, dados, indent=2):
    """Escrita atômica: tmp + os.replace."""
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=indent)
    os.replace(tmp, path)


def make_backup(path):
    """Copia o arquivo para o diretório de backup antes de modificar."""
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        dest = os.path.join(BACKUP_DIR, f'{ts}_{os.path.basename(path)}')
        import shutil
        shutil.copy2(path, dest)
        return os.path.relpath(dest, BASE)
    except Exception:
        return None


def collect_targets(targets):
    """Expande alvos: arquivos ou pastas (recursivo, .json e .md)."""
    out = []
    for t in targets:
        t = os.path.abspath(t)
        if os.path.isdir(t):
            for root, _, files in os.walk(t):
                for f in files:
                    if f.endswith(('.json', '.md')):
                        out.append(os.path.join(root, f))
        elif os.path.isfile(t):
            out.append(t)
    return sorted(set(out))


def _parenteses_balanceados(linha):
    """True se os parênteses da linha estão balanceados (ignorando strings)."""
    nivel = 0
    em_string = None
    i = 0
    while i < len(linha):
        c = linha[i]
        if em_string:
            if c == '\\':
                i += 2
                continue
            if c == em_string:
                em_string = None
        else:
            if c in ('"', "'"):
                em_string = c
            elif c == '(':
                nivel += 1
            elif c == ')':
                nivel -= 1
                if nivel < 0:
                    return False
        i += 1
    return nivel == 0 and em_string is None


def corrigir_linha(linha, tipo):
    """Corrige uma linha com escrita perigosa. Retorna linha corrigida ou None.

    Insere o argumento antes do parêntese de fechamento da chamada, lidando
    com sufixos como "as f:" ou ".close()". Só linhas de uma única chamada
    com parênteses balanceados são corrigidas.
    """
    if not _parenteses_balanceados(linha):
        return None
    if tipo == 'encoding':
        marcador, arg = 'encoding=', 'encoding="utf-8"'
        alvo = 'write_text('
        if marcador in linha:
            return None
        if alvo in linha:
            i = linha.find(alvo) + len(alvo) - 1  # posição do '('
        elif 'open(' in linha:
            i = linha.find('open(') + len('open(') - 1
        else:
            return None
    elif tipo == 'ensure_ascii':
        marcador, arg = 'ensure_ascii=', 'ensure_ascii=False'
        alvo = 'json.dump('
        if marcador in linha or alvo not in linha:
            return None
        i = linha.find(alvo) + len(alvo) - 1
    else:
        return None
    # Acha o ')' que fecha o parêntese aberto em i
    nivel = 0
    em_string = None
    j = i
    while j < len(linha):
        c = linha[j]
        if em_string:
            if c == '\\':
                j += 2
                continue
            if c == em_string:
                em_string = None
        else:
            if c in ('"', "'"):
                em_string = c
            elif c == '(':
                nivel += 1
            elif c == ')':
                nivel -= 1
                if nivel == 0:
                    # Insere antes deste ')'
                    args = linha[i + 1:j].rstrip()
                    if args.endswith(','):
                        args = args[:-1].rstrip()
                    nova = linha[:i + 1] + args + ', ' + arg + linha[j:]
                    return nova if nova != linha else None
        j += 1
    return None


def audit_script(path, fix=False):
    """Audita um script Python por padrões de escrita perigosa.
    Retorna {arquivo, riscos[], corrigidos, backup}.
    """
    rel = {'arquivo': os.path.relpath(path, BASE), 'riscos': [], 'corrigidos': 0,
           'backup': None}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            linhas = f.readlines()
    except (OSError, UnicodeDecodeError) as e:
        rel['riscos'].append({'linha': 0, 'tipo': 'erro', 'mensagem': f'leitura: {e}'})
        return rel
    novas_linhas = list(linhas)
    alterado = False
    for i, linha in enumerate(linhas, 1):
        for padrao, tipo, mensagem, marcador in PADROES_RISCO:
            match = padrao.search(linha)
            if not match:
                continue
            if _dentro_de_string(linha, match.start()):
                continue  # match dentro de string literal (falso positivo)
            bloco = _bloco_chamada(linhas, i - 1)
            if marcador in bloco:
                continue  # já seguro
            novo = corrigir_linha(linha, tipo) if fix else None
            if novo and novo != linha:
                rel['riscos'].append({'linha': i, 'tipo': tipo, 'mensagem': mensagem,
                                      'corrigida': True})
                novas_linhas[i - 1] = novo
                rel['corrigidos'] += 1
                alterado = True
            else:
                rel['riscos'].append({'linha': i, 'tipo': tipo, 'mensagem': mensagem,
                                      'corrigida': False})
    if alterado and fix:
        novo_conteudo = ''.join(novas_linhas)
        # Backup antes de modificar
        bak = make_backup(path)
        # Validação: o código corrigido precisa continuar compilando
        tmp = path + '.tmp_audit'
        try:
            with open(tmp, 'w', encoding='utf-8') as f:
                f.write(novo_conteudo)
            import py_compile
            py_compile.compile(tmp, doraise=True)
            os.replace(tmp, path)
            rel['backup'] = bak
        except (py_compile.PyCompileError, SyntaxError, OSError) as e:
            # Se quebrou, descarta a edição e restaura o original
            if os.path.exists(tmp):
                os.remove(tmp)
            rel['corrigidos'] = 0
            rel['riscos'].append({'linha': 0, 'tipo': 'erro',
                                  'mensagem': f'correcao invalidada por py_compile: {e}'})
    return rel


def run_audit(fix=False):
    """Audita os scripts do ecossistema (prevenção de mojibake na escrita).
    Retorna (exit_code, agregado).
    """
    agregado = {
        'scanned_at': datetime.now().isoformat(timespec='seconds'),
        'auditado': 'scripts',
        'arquivos': 0,
        'riscos': 0,
        'corrigidos': 0,
        'arquivos_corrigidos': [],
        'relatorios': [],
    }
    exit_code = 0
    arquivos = []
    for d in AUDIT_DIRS:
        base_d = os.path.join(BASE, d)
        if os.path.isdir(base_d):
            for f in sorted(os.listdir(base_d)):
                if f.endswith('.py'):
                    arquivos.append(os.path.join(base_d, f))
    agregado['arquivos'] = len(arquivos)
    for path in arquivos:
        rel = audit_script(path, fix=fix)
        # Script que não compila é um risco de runtime (ex.: stub markdown
        # tratado como .py). Não há correção automática segura — só reporta.
        try:
            import py_compile
            py_compile.compile(path, doraise=True)
        except (py_compile.PyCompileError, SyntaxError, OSError) as e:
            rel['riscos'].append({'linha': 0, 'tipo': 'nao_compila',
                                  'mensagem': f'arquivo nao compila: {e}',
                                  'corrigida': False})
        if rel['riscos']:
            agregado['riscos'] += 1
            if rel['backup'] or rel['corrigidos']:
                agregado['corrigidos'] += rel['corrigidos']
                agregado['arquivos_corrigidos'].append(rel['arquivo'])
            if not rel['backup']:
                exit_code = 1  # ainda há risco não corrigido
        agregado['relatorios'].append(rel)
    return exit_code, agregado


def run(fix=False, targets=None, json_out=False, report_only=False):
    """Executa a varredura. Retorna (exit_code, relatorio_agregado)."""
    targets = targets or DEFAULT_TARGETS
    arquivos = collect_targets(targets)
    agregado = {
        'scanned_at': datetime.now().isoformat(timespec='seconds'),
        'arquivos': len(arquivos),
        'corrompidos': 0,
        'corrigidos': 0,
        'restaurados': 0,
        'arquivos_corrigidos': [],
        'relatorios': [],
    }
    exit_code = 0
    for path in arquivos:
        ext = os.path.splitext(path)[1].lower()
        if ext == '.json':
            rel = scan_json(path)
            # Guardião estrutural do graph: aprende baseline de versões sãs
            if (os.path.basename(path) == GRAPH_FILENAME and rel['ok']
                    and not rel.get('mojibake')):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        dados = json.load(f)
                    _atualiza_baseline(path, dados)
                except (OSError, ValueError):
                    pass
            # Guardião estrutural do graph: auto-restauro em --fix quando
            # detectado truncamento (schema + baseline), com rollback.
            if (fix and os.path.basename(path) == GRAPH_FILENAME
                    and not rel['ok'] and rel.get('intencao') == 'truncamento'):
                ok_rest, msg = _restaura_graph(path, rel['arquivo'])
                if ok_rest:
                    rel['ok'] = True
                    rel['erros'] = [f'auto-restauro: {msg}']
                    rel['backup'] = None  # backup interno do restauro
                    rel['corrigidos'] = 1
                    rel['restaurado'] = True
                    # re-lê contagens para o relatório refletir o estado final
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            dados_pos = json.load(f)
                        rel['contagens'] = _contagem_listas(dados_pos)
                    except (OSError, ValueError):
                        pass
                else:
                    rel['erros'].append(f'auto-restauro falhou: {msg}')
        elif ext == '.md':
            rel = scan_md(path, fix=fix)
        else:
            continue
        if rel.get('backup'):
            # Já corrigido dentro do scan (md) — conta como corrigido
            agregado['corrigidos'] += rel['corrigidos']
            agregado['arquivos_corrigidos'].append(rel['arquivo'])
        elif rel.get('restaurado'):
            # Guardião estrutural restaurou o gráfico de um .bak_* saudável
            agregado['corrigidos'] += rel.get('corrigidos', 0)
            agregado['arquivos_corrigidos'].append(rel['arquivo'])
            agregado['restaurados'] = agregado.get('restaurados', 0) + 1
        elif not rel['ok'] or rel['mojibake']:
            agregado['corrompidos'] += 1
            exit_code = 1
            if fix and rel['corrigidos'] and ext == '.json':
                # Re-escritura com backup + atômica + pós-validação com rollback
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        dados = json.load(f)
                    n = fix_json(dados)
                    if n:
                        bak = make_backup(path)
                        atomic_write_json(path, dados)
                        # Pós-validação: re-lê o que foi gravado; se ainda houver
                        # mojibake reversível ou JSON inválido, restaura o backup
                        try:
                            with open(path, 'r', encoding='utf-8') as f:
                                texto_pos = f.read()
                            dados_pos = json.loads(texto_pos)
                            if detecta_mojibake(texto_pos):
                                raise ValueError('mojibake residual apos correcao')
                            if isinstance(dados_pos, dict) and 'last_updated' in dados_pos:
                                for chave in ('patterns', 'decisions'):
                                    if chave not in dados_pos:
                                        raise ValueError(f'estrutura: falta "{chave}"')
                        except (ValueError, json.JSONDecodeError) as e:
                            if bak:
                                src = os.path.join(BASE, bak)
                                if os.path.exists(src):
                                    os.replace(src, path)
                            rel['ok'] = False
                            rel['erros'] = [f'pos-validacao falhou, backup restaurado: {e}']
                            agregado['corrigidos'] += 0
                        else:
                            rel['backup'] = bak
                            rel['ok'] = True
                            rel['erros'] = []
                            agregado['corrigidos'] += n
                            agregado['arquivos_corrigidos'].append(rel['arquivo'])
                except Exception as e:
                    rel['ok'] = False
                    rel['erros'].append(f'correcao: {e}')
            else:
                # Corrige em memória apenas para relatório (mesmo em --check
                # reportamos quantos caracteres seriam corrigidos, sem gravar)
                pass
        agregado['relatorios'].append(rel)

    if json_out:
        print(json.dumps(agregado, ensure_ascii=False, indent=2))
    else:
        print(f'integrity_guard: {agregado["arquivos"]} arquivo(s) verificado(s)')
        for rel in agregado['relatorios']:
            estado = 'OK' if rel['ok'] and not rel['mojibake'] else 'CORROMPIDO'
            if rel.get('restaurado'):
                estado = 'RESTAURADO'
            elif rel.get('corrigidos'):
                estado = f'CORRIGIDO ({rel["corrigidos"]} strings)'
            print(f'  [{estado}] {rel["arquivo"]}')
            if rel.get('contagens'):
                seq = {k: rel['contagens'].get(k, 0) for k in GRAPH_MIN_COUNTS}
                print(f'      contagens: {seq}')
            for err in rel['erros']:
                print(f'      {err}')
            if rel.get('backup'):
                print(f'      backup: {rel["backup"]}')
        if fix:
            extra = f', {agregado.get("restaurados", 0)} restauro(s) estrutural(ais)' \
                    if agregado.get('restaurados') else ''
            print(f'RESULTADO: {agregado["corrigidos"]} string(s) corrigida(s) em '
                  f'{len(agregado["arquivos_corrigidos"])} arquivo(s){extra}')
        else:
            print(f'RESULTADO: {agregado["corrompidos"]} arquivo(s) com corrupcao '
                  f'(use --fix para corrigir)')
    return exit_code, agregado


def main():
    parser = argparse.ArgumentParser(description='Guarda de integridade de dados')
    parser.add_argument('--check', action='store_true', help='verificar sem alterar')
    parser.add_argument('--fix', action='store_true', help='verificar e corrigir')
    parser.add_argument('--audit', action='store_true',
                        help='auditar scripts por escrita perigosa (prevenção)')
    parser.add_argument('--json', dest='json_out', action='store_true',
                        help='saída em JSON (para consumo por scripts)')
    parser.add_argument('--targets', nargs='*', default=None,
                        help='arquivos/pastas específicos (padrão: dados do ecossistema)')
    args = parser.parse_args()

    if args.audit:
        code, agregado = run_audit(fix=args.fix)
        if args.json_out:
            print(json.dumps(agregado, ensure_ascii=False, indent=2))
        else:
            print(f'integrity_guard (auditoria): {agregado["arquivos"]} script(s) auditado(s)')
            for rel in agregado['relatorios']:
                if rel['riscos']:
                    estado = 'CORRIGIDO' if rel['backup'] else 'RISCO'
                    print(f'  [{estado}] {rel["arquivo"]}')
                    for r in rel['riscos']:
                        marca = 'fix' if r.get('corrigida') else '  '
                        print(f'      L{r["linha"]} {marca} {r["mensagem"]}')
                    if rel['backup']:
                        print(f'      backup: {rel["backup"]}')
            if args.fix:
                print(f'RESULTADO: {agregado["corrigidos"]} correcao(ões) em '
                      f'{len(agregado["arquivos_corrigidos"])} arquivo(s)')
            else:
                print(f'RESULTADO: {agregado["riscos"]} arquivo(s) com risco '
                      f'(use --audit --fix para corrigir)')
        return code

    code, _ = run(fix=args.fix, targets=args.targets, json_out=args.json_out)
    return code


if __name__ == '__main__':
    sys.exit(main())