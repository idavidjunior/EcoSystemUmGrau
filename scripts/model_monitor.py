"""Model Monitor: monitoramento inteligente de modelos LLM.

Rastreia performance (latência, erros, taxa de sucesso) e limites (custo,
requests) para alternância automática entre modelos. Integrado ao plugin
@razroo/opencode-model-fallback.

Uso CLI:
  python scripts/model_monitor.py status               # mostra status completo
  python scripts/model_monitor.py on                    # ativa monitoramento
  python scripts/model_monitor.py off                   # desativa monitoramento
  python scripts/model_monitor.py trocar <modelo>       # alternância manual
  python scripts/model_monitor.py config                # mostra configuração
  python scripts/model_monitor.py config --limite-custo 5.0  #define limite mensal
  python scripts/model_monitor.py registrar <modelo> <latencia_ms> <sucesso: true/false>  # registra request
  python scripts/model_monitor.py rankings              # mostra ranking de modelos
  python scripts/model_monitor.py reset                 # reseta métricas
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

BASE = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUNTIME_DIR = os.path.join(BASE, 'runtime')
STATE_FILE = os.path.join(RUNTIME_DIR, 'model_monitor.json')
FALLBACK_CONFIG = os.path.join(BASE, 'config', 'opencode-model-fallback.jsonc')
OPENCODE_CONFIG_DEPLOYED = os.path.join(
    os.path.expanduser('~'), '.config', 'opencode', 'opencode.jsonc'
)

DEFAULT_STATE = {
    'schema_version': 1,
    'enabled': False,
    'updated_at': '',
    'current_model': '',
    'config': {
        'limite_custo_mensal_usd': 10.0,
        'latencia_max_ms': 20000,
        'taxa_erro_max_pct': 10.0,
        'min_requests_para_avaliar': 5,
        'cooldown_troca_segundos': 300,
        'custo_input_por_1m': {},
        'custo_output_por_1m': {},
    },
    'modelos': {},
    'historico_trocas': [],
    'custo_acumulado': {
        'total_usd': 0.0,
        'por_modelo': {},
        'reset_em': '',
    },
}

DEFAULT_MODELO = {
    'id': '',
    'requests_total': 0,
    'requests_sucesso': 0,
    'requests_erro': 0,
    'latencia_total_ms': 0,
    'latencia_media_ms': 0,
    'taxa_sucesso_pct': 100.0,
    'ultima_troca': '',
    'motivo_ultima_troca': '',
    'cooldown_ate': '',
    'ativo': True,
}


def _ensure_dirs():
    os.makedirs(RUNTIME_DIR, exist_ok=True)


def _now():
    return datetime.now().isoformat(timespec='seconds')


def _load_state():
    _ensure_dirs()
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, encoding='utf-8') as f:
                data = json.load(f)
            for k, v in DEFAULT_STATE.items():
                data.setdefault(k, v)
            return data
        except (json.JSONDecodeError, KeyError):
            pass
    state = dict(DEFAULT_STATE)
    state['updated_at'] = _now()
    _save_state(state)
    return state


def _save_state(state):
    _ensure_dirs()
    state['updated_at'] = _now()
    tmp = STATE_FILE + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp, STATE_FILE)


def _read_fallback_config():
    """Lê o config do plugin fallback (JSONC → JSON simplificado)."""
    if not os.path.exists(FALLBACK_CONFIG):
        return {'enabled': True, 'fallback_models': [], 'retry_on_errors': [429, 500, 502, 503, 504]}
    with open(FALLBACK_CONFIG, encoding='utf-8') as f:
        content = f.read()
    # Remove comentários // e /* */
    import re
    content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    # Remove trailing commas
    content = re.sub(r',\s*([}\]])', r'\1', content)
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {'enabled': True, 'fallback_models': [], 'retry_on_errors': [429, 500, 502, 503, 504]}


def _write_fallback_config(config):
    """Escreve o config do plugin fallback de forma segura."""
    tmp = FALLBACK_CONFIG + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    os.replace(tmp, FALLBACK_CONFIG)


def _parse_fallback_log(linhas_max=200):
    """Extrai métricas do log do plugin fallback."""
    log_path = os.path.join(
        os.path.expanduser('~'), '.config', 'opencode', 'opencode-model-fallback.log'
    )
    if not os.path.exists(log_path):
        return []

    metricas = []
    try:
        with open(log_path, encoding='utf-8', errors='replace') as f:
            linhas = f.readlines()

        for linha in linhas[-linhas_max:]:
            if 'fallback triggered' in linha.lower() or 'model switched' in linha.lower():
                # Tenta extrair modelo e razão
                import re
                modelo_match = re.search(r'"model":\s*"([^"]+)"', linha)
                razao_match = re.search(r'"reason":\s*"([^"]+)"', linha)
                if modelo_match:
                    metricas.append({
                        'modelo': modelo_match.group(1),
                        'razao': razao_match.group(1) if razao_match else 'erro_desconhecido',
                        'timestamp': linha[:19] if len(linha) > 19 else '',
                    })
    except Exception:
        pass

    return metricas


def _calcular_score(modelo_data, config):
    """Calcula score de saúde do modelo (0-100). Maior = melhor."""
    if modelo_data['requests_total'] == 0:
        return 50.0  # Sem dados, score neutro

    # Peso: taxa de sucesso (60%), latência (30%), penalidade por erros (10%)
    taxa_sucesso = modelo_data['taxa_sucesso_pct']

    latencia = modelo_data['latencia_media_ms']
    latencia_max = config.get('latencia_max_ms', 20000)
    if latencia_max > 0:
        score_latencia = max(0, 100 - (latencia / latencia_max * 100))
    else:
        score_latencia = 50.0

    penalidade_erro = max(0, 100 - modelo_data['requests_erro'] * 5)

    score = (taxa_sucesso * 0.6) + (score_latencia * 0.3) + (penalidade_erro * 0.1)
    return round(min(100, max(0, score)), 1)


def _obter_modelos_disponiveis():
    """Retorna lista de modelos gratuitos do Zen."""
    return [
        'opencode/big-pickle',
        'opencode/deepseek-v4-flash-free',
        'opencode/mimo-v2.5-free',
        'opencode/hy3-free',
        'opencode/laguna-s-2.1-free',
        'opencode/nemotron-3-ultra-free',
        'opencode/nemotron-3.5-lightning-free',
    ]


def cmd_status(args):
    """Mostra status completo do monitor."""
    state = _load_state()
    config = state.get('config', DEFAULT_STATE['config'])

    lines = []
    lines.append('=== MODEL MONITOR ===')
    lines.append(f"Status:       {'ATIVO' if state['enabled'] else 'INATIVO'}")
    lines.append(f"Modelo atual: {state.get('current_model', '(não definido)')}")
    lines.append(f"Atualizado:   {state.get('updated_at', '(nunca)')}")
    lines.append('')

    # Configuração
    lines.append('--- CONFIGURAÇÃO ---')
    lines.append(f"Limite custo mensal:  ${config.get('limite_custo_mensal_usd', 10):.2f}")
    lines.append(f"Latência máxima:      {config.get('latencia_max_ms', 20000)}ms")
    lines.append(f"Taxa erro máxima:     {config.get('taxa_erro_max_pct', 10)}%")
    lines.append(f"Mín. requests avaliar: {config.get('min_requests_para_avaliar', 5)}")
    lines.append(f"Cooldown troca:       {config.get('cooldown_troca_segundos', 300)}s")
    lines.append('')

    # Custos
    custos = state.get('custo_acumulado', {})
    lines.append('--- CUSTO ACUMULADO ---')
    lines.append(f"Total: ${custos.get('total_usd', 0):.4f}")
    por_modelo = custos.get('por_modelo', {})
    if por_modelo:
        for m, c in sorted(por_modelo.items(), key=lambda x: -x[1]):
            lines.append(f"  {m}: ${c:.4f}")
    lines.append('')

    # Modelos
    modelos = state.get('modelos', {})
    if modelos:
        lines.append('--- MODELOS RASTREADOS ---')
        for mid, md in sorted(modelos.items(), key=lambda x: -_calcular_score(x[1], config)):
            score = _calcular_score(md, config)
            lines.append(
                f"  [{score:5.1f}] {mid} | "
                f"reqs={md['requests_total']} | "
                f"ok={md['taxa_sucesso_pct']:.0f}% | "
                f"lat={md['latencia_media_ms']:.0f}ms | "
                f"erros={md['requests_erro']}"
            )
    else:
        lines.append('--- MODELOS RASTREADOS ---')
        lines.append('  (nenhum modelo registrado ainda)')

    # Fallback chain
    lines.append('')
    lines.append('--- FALLBACK CHAIN ---')
    fb_config = _read_fallback_config()
    chain = fb_config.get('fallback_models', [])
    if chain:
        for i, m in enumerate(chain, 1):
            lines.append(f"  {i}. {m}")
    else:
        lines.append('  (fallback chain vazia)')

    # Últimas trocas
    trocas = state.get('historico_trocas', [])
    if trocas:
        lines.append('')
        lines.append('--- ÚLTIMAS TROCAS ---')
        for t in trocas[-5:]:
            lines.append(f"  {t.get('timestamp', '')[:16]} | {t.get('de', '?')} → {t.get('para', '?')} | {t.get('motivo', '?')}")

    print('\n'.join(lines))
    return 0


def cmd_on(args):
    """Ativa monitoramento."""
    state = _load_state()
    state['enabled'] = True
    if not state.get('current_model'):
        state['current_model'] = 'opencode/big-pickle'
    _save_state(state)
    print('[OK] Model Monitor ATIVADO')
    return 0


def cmd_off(args):
    """Desativa monitoramento."""
    state = _load_state()
    state['enabled'] = False
    _save_state(state)
    print('[OK] Model Monitor DESATIVADO')
    return 0


def cmd_trocar(args):
    """Alternância manual de modelo."""
    modelo = args.modelo
    if not modelo:
        print('[ERR] Informe o modelo: /ecomodelo trocar opencode/mimo-v2.5-free')
        return 1

    state = _load_state()
    modelo_atual = state.get('current_model', '')

    if modelo_atual == modelo:
        print(f'[INFO] Modelo já é {modelo}')
        return 0

    # Verificar cooldown
    config = state.get('config', DEFAULT_STATE['config'])
    cooldown = config.get('cooldown_troca_segundos', 300)
    modelos = state.get('modelos', {})
    if modelo_atual in modelos:
        cooldown_ate = modelos[modelo_atual].get('cooldown_ate', '')
        if cooldown_ate:
            try:
                ate_dt = datetime.fromisoformat(cooldown_ate)
                if datetime.now() < ate_dt:
                    restante = (ate_dt - datetime.now()).seconds
                    print(f'[WARN] Cooldown ativo para {modelo_atual}. Aguarde {restante}s.')
                    return 1
            except ValueError:
                pass

    # Registrar troca
    troca = {
        'timestamp': _now(),
        'de': modelo_atual,
        'para': modelo,
        'motivo': 'manual',
    }
    state.setdefault('historico_trocas', []).append(troca)
    state['historico_trocas'] = state['historico_trocas'][-20:]

    # Atualizar modelo atual
    state['current_model'] = modelo

    # Inicializar dados do modelo se não existir
    if modelo not in state.get('modelos', {}):
        state.setdefault('modelos', {})[modelo] = dict(DEFAULT_MODELO)
        state['modelos'][modelo]['id'] = modelo

    _save_state(state)
    print(f'[OK] Modelo alterado: {modelo_atual or "(nenhum)"} → {modelo}')
    return 0


def cmd_config(args):
    """Mostra ou altera configuração."""
    state = _load_state()
    config = state.get('config', DEFAULT_STATE['config'])

    if args.limite_custo is not None:
        config['limite_custo_mensal_usd'] = float(args.limite_custo)
        state['config'] = config
        _save_state(state)
        print(f'[OK] Limite de custo mensal: ${args.limite_custo:.2f}')
        return 0

    if args.latencia_max is not None:
        config['latencia_max_ms'] = int(args.latencia_max)
        state['config'] = config
        _save_state(state)
        print(f'[OK] Latência máxima: {args.latencia_max}ms')
        return 0

    if args.taxa_erro_max is not None:
        config['taxa_erro_max_pct'] = float(args.taxa_erro_max)
        state['config'] = config
        _save_state(state)
        print(f'[OK] Taxa de erro máxima: {args.taxa_erro_max}%')
        return 0

    # Mostrar config
    lines = []
    lines.append('=== CONFIGURAÇÃO DO MODEL MONITOR ===')
    lines.append(f"Limite custo mensal:   ${config.get('limite_custo_mensal_usd', 10):.2f}")
    lines.append(f"Latência máxima:       {config.get('latencia_max_ms', 20000)}ms")
    lines.append(f"Taxa erro máxima:      {config.get('taxa_erro_max_pct', 10)}%")
    lines.append(f"Mín. requests avaliar:  {config.get('min_requests_para_avaliar', 5)}")
    lines.append(f"Cooldown troca:        {config.get('cooldown_troca_segundos', 300)}s")
    lines.append('')
    lines.append('Para alterar:')
    lines.append('  /ecomodelo config --limite-custo 5.0')
    lines.append('  /ecomodelo config --latencia-max 15000')
    lines.append('  /ecomodelo config --taxa-erro-max 8.0')
    print('\n'.join(lines))
    return 0


def cmd_registrar(args):
    """Registra uma requisição (chamado pelo agente ou bridge)."""
    modelo = args.modelo
    latencia = args.latencia_ms
    sucesso = args.sucesso.lower() in ('true', '1', 'sim', 'ok')

    state = _load_state()
    modelos = state.setdefault('modelos', {})

    if modelo not in modelos:
        modelos[modelo] = dict(DEFAULT_MODELO)
        modelos[modelo]['id'] = modelo

    md = modelos[modelo]
    md['requests_total'] += 1
    md['latencia_total_ms'] += latencia
    md['latencia_media_ms'] = md['latencia_total_ms'] / md['requests_total']

    if sucesso:
        md['requests_sucesso'] += 1
    else:
        md['requests_erro'] += 1

    md['taxa_sucesso_pct'] = round(
        (md['requests_sucesso'] / md['requests_total']) * 100, 1
    ) if md['requests_total'] > 0 else 100.0

    _save_state(state)

    # Verificar se precisa trocar automaticamente
    config = state.get('config', DEFAULT_STATE['config'])
    if state.get('enabled') and md['requests_total'] >= config.get('min_requests_para_avaliar', 5):
        score = _calcular_score(md, config)
        if score < 30:
            _trocar_automaticamente(state, modelo, f'score_baixo={score}')

    return 0


def _trocar_automaticamente(state, modelo_atual, motivo):
    """Troca automaticamente para o melhor modelo disponível."""
    config = state.get('config', DEFAULT_STATE['config'])
    modelos = state.get('modelos', {})
    candidatos = _obter_modelos_disponiveis()

    # Filtrar: remover o atual e os em cooldown
    ahora = datetime.now()
    opcoes = []
    for c in candidatos:
        if c == modelo_atual:
            continue
        if c in modelos:
            cooldown_ate = modelos[c].get('cooldown_ate', '')
            if cooldown_ate:
                try:
                    if datetime.now() < datetime.fromisoformat(cooldown_ate):
                        continue
                except ValueError:
                    pass
        opcoes.append(c)

    if not opcoes:
        return

    # Escolher o primeiro disponível (ou o com melhor score)
    melhor = opcoes[0]
    melhor_score = -1
    for o in opcoes:
        if o in modelos:
            s = _calcular_score(modelos[o], config)
            if s > melhor_score:
                melhor_score = s
                melhor = o

    # Executar troca
    troca = {
        'timestamp': _now(),
        'de': modelo_atual,
        'para': melhor,
        'motivo': motivo,
    }
    state.setdefault('historico_trocas', []).append(troca)
    state['historico_trocas'] = state['historico_trocas'][-20:]
    state['current_model'] = melhor

    # Aplicar cooldown no modelo antigo
    if modelo_atual in modelos:
        cooldown_seg = config.get('cooldown_troca_segundos', 300)
        modelos[modelo_atual]['cooldown_ate'] = (
            datetime.now() + timedelta(seconds=cooldown_seg)
        ).isoformat(timespec='seconds')
        modelos[modelo_atual]['motivo_ultima_troca'] = motivo

    # Inicializar dados do novo modelo
    if melhor not in modelos:
        modelos[melhor] = dict(DEFAULT_MODELO)
        modelos[melhor]['id'] = melhor

    _save_state(state)
    _atualizar_fallback_chain(state)

    print(f'[AUTO-TROCA] {modelo_atual} → {melhor} ({motivo})')


def _atualizar_fallback_chain(state):
    """Atualiza a fallback chain no config do plugin baseado nos scores."""
    config = state.get('config', DEFAULT_STATE['config'])
    modelos = state.get('modelos', {})
    candidatos = _obter_modelos_disponiveis()

    # Ordenar por score (melhor primeiro)
    scores = []
    for c in candidatos:
        if c in modelos:
            scores.append((c, _calcular_score(modelos[c], config)))
        else:
            scores.append((c, 50.0))  # Sem dados = neutro

    scores.sort(key=lambda x: -x[1])

    # Atualizar fallback config
    fb_config = _read_fallback_config()
    fb_config['fallback_models'] = [s[0] for s in scores]
    _write_fallback_config(fb_config)


def cmd_rankings(args):
    """Mostra ranking de modelos por score."""
    state = _load_state()
    config = state.get('config', DEFAULT_STATE['config'])
    modelos = state.get('modelos', {})
    candidatos = _obter_modelos_disponiveis()

    lines = []
    lines.append('=== RANKING DE MODELOS ===')
    lines.append(f"{'Score':>6} | {'Modelo':<40} | {'Reqs':>5} | {'Sucesso':>7} | {'Latência':>8}")
    lines.append('-' * 80)

    dados = []
    for c in candidatos:
        if c in modelos:
            md = modelos[c]
            score = _calcular_score(md, config)
            dados.append((score, c, md))
        else:
            dados.append((50.0, c, None))

    dados.sort(key=lambda x: -x[0])

    for score, mid, md in dados:
        if md:
            lines.append(
                f"{score:6.1f} | {mid:<40} | {md['requests_total']:>5} | "
                f"{md['taxa_sucesso_pct']:>6.0f}% | {md['latencia_media_ms']:>7.0f}ms"
            )
        else:
            lines.append(f"{score:6.1f} | {mid:<40} | {'—':>5} | {'—':>7} | {'—':>8}")

    print('\n'.join(lines))
    return 0


def cmd_reset(args):
    """Reseta métricas de todos os modelos."""
    state = _load_state()
    state['modelos'] = {}
    state['historico_trocas'] = []
    state['custo_acumulado'] = DEFAULT_STATE['custo_acumulado']
    _save_state(state)
    print('[OK] Métricas resetadas')
    return 0


def main():
    parser = argparse.ArgumentParser(description='Model Monitor — monitoramento de modelos LLM')
    sub = parser.add_subparsers(dest='cmd')

    sub.add_parser('status')
    sub.add_parser('on')
    sub.add_parser('off')

    p_trocar = sub.add_parser('trocar')
    p_trocar.add_argument('modelo', nargs='?', default='')

    p_config = sub.add_parser('config')
    p_config.add_argument('--limite-custo', type=float, default=None)
    p_config.add_argument('--latencia-max', type=int, default=None)
    p_config.add_argument('--taxa-erro-max', type=float, default=None)

    p_reg = sub.add_parser('registrar')
    p_reg.add_argument('modelo')
    p_reg.add_argument('latencia_ms', type=int)
    p_reg.add_argument('sucesso')

    sub.add_parser('rankings')
    sub.add_parser('reset')

    args = parser.parse_args()
    cmd = args.cmd or 'status'

    if cmd == 'status':
        return cmd_status(args)
    elif cmd == 'on':
        return cmd_on(args)
    elif cmd == 'off':
        return cmd_off(args)
    elif cmd == 'trocar':
        return cmd_trocar(args)
    elif cmd == 'config':
        return cmd_config(args)
    elif cmd == 'registrar':
        return cmd_registrar(args)
    elif cmd == 'rankings':
        return cmd_rankings(args)
    elif cmd == 'reset':
        return cmd_reset(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.exit(main())
