#!/usr/bin/env python3
"""Detector automático de preferências do usuário.

Três abordagens integradas:
1. FRASE NATURAL: "minha preferência é X" / "prefiro Y" / "gosto de Z"
2. HEURÍSTICA REPETIÇÃO: padrões de uso repetido (flags, comandos, pronúncias)
3. PREDITOR DE USO: sequências, categorias frequentes → sugere preferência

Integra com memory_engine (kind='preferencia') e roda no vigilante.
"""

import json
import re
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter, defaultdict

# Paths
SCRIPTS_DIR = Path(__file__).resolve().parent
ECO_DIR = SCRIPTS_DIR.parent
MEMORY_ENGINE = SCRIPTS_DIR / 'memory_engine.py'
HISTORICO = ECO_DIR / 'conversa_unica.json'
BRIDGE_ESTADO = SCRIPTS_DIR / 'bridge_estado.json'
PREDICAO_FILE = SCRIPTS_DIR / 'predicao_uso.json'
PREFERENCIAS_FILE = SCRIPTS_DIR / 'preferencias_detectadas.json'

# Carrega memory_engine
sys.path.insert(0, str(SCRIPTS_DIR))
from memory_engine import add_memory, query

# ─────────────────────────────────────────────────────────────────────────────
# 1. FRASE NATURAL — Parser de preferência explícita
# ─────────────────────────────────────────────────────────────────────────────

PREFERENCE_PATTERNS = [
    # "minha preferência é X", "minha pref é Y"
    re.compile(r'\bminha\s+prefer[eê]ncia\s+(?:é|eh|eh\s+)\s*(.+?)[.!?]*$', re.IGNORECASE),
    # "prefiro X", "prefiro que Y"
    re.compile(r'\bprefiro\s+(?:que\s+)?(.+?)[.!?]*$', re.IGNORECASE),
    # "gosto de X", "gosto quando Y"
    re.compile(r'\bgosto\s+(?:de|quando|que)\s+(.+?)[.!?]*$', re.IGNORECASE),
    # "quero sempre X", "sempre quero Y"
    re.compile(r'\bquero\s+sempre\s+(.+?)[.!?]*$', re.IGNORECASE),
    # "meu jeito é X", "do meu jeito Y"
    re.compile(r'\bmeu\s+jeito\s+(?:é|eh)\s+(.+?)[.!?]*$', re.IGNORECASE),
    # "configura X como padrão", "define Y como default"
    re.compile(r'\b(?:configur[ae]|define|defina)\s+(.+?)\s+(?:como|pra|para)\s+.+?(?:padr[ãa]o|default)(?:\s|$|[.!?])', re.IGNORECASE),
    # "não gosto de X", "odeio Y" (preferência negativa)
    re.compile(r'\b(?:n[ãa]o\s+gosto|odeio|detesto)\s+(?:de|quando|que)\s+(.+?)[.!?]*$', re.IGNORECASE),
]

NEGATIVE_KEYWORDS = ['não', 'nao', 'nunca', 'jamais', 'evita', 'evito', 'sem', 'desativa', 'desativo']

def parse_natural_preference(text: str) -> list[dict]:
    """Extrai preferências de frase natural. Retorna lista de dicts."""
    prefs = []
    text_lower = text.strip().lower()
    seen = set()
    
    for pattern in PREFERENCE_PATTERNS:
        match = pattern.search(text)
        if match:
            content = match.group(1).strip()
            # Limpa pontuação final
            content = re.sub(r'[.!?]+$', '', content).strip()
            if not content or len(content) < 3:
                continue
            
            # Evita duplicatas
            content_key = content.lower()
            if content_key in seen:
                continue
            seen.add(content_key)
            
            # Detecta se é negativa
            is_negative = any(kw in text_lower for kw in NEGATIVE_KEYWORDS)
            
            # Normaliza
            prefs.append({
                'tipo': 'frase_natural',
                'preferencia': content,
                'negativa': is_negative,
                'origem': text[:100],
                'confianca': 0.95 if not is_negative else 0.9,
                'timestamp': datetime.now().isoformat()
            })
    
    return prefs


