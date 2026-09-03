"""Kernel Permanente do Ecossistema.

Autoridade máxima. Nenhuma resposta é produzida sem passar pelo Kernel.
Controla regras, prioridades, contratos, políticas, formatos obrigatórios,
sequência de execução, validações e autorização para resposta.

O Kernel é agnóstico de LLM: a inteligência operacional vive aqui, não no modelo.

Uso CLI:
  python scripts/runtime_kernel.py status                 # estado do kernel
  python scripts/runtime_kernel.py check "<texto>"       # valida texto contra regras (contrato de saída)
  python scripts/runtime_kernel.py contrato-entrada "<objetivo>"
  python scripts/runtime_kernel.py pipeline              # fluxo obrigatório
  python scripts/runtime_kernel.py regras                # lista regras absolutas
  python scripts/runtime_kernel.py complexity "<pedido>" # classifica complexidade (LOW/HIGH)
  python scripts/runtime_kernel.py plan "<objetivo>"     # cria plano via mcp-planner
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple

BASE = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(BASE, 'scripts')
sys.path.insert(0, SCRIPTS)

CONSTITUICAO = os.path.join(BASE, 'config', 'agents', '00-system-rules.md')

try:
    from llm_router import router as llm_router
    LLM_ROUTER_AVAILABLE = True
except ImportError:
    LLM_ROUTER_AVAILABLE = False

# Sequência obrigatória de execução (nenhuma etapa pode ser pulada)
PIPELINE = [
    'Bootloader (restaura estado + verifica integridade)',
    'Kernel (autoriza e enquadra a tarefa)',
    'Memory Engine (carrega memória relevante)',
    'Context Loader (seleciona documentos/agentes relevantes)',
    'Conselho Permanente (somente se complexidade/criticidade alta)',
    'LER (somente se tarefa multi-passo ou exploração)',
    'Validador (verifica conformidade da resposta)',
    'Auditor (auditoria final contra Constituição/objetivo)',
    'Resposta Final (após autorização do Kernel)',
]

# Contrato de entrada obrigatório
ENTRADA_CONTRATO = {
    'objetivo': 'O que deve ser alcançado',
    'contexto': 'Estado atual do ecossistema',
    'restricoes': 'Limites e condições',
    'memoria_necessaria': 'Memórias que precisam ser carregadas',
    'ferramentas': 'Ferramentas e documentos disponíveis',
    'criterios_sucesso': 'Como saber que a tarefa foi concluída',
    'formato_esperado': 'Formato da resposta',
}

# Contrato de saída obrigatório
SAIDA_CONTRATO = {
    'resultado': 'O que foi entregue',
    'justificativa': 'Por que esta é a resposta correta',
    'verificacoes': 'Validações realizadas',
    'pendencias': 'O que ficou pendente',
    'proximos_passos': 'Recomendações de continuidade',
}


# ============================================================================
# COMPLEXITY CLASSIFIER — Few-shot zero-shot classification (LOW/HIGH)
# ============================================================================

class ComplexityClassifier:
    """Classifica complexidade de pedidos: LOW (direto) vs HIGH (precisa planner).

    Usa zero-shot classification (BART-large-mnli) com few-shot examples
    para decidir se a tarefa deve ser roteada direto ou passar pelo PlannerAgent.
    """

    _instance = None
    _lock = None

    def __new__(cls):
        import threading
        if cls._lock is None:
            cls._lock = threading.Lock()
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._clf = None
        self._labels = ["LOW", "HIGH"]
        self._examples = self._load_few_shot_examples()

    def _load_few_shot_examples(self) -> List[Tuple[str, str]]:
        """Exemplos few-shot baseados no AgenticSeek (router.py)."""
        return [
            # LOW - tarefas diretas, single-step
            ("hi", "LOW"),
            ("olá", "LOW"),
            ("como vai", "LOW"),
            ("qual a data de hoje", "LOW"),
            ("escreva um script python para verificar se o dispositivo está na rede", "LOW"),
            ("debugue este código java que não funciona", "LOW"),
            ("busque na web o preço da RTX 4090", "LOW"),
            ("encontre o arquivo notes.txt no meu Documents", "LOW"),
            ("crie um script bash para listar processos", "LOW"),
            ("escreva uma função python para inverter string", "LOW"),
            ("qual o clima em São Paulo hoje", "LOW"),
            ("conte uma piada", "LOW"),
            ("traduza este texto para inglês", "LOW"),
            ("formate este JSON", "LOW"),
            ("gere um UUID", "LOW"),
            ("qual a capital da França", "LOW"),
            ("calcule 15% de 280", "LOW"),
            ("liste arquivos .py no diretório atual", "LOW"),
            ("verifique se a porta 8080 está aberta", "LOW"),
            ("converta CSV para JSON", "LOW"),
            # HIGH - multi-step, precisa planejamento, dependências
            ("pesquise startups de IA em São Paulo, salve em CSV e faça gráfico", "HIGH"),
            ("encontre o repo vitess, clone e instale seguindo o readme", "HIGH"),
            ("crie um servidor web em Go que consulte API de voos e mostre no frontend", "HIGH"),
            ("faça busca profunda de players de IA 2025 e gere relatório em arquivo", "HIGH"),
            ("encontre o arquivo budget.xlsx, analise dados e gere gráfico para o chefe", "HIGH"),
            ("planeje viagem de 3 dias para Nova York com voos e hotéis", "HIGH"),
            ("clone o repo, rode os testes, corrija falhas e faça deploy", "HIGH"),
            ("pesquise API de clima, crie app python que mostra previsão", "HIGH"),
            ("organize arquivos do desktop por extensão e escreva script para listar", "HIGH"),
            ("encontre API pública de cripto, construa tracker em Flask", "HIGH"),
            ("busque tutoriais de ML, treine modelo simples e salve", "HIGH"),
            ("crie app Node.js que consulta API de tráfego e exibe mapa", "HIGH"),
            ("encontre arquivo resume.pdf, aplique para vagas compatíveis online", "HIGH"),
            ("configure novo projeto Flutter, implemente autenticação, teste", "HIGH"),
            ("migre banco de dados, rode migrações, valide integridade", "HIGH"),
            ("implemente CI/CD pipeline com testes, lint, deploy automático", "HIGH"),
            ("refatore módulo legado, escreva testes, valide regressão", "HIGH"),
            ("projetar arquitetura microserviços, defina contratos, documente", "HIGH"),
            ("audite código legado, liste vulnerabilidades, proponha fixes", "HIGH"),
        ]

    def _get_classifier(self):
        """Lazy load do classificador zero-shot.

        Por padrão usa heurística (rápida, sem download).
        Transformers só carrega se USE_TRANSFORMERS_CLASSIFIER=1 e modelo já estiver em cache.
        """
        if self._clf is not None:
            return self._clf

        # Verifica se deve tentar transformers
        import os
        if os.getenv("USE_TRANSFORMERS_CLASSIFIER") != "1":
            self._clf = None
            return None

        try:
            from transformers import pipeline
            # Tenta carregar apenas se já estiver em cache local
            self._clf = pipeline("zero-shot-classification",
                                 model="facebook/bart-large-mnli",
                                 local_files_only=True)
        except Exception:
            self._clf = None
        return self._clf

    def _heuristic_classify(self, text: str) -> Tuple[str, float]:
        """Classificação heurística quando transformers não disponível."""
        text_lower = text.lower()
        # Palavras-chave que indicam HIGH
        high_keywords = [
            'planeje', 'planejar', 'organize', 'organizar', 'migre', 'migrar',
            'implemente', 'implementar', 'construa', 'construir', 'crie app',
            'crie aplicação', 'desenvolva', 'desenvolver', 'arquitetura',
            'pipeline', 'deploy', 'refatore', 'refatorar', 'audite', 'auditoria',
            'clone e instale', 'clone e rode', 'setup completo', 'configuração completa',
            'relatório completo', 'análise completa', 'estudo completo',
            'múltiplas', 'várias etapas', 'passo a passo', 'em etapas',
            'depende de', 'precisa de', 'requer', 'depois', 'então', 'seguido de',
        ]
        # Palavras-chave que indicam LOW (single action)
        low_keywords = [
            'qual', 'quanto', 'quando', 'onde', 'quem', 'o que', 'como',
            'escreva', 'escrever', 'gere', 'gerar', 'liste', 'listar',
            'encontre', 'encontrar', 'busque', 'buscar', 'procure', 'procurar',
            'verifique', 'verificar', 'cheque', 'checar', 'teste', 'testar',
            'debugue', 'debugar', 'corrija', 'corrigir', 'formate', 'formatar',
            'converta', 'converter', 'traduza', 'traduzir', 'calcule', 'calcular',
        ]

        high_score = sum(1 for kw in high_keywords if kw in text_lower)
        low_score = sum(1 for kw in low_keywords if kw in text_lower)

        # Heurísticas adicionais
        if len(text.split()) > 30:
            high_score += 1
        if any(c in text for c in [',', ';', ' e ', ' depois ', ' então ']):
            high_score += 1
        if text.count(' ') > 50:
            high_score += 2

        if high_score > low_score:
            confidence = min(0.5 + (high_score - low_score) * 0.1, 0.9)
            return "HIGH", confidence
        else:
            confidence = min(0.5 + (low_score - high_score) * 0.1, 0.9)
            return "LOW", confidence

    def classify(self, text: str) -> Dict:
        """Classifica complexidade do texto.

        Returns:
            dict: {'complexity': 'LOW'|'HIGH', 'confidence': float, 'method': 'transformers'|'heuristic'}
        """
        if not text or not text.strip():
            return {'complexity': 'LOW', 'confidence': 1.0, 'method': 'empty'}

        clf = self._get_classifier()

        if clf is not None:
            try:
                # Usa zero-shot com labels + few-shot context
                candidate_labels = self._labels
                result = clf(text, candidate_labels, multi_label=False)
                # result: {'labels': [...], 'scores': [...]}
                complexity = result['labels'][0]
                confidence = float(result['scores'][0])
                return {'complexity': complexity, 'confidence': confidence, 'method': 'transformers'}
            except Exception:
                pass

        # Fallback heurístico
        complexity, confidence = self._heuristic_classify(text)
        return {'complexity': complexity, 'confidence': confidence, 'method': 'heuristic'}

    def is_high_complexity(self, text: str) -> bool:
        """Retorna True se complexidade HIGH."""
        return self.classify(text)['complexity'] == 'HIGH'


# Singleton global
complexity_classifier = ComplexityClassifier()


class Kernel:
    def __init__(self):
        self.rules = self._load_absolute_rules()
        self.status = 'ACTIVE'

    def _load_absolute_rules(self):
        """Extrai as regras absolutas da Constituição."""
        rules = []
        if not os.path.exists(CONSTITUICAO):
            return rules
        with open(CONSTITUICAO, encoding='utf-8') as f:
            content = f.read()
        # Regras absolutas numeradas dentro da cláusula pétrea de soberania
        section = content.split('# CLÁUSULA PÉTREA — SOBERANIA DO RUNTIME E DO KERNEL')
        if len(section) > 1:
            body = section[1].split('\n---')[0]
            for line in body.splitlines():
                line = line.strip()
                m = re.match(r'\d+\.\s+(.+)', line)
                if m:
                    rules.append(m.group(1))
        return rules

    def compreender(self, pedido):
        """Gancho: compreensão de pedidos antes da execução (fail-soft, stdlib).

        Alimenta o contrato de entrada com objetivo, ações, restrições,
        critérios de sucesso, ambiguidades e riscos do pedido.
        """
        try:
            import importlib.util
            mod_path = os.path.join(BASE, 'mcp', 'nucleo', 'habilidades',
                                    'compreensao-pedidos', 'compreensao.py')
            spec = importlib.util.spec_from_file_location('compreensao_pedidos_mod', mod_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod.compreender(pedido, refinar=False)
        except Exception as e:
            return {'objetivo': pedido.strip(), 'erro_compreensao': str(e)}

    def _load_compreensao_mod(self):
        """Carrega o módulo de compreensão (fail-soft) ou None."""
        try:
            import importlib.util
            mod_path = os.path.join(BASE, 'mcp', 'nucleo', 'habilidades',
                                    'compreensao-pedidos', 'compreensao.py')
            spec = importlib.util.spec_from_file_location('compreensao_pedidos_mod', mod_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
        except Exception:
            return None

    def gate_veto(self, goal, ent=None):
        """Gate consultável de entrega/veto (Fase 2). Bloqueia antes de rotear.

        Reutiliza `gerar_checklist` do módulo de compreensão (responsabilidade
        única, sem duplicar a lógica de vetos). Fail-soft: se o módulo estiver
        indisponível, o pedido segue APROVADO (não trava a execução).

        Returns:
            dict: {'aprovado': bool, 'status': 'APROVADO'|'BLOQUEADO',
                   'vetos': list, 'itens': list, 'objetivo': str,
                   'gate': bool, 'motivo': str}
        """
        mod = self._load_compreensao_mod()
        if mod is None:
            return {'aprovado': True, 'status': 'APROVADO', 'vetos': [],
                    'itens': [], 'objetivo': goal, 'gate': False,
                    'motivo': 'módulo de compreensão indisponível (fail-soft)'}
        try:
            res = mod.gerar_checklist(goal)
            vetos = res.get('vetos', [])
            status = res.get('status', 'APROVADO')
            return {
                'aprovado': status != 'BLOQUEADO',
                'status': status,
                'vetos': vetos,
                'itens': res.get('itens', []),
                'objetivo': goal,
                'gate': True,
                'motivo': ('vetado: ' + '; '.join(v.get('regra', '?') for v in vetos)
                           if vetos else 'sem vetos ativos'),
            }
        except Exception as e:
            return {'aprovado': True, 'status': 'APROVADO', 'vetos': [],
                    'itens': [], 'objetivo': goal, 'gate': False,
                    'motivo': f'falha no gate ({e}) — fail-soft aprovado'}

    def authorize(self, goal, ent=None):
        """Enquadra a tarefa no contrato de entrada. Retorna contrato preenchido.

        Se `ent` (entendimento do pedido) for fornecido, o contrato é enriquecido
        com restrições e critérios de sucesso extraídos da compreensão.
        Inclui classificação de complexidade (LOW/HIGH) para roteamento condicional.
        """
        contract = {k: '' for k in ENTRADA_CONTRATO}
        contract['objetivo'] = goal.strip()
        contract['contexto'] = '(restaurar via runtime_boot)'

        # Classificação de complexidade (sempre executada)
        complexity_result = complexity_classifier.classify(goal)
        contract['complexidade'] = complexity_result['complexity']
        contract['complexidade_confianca'] = complexity_result['confidence']
        contract['complexidade_metodo'] = complexity_result['method']

        if ent and not ent.get('erro_compreensao'):
            acoes = '; '.join(f"{a['verbo']} {a['objeto']}" for a in ent.get('acoes', []))
            if acoes:
                contract['contexto'] += f' | ações: {acoes}'
            contract['restricoes'] = '; '.join(ent.get('restricoes', [])) or '(sem restrições declaradas)'
            contract['criterios_sucesso'] = '; '.join(ent.get('criterios_sucesso', [])) or '(definir durante execução)'

        # Se HIGH, indica que deve ir para PlannerAgent
        if contract['complexidade'] == 'HIGH':
            contract['roteamento'] = 'PLANNER_AGENT'
            contract['contexto'] += ' | complexidade HIGH -> requer planejamento multi-agente'
        else:
            contract['roteamento'] = 'DIRECT'
            contract['contexto'] += ' | complexidade LOW -> execução direta'

        return contract

    def route_task(self, goal, ent=None):
        """Roteia tarefa baseado na complexidade.

        Returns:
            dict: {'route': 'DIRECT'|'PLANNER', 'contract': ..., 'plan': ...}
        """
        contract = self.authorize(goal, ent)

        # Fase 2 — gate de veto consultável antes de rotear. Bloqueia pedidos
        # que disparam regra de veto (commit direto, destruição, segredos, etc.)
        gate = self.gate_veto(goal, ent)
        if not gate['aprovado']:
            return {
                'route': 'BLOQUEADO',
                'contract': contract,
                'plan': None,
                'gate': gate,
                'bloqueio': True,
                'motivo': gate['motivo'],
            }

        if contract['complexidade'] == 'HIGH':
            # Delega para mcp-planner
            plan = self._call_planner(goal, contract)
            return {
                'route': 'PLANNER',
                'contract': contract,
                'plan': plan,
                'gate': gate,
            }
        else:
            return {
                'route': 'DIRECT',
                'contract': contract,
                'plan': None,
                'gate': gate,
            }

    def _call_planner(self, goal: str, contract: Dict) -> Optional[Dict]:
        """Chama MCP server mcp-planner para criar plano.

        Tenta via MCP stdio (initialize + tools/call create_plan).
        Retorna plano estruturado ou None se indisponível.
        """
        import subprocess
        import json

        planner_path = os.path.join(BASE, 'mcp', 'nucleo', 'habilidades', 'planner', 'server.py')
        if not os.path.exists(planner_path):
            return None

        # Request create_plan
        req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "create_plan",
                "arguments": {
                    "goal": goal,
                    "context": contract.get('contexto', ''),
                    "constraints": contract.get('restricoes', ''),
                    "success_criteria": contract.get('criterios_sucesso', '')
                }
            }
        }

        try:
            result = subprocess.run(
                [sys.executable, planner_path],
                input=json.dumps(req) + "\n",
                capture_output=True, text=True, timeout=30, cwd=BASE
            )
            if result.returncode != 0:
                return None

            # Parse response (line-delimited JSON)
            for line in result.stdout.strip().split('\n'):
                try:
                    resp = json.loads(line)
                    if resp.get('id') == 1 and 'result' in resp:
                        content = resp['result'].get('content', [])
                        if content and content[0].get('type') == 'text':
                            plan_text = content[0]['text']
                            return json.loads(plan_text)
                except json.JSONDecodeError:
                    continue
        except Exception:
            pass

        return None

    def validate_output(self, text, goal=''):
        """Valida uma resposta contra as regras do Kernel (contrato de saída).

        Retorna (ok, lista de falhas).
        """
        failures = []
        text = text or ''
        if not text.strip():
            failures.append('Resposta vazia')
        for rule in self.rules:
            rl = rule.lower()
            # Checagens heurísticas leves baseadas nas regras absolutas
            if 'memória' in rl and ('memória' not in text.lower() and
                                     'memory' not in text.lower() and goal):
                failures.append(f'Regra: "{rule}" — resposta não referencia memória/contexto')
            if 'validar' in rl and ('valid' not in text.lower() and
                                     'verific' not in text.lower()):
                failures.append(f'Regra: "{rule}" — resposta não declara validação realizada')
            if 'justificativa' in rl and ('justific' not in text.lower() and
                                           'porqu' not in text.lower()):
                failures.append(f'Regra: "{rule}" — resposta sem justificativa explícita')
        return (len(failures) == 0, failures)

    def authorize_response(self, text, goal=''):
        """Autorização final do Kernel para emitir a resposta."""
        ok, failures = self.validate_output(text, goal)
        if not ok:
            return False, failures
        return True, ['todas as regras absolutas respeitadas']

    def render_status(self):
        lines = ['=== KERNEL PERMANENTE ===', f'Status: {self.status}',
                 f'Regras absolutas: {len(self.rules)}']
        for r in self.rules:
            lines.append(f'  • {r}')
        lines.append('')
        lines.append('Pipeline obrigatório:')
        for i, step in enumerate(PIPELINE, 1):
            lines.append(f'  {i}. {step}')
        return '\n'.join(lines)

    def render_contract(self, kind='entrada'):
        contract = ENTRADA_CONTRATO if kind == 'entrada' else SAIDA_CONTRATO
        lines = [f'=== CONTRATO DE {kind.upper()} (obrigatório) ===']
        for k, v in contract.items():
            lines.append(f'  {k}: {v}')
        return '\n'.join(lines)



    def selecionar_modelo(self, objetivo, contexto='', prioridade='balanced', capacidades_requeridas=None):
        """Selecionar modelo adequado usando o LLM Router.

        Este método usa o LLM Router para determinar o melhor modelo para a tarefa,
        seguindo as regras de task_type, priority, capabilities e fallback.
        Se o LLM Router não estiver disponível, retorna um resultado padrão.

        Returns: dicionário com a decisão do roteador
        """
        if not LLM_ROUTER_AVAILABLE:
            return {
                'modelo': 'opencode/big-pickle',
                'confianca': 0.5,
                'razao': 'LLM Router não disponível, usando modelo padrão',
                'alternativas': []
            }

        # Construir request de roteamento baseado nos parâmetros
        # Os tipos de tarefa mais comuns mapeados para o LLM Router
        task_type_map = {
            'coding': 'coding',
            'reasoning': 'reasoning',
            'creative': 'creative',
            'analysis': 'analysis',
            'chat': 'chat',
            'planning': 'planning',
            'debugging': 'debugging',
            'architecture': 'architecture',
        }

        # Detectar type da tarefa baseado no objetivo (heurística simples)
        tipo_detectado = 'chat'  # default
        objetivo_lower = objetivo.lower()
        for key, value in task_type_map.items():
            if key in objetivo_lower:
                tipo_detectado = value
                break

        # Chamar o roteador via subprocess para usar o CLI do router
        import subprocess
        try:
            result = subprocess.run(
                ['python', 'scripts/llm_router.py', 'route', tipo_detectado,
                 '--priority', prioridade,
                 '--min-context', '4000'],
                capture_output=True, text=True, cwd='C:\\\\Users\\\\David Jr\\\\Documents\\\\Default Project\\\\EcoSystemUmGrau'
            )
            if result.returncode == 0 and result.stdout.strip():
                # Parsear o resultado do roteador
                lines = result.stdout.strip().split('\\n')
                selecao = {}
                for line in lines:
                    if line.startswith('Selected:'):
                        selecao['modelo'] = line.split('Selected:')[1].strip()
                    elif line.startswith('Confidence:'):
                        selecao['confianca'] = float(line.split('Confidence:')[1].strip())
                    elif line.startswith('Reasoning:'):
                        selecao['razao'] = line.split('Reasoning:')[1].strip()

                # Alternativas
                alternativas = []
                # Parsear linhas de alternativas (formato: "modelo (score: X.XX)")
                for line in lines[4:]:  # Pular as 4 linhas iniciais
                    if '(' in line and 'score:' in line:
                        try:
                            modelo_part, score_part = line.split('(', 1)
                            modelo = modelo_part.strip()
                            score = float(score_part.split(')')[0].strip())
                            alternativas.append({'modelo': modelo, 'score': score})
                        except:
                            pass

                selecao['alternativas'] = alternativas
                return selecao
            else:
                return {
                    'modelo': 'opencode/big-pickle',
                    'confianca': 0.3,
                    'razao': 'Falha ao rotear, usando modelo padrão',
                    'alternativas': []
                }
        except Exception as e:
            return {
                'modelo': 'opencode/big-pickle',
                'confianca': 0.3,
                'razao': f'Erro ao rotear: {str(e)}',
                'alternativas': []
            }

    def execute_plan(self, goal: str, max_replans: int = 3) -> dict:
        """Executa plano completo com replan automático em falhas.

        Fluxo:
        1. Roteia tarefa (complexity -> DIRECT ou PLANNER)
        2. Se PLANNER: cria plano via mcp-planner
        3. Executa plano via tool_orchestrator (MCPs reais)
        4. Se step falha: chama replan_on_failure (máx max_replans vezes)
        5. Retorna resultado final agregado
        """
        import json

        route_result = self.route_task(goal)

        if route_result['route'] == 'BLOQUEADO':
            return {
                'route': 'BLOQUEADO',
                'status': 'bloqueado',
                'motivo': route_result.get('motivo', ''),
                'gate': route_result.get('gate', {}),
                'contract': route_result['contract']
            }

        if route_result['route'] == 'DIRECT':
            return {
                'route': 'DIRECT',
                'message': 'Tarefa de baixa complexidade — execução direta (não implementado)',
                'contract': route_result['contract']
            }

        # PLANNER route
        plan = route_result.get('plan')
        if not plan:
            return {
                'route': 'PLANNER',
                'error': 'Falha ao criar plano via mcp-planner',
                'contract': route_result['contract']
            }

        replan_count = 0
        current_plan = plan
        final_results = {}

        while replan_count <= max_replans:
            # Executa plano atual
            exec_result = self._execute_plan_via_orchestrator(current_plan, goal)

            # Verifica se houve falhas
            failed_steps = [
                (sid, r) for sid, r in exec_result.get('results', {}).items()
                if r.get('status') == 'failed'
            ]

            if not failed_steps:
                # Sucesso total
                final_results = exec_result.get('results', {})
                return {
                    'route': 'PLANNER',
                    'status': 'success',
                    'replans': replan_count,
                    'plan': current_plan,
                    'results': final_results,
                    'contract': route_result['contract']
                }

            # Falha detectada - tenta replan
            failed_step_id, failed_result = failed_steps[0]
            error_msg = failed_result.get('error', 'Erro desconhecido')

            # Coleta resultados parciais dos steps que executaram
            partial_results = {
                sid: r for sid, r in exec_result.get('results', {}).items()
                if r.get('status') == 'success'
            }

            # Chama replan_on_failure via MCP
            new_plan = self._call_replan(current_plan, failed_step_id, error_msg, partial_results)
            if not new_plan or new_plan.get('error'):
                return {
                    'route': 'PLANNER',
                    'status': 'failed',
                    'error': f'Replan falhou: {new_plan.get("error") if new_plan else "sem resposta"}',
                    'replans': replan_count,
                    'plan': current_plan,
                    'results': exec_result.get('results', {}),
                    'contract': route_result['contract']
                }

            # Prepara para próxima iteração
            current_plan = new_plan
            replan_count += 1

        # Esgotou tentativas de replan
        return {
            'route': 'PLANNER',
            'status': 'failed',
            'error': f'Esgotadas {max_replans} tentativas de replan',
            'replans': replan_count,
            'plan': current_plan,
            'results': final_results,
            'contract': route_result['contract']
        }

    def _execute_plan_via_orchestrator(self, plan: dict, goal: str) -> dict:
        """Chama mcp-planner:execute_plan via MCP stdio."""
        import subprocess
        import json
        import os

        planner_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                    'mcp', 'nucleo', 'habilidades', 'planner', 'server.py')

        req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "execute_plan",
                "arguments": {
                    "plan": plan,
                    "goal": goal
                }
            }
        }

        try:
            result = subprocess.run(
                [sys.executable, planner_path],
                input=json.dumps(req) + "\n",
                capture_output=True, text=True, timeout=300, cwd=os.path.dirname(planner_path)
            )
            if result.returncode != 0:
                return {"error": f"MCP planner falhou: {result.stderr[:500]}"}

            for line in result.stdout.strip().split('\n'):
                try:
                    resp = json.loads(line)
                    if resp.get('id') == 1 and 'result' in resp:
                        content = resp['result'].get('content', [])
                        if content and content[0].get('type') == 'text':
                            return json.loads(content[0]['text'])
                except json.JSONDecodeError:
                    continue
            return {"error": "Resposta MCP inválida", "raw": result.stdout}
        except Exception as e:
            return {"error": f"Erro executando plano: {str(e)}"}

    def _call_replan(self, plan: dict, failed_step_id: str, error: str, partial_results: dict) -> dict:
        """Chama mcp-planner:replan_on_failure via MCP stdio."""
        import subprocess
        import json
        import os

        planner_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                    'mcp', 'nucleo', 'habilidades', 'planner', 'server.py')

        req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "replan_on_failure",
                "arguments": {
                    "plan": plan,
                    "failed_step_id": failed_step_id,
                    "error": error,
                    "partial_results": partial_results
                }
            }
        }

        try:
            result = subprocess.run(
                [sys.executable, planner_path],
                input=json.dumps(req) + "\n",
                capture_output=True, text=True, timeout=60, cwd=os.path.dirname(planner_path)
            )
            if result.returncode != 0:
                return {"error": f"MCP planner replan falhou: {result.stderr[:500]}"}

            for line in result.stdout.strip().split('\n'):
                try:
                    resp = json.loads(line)
                    if resp.get('id') == 1 and 'result' in resp:
                        content = resp['result'].get('content', [])
                        if content and content[0].get('type') == 'text':
                            return json.loads(content[0]['text'])
                except json.JSONDecodeError:
                    continue
            return {"error": "Resposta MCP inválida", "raw": result.stdout}
        except Exception as e:
            return {"error": f"Erro no replan: {str(e)}"}

    def _call_planner(self, goal: str, contract: dict):
        """Chama mcp-planner:create_plan via MCP stdio."""
        import subprocess
        import json
        import os

        planner_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                    'mcp', 'nucleo', 'habilidades', 'planner', 'server.py')
        if not os.path.exists(planner_path):
            return None

        req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "create_plan",
                "arguments": {
                    "goal": goal,
                    "context": contract.get('contexto', ''),
                    "constraints": contract.get('restricoes', ''),
                    "success_criteria": contract.get('criterios_sucesso', '')
                }
            }
        }

        try:
            result = subprocess.run(
                [sys.executable, planner_path],
                input=json.dumps(req) + "\n",
                capture_output=True, text=True, timeout=30, cwd=os.path.dirname(planner_path)
            )
            if result.returncode != 0:
                return None

            for line in result.stdout.strip().split('\n'):
                try:
                    resp = json.loads(line)
                    if resp.get('id') == 1 and 'result' in resp:
                        content = resp['result'].get('content', [])
                        if content and content[0].get('type') == 'text':
                            return json.loads(content[0]['text'])
                except json.JSONDecodeError:
                    continue
        except Exception:
            pass
        return None


def main():
    parser = argparse.ArgumentParser(description='Kernel Permanente do Ecossistema')
    sub = parser.add_subparsers(dest='cmd')

    sub.add_parser('status')
    sub.add_parser('regras')
    sub.add_parser('pipeline')
    p_entrada = sub.add_parser('contrato-entrada')
    p_entrada.add_argument('objetivo', nargs='*', default=[])
    p_check = sub.add_parser('check')
    p_check.add_argument('texto', nargs='*', default=[])

    # Novos comandos Fase 1
    p_complexity = sub.add_parser('complexity')
    p_complexity.add_argument('pedido', nargs='*', default=[])
    p_complexity.add_argument('--json', action='store_true', help='Saída em JSON')

    p_plan = sub.add_parser('plan')
    p_plan.add_argument('objetivo', nargs='*', default=[])
    p_plan.add_argument('--json', action='store_true', help='Saída em JSON')

    p_route = sub.add_parser('route')
    p_route.add_argument('objetivo', nargs='*', default=[])
    p_route.add_argument('--json', action='store_true', help='Saída em JSON')

    # Fase 2: execução de plano com replan
    p_execute = sub.add_parser('execute-plan')
    p_execute.add_argument('objetivo', nargs='*', default=[])
    p_execute.add_argument('--max-replans', type=int, default=3, help='Máximo de replans em falhas')
    p_execute.add_argument('--json', action='store_true', help='Saída em JSON')

    args = parser.parse_args()
    cmd = args.cmd or 'status'
    kernel = Kernel()

    if cmd == 'status':
        print(kernel.render_status())
    elif cmd == 'regras':
        for r in kernel.rules:
            print(f'  • {r}')
    elif cmd == 'pipeline':
        for i, step in enumerate(PIPELINE, 1):
            print(f'  {i}. {step}')
    elif cmd == 'contrato-entrada':
        print(kernel.render_contract('entrada'))
        if args.objetivo:
            goal = ' '.join(args.objetivo)
            ent = kernel.compreender(goal)
            contract = kernel.authorize(goal, ent)
            print(f'\nContrato preenchido:\n  objetivo: {contract["objetivo"]}')
            if not ent.get('erro_compreensao'):
                print(f'  COMPREENSÃO: score {ent.get("score_entendimento")} ({ent.get("julgamento")})')
                for a in ent.get('acoes', []):
                    print(f"    ação: {a['verbo']} {a['objeto']}")
                for am in ent.get('ambiguidades', []):
                    print(f"    ambiguidade: {am['tipo']} — {am['msg']}")
                for r in ent.get('riscos', []):
                    print(f"    risco: {r['tipo']} ({r['nivel']}) — {r['msg']}")
            else:
                print(f'  COMPREENSÃO: indisponível ({ent.get("erro_compreensao")})')
            print(f'  complexidade: {contract.get("complexidade")} (conf: {contract.get("complexidade_confianca"):.2f}, método: {contract.get("complexidade_metodo")})')
            print(f'  roteamento: {contract.get("roteamento")}')
            print(f'  restricoes: {contract["restricoes"]}')
            print(f'  criterios_sucesso: {contract["criterios_sucesso"]}')
    elif cmd == 'check':
        text = ' '.join(args.texto)
        ok, failures = kernel.validate_output(text)
        if ok:
            print('[OK] Resposta conforme as regras do Kernel.')
        else:
            print('[REPROVADO]')
            for f in failures:
                print(f'  - {f}')
            sys.exit(1)
    elif cmd == 'complexity':
        if not args.pedido:
            print('Uso: kernel complexity "<pedido>" [--json]')
            return 1
        goal = ' '.join(args.pedido)
        result = complexity_classifier.classify(goal)
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f'Complexidade: {result["complexity"]}')
            print(f'Confiança: {result["confidence"]:.2f}')
            print(f'Método: {result["method"]}')
    elif cmd == 'plan':
        if not args.objetivo:
            print('Uso: kernel plan "<objetivo>" [--json]')
            return 1
        goal = ' '.join(args.objetivo)
        ent = kernel.compreender(goal)
        contract = kernel.authorize(goal, ent)
        if contract['complexidade'] != 'HIGH':
            result = {'message': 'Complexidade LOW — não requer planejamento', 'contract': contract}
        else:
            plan = kernel._call_planner(goal, contract)
            result = {'plan': plan, 'contract': contract}
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        else:
            if 'plan' in result and result['plan']:
                print(json.dumps(result['plan'], indent=2, ensure_ascii=False))
            else:
                print(result.get('message', 'Sem plano gerado'))
    elif cmd == 'route':
        if not args.objetivo:
            print('Uso: kernel route "<objetivo>" [--json]')
            return 1
        goal = ' '.join(args.objetivo)
        ent = kernel.compreender(goal)
        route_result = kernel.route_task(goal, ent)
        if args.json:
            print(json.dumps(route_result, indent=2, ensure_ascii=False, default=str))
        else:
            print(f'Roteamento: {route_result["route"]}')
            print(f'Complexidade: {route_result["contract"]["complexidade"]}')
            if route_result.get('plan'):
                print('Plano gerado via mcp-planner')
    elif cmd == 'execute-plan':
        if not args.objetivo:
            print('Uso: kernel execute-plan "<objetivo>" [--max-replans N] [--json]')
            return 1
        goal = ' '.join(args.objetivo)
        result = kernel.execute_plan(goal, max_replans=args.max_replans)
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        else:
            print(f'Roteamento: {result.get("route")}')
            print(f'Status: {result.get("status")}')
            if result.get('replans') is not None:
                print(f'Replans: {result["replans"]}')
            if result.get('error'):
                print(f'Erro: {result["error"]}')
            if result.get('results'):
                success = sum(1 for r in result['results'].values() if r.get('status') == 'success')
                total = len(result['results'])
                print(f'Steps: {success}/{total} sucessos')
    return 0


if __name__ == '__main__':
    sys.exit(main())