# ─────────────────────────────────────────────────────────────────────────────
# 2. HEURÍSTICA DE REPETIÇÃO — Padrões de uso observados
# ─────────────────────────────────────────────────────────────────────────────

# Padrões conhecidos a monitorar
USAGE_PATTERNS = {
    'intervalo_monitor': {
        'regex': r'--interval\s+(\d+)',
        'chave': 'monitor_interval',
        'desc': 'Intervalo do monitor ADB'
    },
    'pronuncia_adb': {
        'regex': r'\ba\s+d\s+b\b',
        'chave': 'pronuncia_adb',
        'desc': 'Pronúncia "a d b" para adb'
    },
    'monitor_silencioso': {
        'regex': r'(?:monitor|daemon).*silencioso',
        'chave': 'monitor_silencioso',
        'desc': 'Prefere monitor silencioso'
    },
    'usb_priority': {
        'regex': r'(?:usb|prioridade).*(?:primeiro|primeira|prioridade)',
        'chave': 'usb_priority',
        'desc': 'Prioridade USB no ADB'
    },
    'tts_pronuncia': {
        'regex': r'(?:pronunc|fala|diga|diz)\s+(\w+)\s+como\s+(\w+)',
        'chave': 'tts_pronuncia_custom',
        'desc': 'Pronúncia customizada TTS'
    },
    'tailscale_fallback': {
        'regex': r'tailscale.*fallback|fallback.*tailscale',
        'chave': 'tailscale_fallback',
        'desc': 'Prefere Tailscale como fallback'
    },
}

def extract_usage_patterns(texts: list[str]) -> list[dict]:
    """Detecta padrões repetidos em lista de textos (últimas N interações)."""
    found = defaultdict(int)
    contexts = defaultdict(list)
    
    for text in texts:
        for pattern_name, config in USAGE_PATTERNS.items():
            matches = re.findall(config['regex'], text, re.IGNORECASE)
            if matches:
                found[pattern_name] += len(matches)
                contexts[pattern_name].append(text[:100])
    
    prefs = []
    for pattern_name, count in found.items():
        if count >= 2:  # Pelo menos 2 ocorrências
            config = USAGE_PATTERNS[pattern_name]
            prefs.append({
                'tipo': 'repeticao',
                'chave': config['chave'],
                'preferencia': config['desc'],
                'detalhe': f'Detectado {count}x nas últimas interações',
                'ocorrencias': count,
                'contextos': contexts[pattern_name][:3],
                'confianca': min(0.6 + (count * 0.1), 0.9),
                'timestamp': datetime.now().isoformat()
            })
    
    return prefs


# ─────────────────────────────────────────────────────────────────────────────
# 3. PREDITOR DE USO — Sequências e categorias frequentes
# ─────────────────────────────────────────────────────────────────────────────

CATEGORIAS = {
    "adb": ["adb", "android", "celular", "dispositivo", "connect", "tcpip", "wireless"],
    "monitor": ["monitor", "daemon", "background", "silencioso", "intervalo"],
    "tts": ["tts", "voz", "fala", "pronuncia", "speech", "audio"],
    "git": ["git", "commit", "push", "pull", "sync", "branch"],
    "build": ["build", "compilar", "gradle", "apk", "install"],
    "ecossistema": ["ecossistema", "sistema", "jarvis", "vigilante", "runtime"],
    "preferencia": ["prefiro", "preferencia", "gosto", "configura", "define"],
}

def load_recent_interactions(limit=50) -> list[str]:
    """Carrega últimas interações do usuário (de conversa_unica.json e bridge_estado)."""
    texts = []
    
    # conversa_unica.json
    if HISTORICO.exists():
        try:
            with open(HISTORICO, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for entry in data[-limit:]:
                    if isinstance(entry, str) and entry.startswith('Usu'):
                        text = re.sub(r'^Usu[^\s]*\s*:\s*', '', entry)
                        texts.append(text.strip())
        except Exception:
            pass
    
    # bridge_estado.json (últimas conexões)
    if BRIDGE_ESTADO.exists():
        try:
            with open(BRIDGE_ESTADO, 'r', encoding='utf-8') as f:
                estado = json.load(f)
                if 'historico_comandos' in estado:
                    texts.extend(estado['historico_comandos'][-20:])
        except Exception:
            pass
    
    return texts


def categorize_text(text: str) -> str:
    """Classifica texto em categoria."""
    text_lower = text.lower()
    for cat, keywords in CATEGORIAS.items():
        for kw in keywords:
            if kw in text_lower:
                return cat
    return 'outros'


def predict_preferences_from_usage(texts: list[str]) -> list[dict]:
    """Gera sugestões de preferência baseadas em padrões de uso."""
    if not texts:
        return []
    
    prefs = []
    
    # 1. Categoria dominante histórica
    cats = [categorize_text(t) for t in texts]
    freq = Counter(cats)
    if freq:
        top_cat, top_count = freq.most_common(1)[0]
        if top_cat != 'outros' and top_count >= 5:
            prefs.append({
                'tipo': 'predicao_categoria',
                'chave': f'categoria_dominante_{top_cat}',
                'preferencia': f'Uso frequente de {top_cat} ({top_count}x)',
                'detalhe': f'Categoria {top_cat} representa {top_count}/{len(texts)} interações',
                'confianca': min(0.5 + (top_count * 0.05), 0.8),
                'timestamp': datetime.now().isoformat()
            })
    
    # 2. Sequências comuns (A -> B)
    seqs = Counter()
    for i in range(len(texts) - 1):
        cat_a = categorize_text(texts[i])
        cat_b = categorize_text(texts[i + 1])
        if cat_a != 'outros' and cat_b != 'outros':
            seqs[f'{cat_a} -> {cat_b}'] += 1
    
    for seq, count in seqs.most_common(3):
        if count >= 3:
            prefs.append({
                'tipo': 'predicao_sequencia',
                'chave': f'sequencia_{seq.replace(" -> ", "_")}',
                'preferencia': f'Sequência comum: {seq}',
                'detalhe': f'Ocorreu {count}x (costuma pedir {seq.split(" -> ")[1]} após {seq.split(" -> ")[0]})',
                'confianca': min(0.55 + (count * 0.05), 0.85),
                'timestamp': datetime.now().isoformat()
            })
    
    # 3. Comandos/flags repetidos
    flag_pattern = re.compile(r'(--\w+|-\w)\s*')
    all_flags = []
    for t in texts:
        all_flags.extend(flag_pattern.findall(t))
    flag_freq = Counter(all_flags)
    for flag, count in flag_freq.most_common(5):
        if count >= 3:
            prefs.append({
                'tipo': 'predicao_flag',
                'chave': f'flag_repetida_{flag.strip().replace("-", "")}',
                'preferencia': f'Sempre usa flag {flag.strip()}',
                'detalhe': f'Flag {flag.strip()} usada {count}x nas últimas {len(texts)} interações',
                'confianca': min(0.6 + (count * 0.05), 0.9),
                'timestamp': datetime.now().isoformat()
            })
    
    return prefs


# ─────────────────────────────────────────────────────────────────────────────
# INTEGRAÇÃO — Salva no memory_engine e arquivo local
# ─────────────────────────────────────────────────────────────────────────────

def load_detected_prefs() -> dict:
    if PREFERENCIAS_FILE.exists():
        try:
            return json.loads(PREFERENCIAS_FILE.read_text(encoding='utf-8'))
        except Exception:
            pass
    return {'preferencias': [], 'ultima_verificacao': None}


def save_detected_prefs(data: dict):
    PREFERENCIAS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def register_preference_in_memory(pref: dict, reindex: bool = False):
    """Registra preferência no memory_engine (kind='preferencia')."""
    try:
        # Cria summary descritivo
        summary = f"[{pref['tipo']}] {pref['preferencia']}"
        if 'detalhe' in pref:
            summary += f" - {pref['detalhe']}"
        
        task = f"Preferência detectada: {pref['preferencia']}"
        
        add_memory(
            task=task,
            summary=summary,
            kind='preferencia',
            tags=['auto-detectado', pref['tipo']],
            confidence=pref.get('confianca', 0.7),
            source_type='inferido',
            metadata=pref,
            reindex=False
        )
        return True
    except Exception as e:
        print(f"[ERRO] Falha ao registrar no memory_engine: {e}")
        return False


def deduplicate_prefs(new_prefs: list[dict], existing: list[dict]) -> list[dict]:
    """Remove duplicatas baseadas em chave/conteúdo similar."""
    existing_keys = set()
    for p in existing:
        key = p.get('chave') or p.get('preferencia', '')[:50]
        existing_keys.add(key.lower())
    
    unique = []
    for p in new_prefs:
        key = p.get('chave') or p.get('preferencia', '')[:50]
        if key.lower() not in existing_keys:
            unique.append(p)
            existing_keys.add(key.lower())
    return unique


def run_detection_cycle():
    """Executa um ciclo completo de detecção das 3 abordagens."""
    print("[PREF_DETECTOR] Iniciando ciclo de detecção...")
    
    # Carrega estado anterior
    state = load_detected_prefs()
    existing_prefs = state.get('preferencias', [])
    
    # Carrega interações recentes
    texts = load_recent_interactions(50)
    if not texts:
        print("[PREF_DETECTOR] Nenhuma interação recente encontrada")
        return
    
    all_new = []
    
    # 1. FRASE NATURAL — verifica últimas interações
    for text in texts[-10:]:  # últimas 10
        natural = parse_natural_preference(text)
        all_new.extend(natural)
    
    # 2. HEURÍSTICA REPETIÇÃO
    repetition = extract_usage_patterns(texts)
    all_new.extend(repetition)
    
    # 3. PREDITOR DE USO
    prediction = predict_preferences_from_usage(texts)
    all_new.extend(prediction)
    
    # Remove duplicatas
    unique_new = deduplicate_prefs(all_new, existing_prefs)
    
    if not unique_new:
        print("[PREF_DETECTOR] Nenhuma preferência nova detectada")
        return
    
    # Registra cada uma
    saved = 0
    for pref in unique_new:
        if register_preference_in_memory(pref):
            # Adiciona ao estado local
            pref['registrada_em'] = datetime.now().isoformat()
            pref['id'] = len(existing_prefs) + saved + 1
            existing_prefs.append(pref)
            saved += 1
            print(f"[PREF_DETECTOR] ✅ Registrada: {pref['preferencia']} ({pref['tipo']}, conf={pref.get('confianca', 0):.2f})")
    
    # Atualiza estado
    state['preferencias'] = existing_prefs
    state['ultima_verificacao'] = datetime.now().isoformat()
    state['total_registradas'] = len(existing_prefs)
    save_detected_prefs(state)
    
    print(f"[PREF_DETECTOR] Ciclo completo: {saved} novas preferências registradas (total: {len(existing_prefs)})")


def get_user_preferences() -> list[dict]:
    """Retorna preferências atuais do usuário (para uso em prompts/context)."""
    state = load_detected_prefs()
    return state.get('preferencias', [])


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Detector automático de preferências')
    parser.add_argument('--run', action='store_true', help='Executa um ciclo de detecção')
    parser.add_argument('--list', action='store_true', help='Lista preferências registradas')
    parser.add_argument('--test', action='store_true', help='Testa parser com frase de exemplo')
    args = parser.parse_args()
    
    if args.test:
        test_phrases = [
            "minha preferência é monitor silencioso 30 segundos",
            "prefiro que o adb conecte via USB primeiro",
            "gosto quando o TTS fala a d b separado",
            "configure o intervalo como 30 padrão",
            "não gosto de tela preta piscando",
        ]
        for phrase in test_phrases:
            print(f"\nTeste: '{phrase}'")
            result = parse_natural_preference(phrase)
            print(f"  Resultado: {result}")
        return
    
    if args.list:
        prefs = get_user_preferences()
        if prefs:
            for i, p in enumerate(prefs, 1):
                print(f"{i}. [{p['tipo']}] {p['preferencia']} (conf={p.get('confianca', 0):.2f})")
        else:
            print("Nenhuma preferência registrada")
        return
    
    if args.run:
        run_detection_cycle()
        return
    
    # Default: run
    run_detection_cycle()


if __name__ == '__main__':
    main()