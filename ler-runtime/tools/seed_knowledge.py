"""
Seed inicial da base de conhecimento do LER com todo aprendizado acumulado.
Inclui secoes cognitivas (heurísticas, frameworks, raciocínio) para criar
uma base de conhecimento universal e auto-melhoravel.
"""
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from agent.knowledge_consolidator import KnowledgeConsolidator

SEED = {
    "cognitive_patterns": [
        {
            "source": "meta_cognition",
            "title": "Debugging em cascata reversa",
            "domain": "debugging",
            "body": (
                "Quando um bug nao tem causa obvia, comeca pela saida (sintoma) "
                "e traca o caminho inverso ate a entrada. Para cada passo, pergunte: "
                "'Se este componente funcionasse corretamente, o que eu veria?' "
                "Quando a resposta nao corresponde a realidade, voce encontrou o "
                "componente defeituoso. Mais eficiente que debugar pra frente porque "
                "elimina ramos inteiros da arvore de causas."
            ),
        },
        {
            "source": "meta_cognition",
            "title": "Hipotese-falsificacao terminal",
            "domain": "debugging",
            "body": (
                "Para cada hipotese de causa, execute o experimento MAIS RAPIDO "
                "que pode FALSIFICA-LA, nao confirma-la. Se a hipotese for "
                "'o arquivo X nao foi carregado', nao verifique se X foi carregado "
                "(confirmacao), mas sim INTRODUZA UM ERRO OBVIO em X e veja se "
                "o sintoma muda (falsificacao). Isso eviesa para descobrir a "
                "verdade rapidamente em vez de acumular evidencias confirmatorias."
            ),
        },
        {
            "source": "meta_cognition",
            "title": "Lei de Postel aplicada a engenharia",
            "domain": "architecture",
            "body": (
                "'Seja conservador no que voce envia, seja liberal no que voce aceita.' "
                "Outputs devem ser rigorosos (validacao estrita, tipos fortes, contratos "
                "explicitos). Inputs devem ser tolerantes (defaults, fallbacks, parsing "
                "flexivel). Isso cria sistemas que funcionam com peers imperfeitos sem "
                "propagar erros. Exemplo pratico: seu modulo deve falhar ruidosamente "
                "em erros internos mas silenciosamente em erros externos recuperaveis."
            ),
        },
        {
            "source": "meta_cognition",
            "title": "Principio da separacao causa-efeito-temporal",
            "domain": "debugging",
            "body": (
                "Em sistemas distribuidos ou assincronos, a CAUSA de um bug pode "
                "ter ocorrido muito antes do EFEITO ser observado. Nao procure perto "
                "do sintoma. Trace estados globais (logs, snapshots, checkpoints) "
                "para encontrar quando o estado correto foi violado, nao quando o "
                "erro foi reportado. Exemplo: crash no ExoPlayer 30s apos iniciar "
                "musica pode ser causado por configuracao do Equalizer que foi "
                "aplicada no momento 0."
            ),
        },
        {
            "source": "meta_cognition",
            "title": "Estrategia de fallback em cadeia (Chain of Responsibility)",
            "domain": "system_design",
            "body": (
                "Quando uma operacao tem multiplas fontes de dados possiveis, "
                "organize-as em ordem de preferencia (mais precisa primeiro) com "
                "fallback automatico para a proxima. Cada fonte deve reportar "
                "claramente se conseguiu ou nao. Nao pare no primeiro resultado — "
                "avalie todos e escolha o melhor. Exemplo: MetadataSearch usa "
                "AcoustID (fingerprint) -> iTunes BR (scoring) -> MusicBrainz "
                "(detalhado) -> iTunes US (fallback)."
            ),
        },
        {
            "source": "meta_cognition",
            "title": "Validacao contra-intuitiva: teste o erro, nao o acerto",
            "domain": "testing",
            "body": (
                "Para cada funcao, o teste mais valioso nao e o 'caminho feliz' "
                "mas sim: (1) entrada vazia/nula, (2) entrada no limite, (3) entrada "
                "fora do dominio, (4) estado inconsistente, (5) concorrencia. "
                "Se sua funcao lida com arquivos: arquivo inexistente, permissao "
                "negada, disco cheio, arquivo corrompido. 80% dos bugs estao "
                "nos 20% de casos de erro."
            ),
        },
        {
            "source": "meta_cognition",
            "title": "Padrao de escrita atomica para persistencia",
            "domain": "system_design",
            "body": (
                "NUNCA escreva diretamente no arquivo final. Escreva em um arquivo "
                "temporario (.tmp) e use rename atomico (os.replace() no Python, "
                "MoveFileEx on Windows, mv no Linux). O rename e atomico a nivel "
                "de sistema de arquivos em NTFS e ext4: ou o arquivo inteiro aparece, "
                "ou o antigo permanece. SEMPRE. Isso previne corrupcao por crash "
                "no meio da escrita. Leitura: se o .tmp existe e o final nao, "
                "ignore o .tmp (escrita abortada)."
            ),
        },
        {
            "source": "meta_cognition",
            "title": "Estrategia de loop autonomo: planejar-executar-verificar-corrigir",
            "domain": "system_design",
            "body": (
                "Qualquer sistema autonomo segue um ciclo fechado: (1) Planejar: "
                "decompor objetivo em passos verificaveis. (2) Executar: rodar cada "
                "passo com ferramentas reais. (3) Verificar: validar saida contra "
                "criterios objetivos (git diff, test pass, compilacao). (4) Corrigir: "
                "se falhou, registrar causa, replanejar, tentar de novo. O loop "
                "termina apenas quando TODOS os criterios de sucesso sao atingidos. "
                "Nao use max_iterations como criterio de parada — use deteccao de "
                "estagnacao (nenhum progresso em N iteracoes)."
            ),
        },
        {
            "source": "meta_cognition",
            "title": "Modelo de scoring para busca multi-resultado",
            "domain": "algorithm",
            "body": (
                "Quando uma busca retorna multiplos resultados, nao aceite o primeiro. "
                "Atribua scores: match exato + peso alto, match parcial + peso medio, "
                "overlap lexical + peso baixo. Defina thresholds por modo (estrito "
                "vs relaxado). Acompanhe o melhor score entre TODOS os resultados, "
                "nao apenas o primeiro. Retorne null se nenhum resultado atingir "
                "o threshold minimo — e melhor falhar que retornar informacao errada. "
                "O usuario pode entao tentar modo relaxado."
            ),
        },
    ],
    "heuristics": [
        {
            "source": "meta_cognition",
            "title": "Regra dos 3 logs",
            "domain": "debugging",
            "description": (
                "Antes de comecar a debugar, adicione 3 logs: (1) entrada da funcao "
                "com parametros, (2) ponto medio/dentro do loop, (3) saida com "
                "resultado. Isso cobre 90% dos bugs sem precisar de debugger."
            ),
        },
        {
            "source": "meta_cognition",
            "title": "Heuristica de isolamento de falha",
            "domain": "debugging",
            "description": (
                "Quando um sistema falha, isole variaveis UMA de cada vez. Mude "
                "exatamente uma coisa entre cada teste. Se voce mudar duas coisas "
                "e o bug desaparecer, voce nao sabe qual das duas resolveu."
            ),
        },
        {
            "source": "meta_cognition",
            "title": "Escrita atomica sempre",
            "domain": "persistence",
            "description": (
                "Qualquer escrita em arquivo que importa: tmp + rename atomico. "
                "Nao importa o quao trivial parece. Um crash no meio do json.dump "
                "corrompe o arquivo e voce perde tudo."
            ),
        },
        {
            "source": "meta_cognition",
            "title": "Principio do menor escopo de variavel",
            "domain": "coding",
            "description": (
                "Declare variaveis no menor escopo possivel. Se uma variavel pode "
                "ser local a um if, nao a declare no inicio da funcao. Isso reduz "
                "carga cognitiva e previne bugs de reuse de estado."
            ),
        },
        {
            "source": "meta_cognition",
            "title": "Interface sobre implementacao em parametros",
            "domain": "coding",
            "description": (
                "Funcoes que aceitam dados devem aceitar o tipo MAIS GENERICO possivel "
                "(File, nao um path especifico; List, nao ArrayList; InputStream, "
                "nao FileInputStream). Isso maximiza reuso e testabilidade."
            ),
        },
        {
            "source": "meta_cognition",
            "title": "Cache de decisoes caras",
            "domain": "system_design",
            "description": (
                "Se uma computacao e deterministica e custosa, cacheie o resultado. "
                "Se o resultado pode mudar, invalide o cache explicitamente. "
                "Nunca confie em TTL para invalidação de dados que precisam ser "
                "consistentes."
            ),
        },
        {
            "source": "meta_cognition",
            "title": "Sempre esperar o inesperado em E/S",
            "domain": "system_design",
            "description": (
                "Toda operacao de E/S (rede, disco, banco) pode falhar. Sempre "
                "tenha: timeout, retry com backoff, fallback, e log do erro. "
                "Nao existe excecao 'que nunca acontece' em E/S."
            ),
        },
        {
            "source": "meta_cognition",
            "title": "Regra do 'nao magico'",
            "domain": "coding",
            "description": (
                "Numeros magicos, strings literais repetidas, e comportamento "
                "implicito sao bugs esperando para acontecer. Extraia para "
                "constantes nomeadas com documentacao do porque daquele valor."
            ),
        },
        {
            "source": "meta_cognition",
            "title": "State deve ser explícito, nunca implícito",
            "domain": "architecture",
            "description": (
                "Se um componente tem estado (ativo/inativo, conectado/desconectado, "
                "editando/visualizando), represente-o como UMA variavel booleana ou "
                "enum, nao como combinacao de multiplos sinais. State implicito "
                "(ex: 'se alpha=0 e visibility=GONE entao ta oculto') e fonte de bugs."
            ),
        },
        {
            "source": "meta_cognition",
            "title": "Dados > Algoritmos para debugging",
            "domain": "debugging",
            "description": (
                "Quando um algoritmo parece errado, nao olhe primeiro para o algoritmo. "
                "Imprima/inspecione os DADOS que ele esta processando. 90% das vezes "
                "o algoritmo esta certo e os dados estao errados (formato inesperado, "
                "null onde nao deveria, encoding errado, valores fora de range)."
            ),
        },
        {
            "source": "meta_cognition",
            "title": "Verifique o que voce acha que sabe",
            "domain": "debugging",
            "description": (
                "Toda vez que pensar 'isso nao pode ser a causa porque ja sei como "
                "funciona', VERIFIQUE. As suposicoes mais obvias sao as que mais "
                "escondem bugs. Um 'confia mas verifica' sistematico elimina horas "
                "de debugging."
            ),
        },
        {
            "source": "meta_cognition",
            "title": "Projete para falha, nao para sucesso",
            "domain": "architecture",
            "description": (
                "Um sistema robusto nao e o que nunca falha — e o que lida "
                "graciosamente com cada falha. Pergunte: 'O que acontece se o "
                "disco enche? E se a rede cai? E se a memoria acaba? E se o "
                "arquivo esta corrompido?' Para cada resposta, implemente "
                "um comportamento previsivel."
            ),
        },
    ],
    "frameworks": [
        {
            "source": "meta_cognition",
            "name": "Ciclo PDCA (Plan-Do-Check-Act) para engenharia",
            "description": "Loop classico de melhoria continua adaptado para engenharia de software.",
            "body": (
                "Plan: Defina objetivo claro com criterios de sucesso mensuraveis. "
                "Decomponha em passos atomicos. Identifique riscos e mitigacoes. "
                "Do: Execute cada passo com ferramentas reais. Colete evidencias "
                "(logs, saidas, diff). Check: Valide resultado contra criterios. "
                "Testes passaram? Codigo compilou? Comportamento esperado ocorreu? "
                "Act: Se OK, padronize e documente. Se falhou, registre causa raiz, "
                "ajuste o plano, repita. NUNCA pule o Check — e onde o aprendizado "
                "acontece."
            ),
        },
        {
            "source": "meta_cognition",
            "name": "Metodo dos 5 Porques (5 Whys)",
            "description": "Tecnica de analise de causa raiz: pergunte 'por que?' 5 vezes para cada sintoma.",
            "body": (
                "Sintoma -> Por que? -> Causa nivel 1 -> Por que? -> Causa nivel 2 "
                "-> ... -> Causa raiz. Exemplo: 'O APK crasha ao abrir' -> Por que? "
                "'Activity nao encontrada' -> Por que? 'AndroidManifest sem entry" 
                " point' -> Por que? 'Build script nao gerou manifest correto' "
                "-> Por que? 'Parametro de output name mudou e script ficou "
                "inconsistente' -> Por que? 'Nao havia teste para validar o "
                "manifest apos build'. A causa raiz NAO e o crash e sim a "
                "falta de validacao pos-build. Corrigir isso previne a classe "
                "inteira de bugs, nao apenas este."
            ),
        },
        {
            "source": "meta_cognition",
            "name": "MECE (Mutually Exclusive, Collectively Exhaustive)",
            "description": "Principio de classificacao: particoes sem sobreposicao que cobrem todo o espaco.",
            "body": (
                "Ao categorizar problemas, estados, ou causas, cada item deve "
                "pertencer a EXATAMENTE UMA categoria (mutuamente exclusiva) e "
                "todas as categorias juntas devem cobrir TODAS as possibilidades "
                "(coletivamente exaustivas). Exemplo: estado de conexao = "
                "{conectado, desconectado, conectando} — sao ME? Sim. "
                "CE? Nao — falta 'falha de autenticacao'. MECE garante que "
                "voce nao perde casos e nao conta duas vezes o mesmo caso."
            ),
        },
        {
            "source": "meta_cognition",
            "name": "FIRST Principles para testes",
            "description": "Propriedades de um bom teste unitario: Fast, Isolated, Repeatable, Self-validating, Timely.",
            "body": (
                "Fast: Teste roda em milissegundos. Se demora, nao e teste unitario. "
                "Isolated: Teste nao depende de outros testes, ordem de execucao, "
                "ou estado global. Repeatable: Mesmo resultado sempre, em qualquer "
                "maquina. Self-validating: Teste passa ou falha — sem interpretacao "
                "humana. Timely: Teste escrito antes ou junto com o codigo. Se um "
                "teste viola FIRST, ele perde valor como rede de seguranca."
            ),
        },
        {
            "source": "meta_cognition",
            "name": "Arvore de Decisao para Fallback de Servico",
            "description": "Estrategia para servicos com multiplas fontes de dados em ordem de preferencia.",
            "body": (
                "1. Tente fonte primaria (mais precisa). Se sucesso com score >= "
                "threshold, retorne. 2. Se falhou ou score baixo, armazene melhor "
                "resultado ate agora e tente fonte secundaria. 3. Compare scores, "
                "fique com o maior. 4. Se nenhuma fonte atingiu threshold minimo, "
                "retorne null (ou tente modo relaxado). 5. Registre metricas: "
                "qual fonte venceu, scores, tempo de resposta. Isso permite "
                "ajustar thresholds e ordem das fontes baseado em dados reais."
            ),
        },
        {
            "source": "meta_cognition",
            "name": "Framework de Persistencia com Snapshot Imutavel",
            "description": "Padrao onde cada salvamento e um snapshot timestampado, nunca overwrite.",
            "body": (
                "1. Estado atual e mantido em memoria (mutable). 2. 'Salvar' "
                "cria novo arquivo com timestamp no nome: "
                "'dados_YYYY-MM-DD_HH-mm-ss.json'. 3. 'Auto-save' escreve "
                "em arquivo temporario para recuperacao de sessao. 4. 'Limpar' "
                "so reseta memoria — nunca toca em arquivos. 5. 'Carregar' "
                "le um arquivo especifico passado pelo usuario (nunca o auto-save). "
                "6. Historico completo preservado por design. 7. Nao ha botao "
                "de 'desfazer' porque cada salvamento e um ponto de restauracao."
            ),
        },
        {
            "source": "meta_cognition",
            "name": "Framework de Aprendizado Continuo (Auto-Learning)",
            "description": "Sistema que acumula conhecimento automaticamente entre sessoes.",
            "body": (
                "1. Toda interacao relevante (missao, sessao, correcao de bug) "
                "dispara consolidacao. 2. Novos padroes sao extraidos e mergeados "
                "com conhecimento existente (dedup inteligente por similaridade "
                "de texto). 3. Base de conhecimento tem secoes: tecnicas (padroes, "
                "decisoes, bugs) e cognitivas (heuristicas, frameworks, raciocinio). "
                "4. Exportacao portable em Markdown para qualquer IA consumir. "
                "5. Auto-melhoria: detecta gargalos, padroes de erro, e sugestoes "
                "de melhoria baseado em metricas reais. 6. Conhecimento sobrevive "
                "a reset de sessao, troca de modelo, queda de energia."
            ),
        },
    ],
    "bug_fixes": [
        {
            "source": "ler_auditoria",
            "issue": "max_iterations hard stop forca parada prematura mesmo sem objetivo atingido",
            "root_cause": "Loop principal usava while self.iteration < self.max_iterations (100) como criterio de saida, ignorando se o objetivo foi alcancado",
            "fix": "Substituido por deteccao de estagnacao: 30 iteracoes sem progresso. max_iterations subiu para 1000 como seguranca.",
            "category": "loop_control",
        },
        {
            "source": "ler_auditoria",
            "issue": "Score < threshold mas sem failed_steps ia direto para SUCCESS_VERIFIED",
            "root_cause": "_phase_success_eval verificava apenas failed_steps, nao o score real. Se todos steps 'completaram' com bugs, LER considerava sucesso.",
            "fix": "Score < threshold sempre vai para REPLANNING. Idem para _phase_final_audit.",
            "category": "success_evaluation",
        },
        {
            "source": "ler_auditoria",
            "issue": "Executor nao validava resultado real da implementacao",
            "root_cause": "_action_implement retornava string fixa sem verificar se arquivos foram modificados. _action_test so reportava numero de testes sem all_passed.",
            "fix": "Executor agora verifica git diff --stat e git status apos implement/fix/refactor. Testes reportam all_passed.",
            "category": "execution_validation",
        },
        {
            "source": "ler_auditoria",
            "issue": "Nao havia feedback loop do usuario — LER terminava mesmo se objetivo nao fosse atingido",
            "root_cause": "COMPLETED -> _finalize direto, sem perguntar ao usuario se o resultado foi satisfatorio",
            "fix": "Adicionado _ask_user_feedback() em _finalize e _handle_complete. Se usuario rejeita, registra failed_pattern e chama _restart_mission().",
            "category": "user_feedback",
        },
        {
            "source": "ler_auditoria",
            "issue": "Persistencia sem atomicidade — crash no meio do json.dump corrompia arquivo",
            "root_cause": "Escrita direta com json.dump() sem arquivo temporario",
            "fix": "Todas escritas usam arquivo .tmp + os.replace() (atomico em ext4/NTFS).",
            "category": "persistence",
        },
        {
            "source": "ler_auditoria",
            "issue": "Logs sem rotacao — logs cresciam indefinidamente",
            "root_cause": "Session.log escrevia sempre no mesmo arquivo sem limite de tamanho",
            "fix": "_rotate_log() rotaciona em 5 niveis ao atingir 512KB.",
            "category": "observability",
        },
        {
            "source": "ler_auditoria",
            "issue": "Executor.results sem limite — memoria crescia indefinidamente",
            "root_cause": "results dict acumulava resultados sem nunca remover entradas antigas",
            "fix": "MAX_RESULTS=50, remove entrada mais velha ao estourar.",
            "category": "resource_management",
        },
        {
            "source": "ler_auditoria",
            "issue": "Code duplication entre checkpoint.py e persistence.py (~200 linhas duplicadas)",
            "root_cause": "Duas implementacoes paralelas de save/load JSON com logica identica",
            "fix": "Unificado via atomic_write_json()/atomic_read_json() em checkpoint.py, persistence.py delega.",
            "category": "code_quality",
        },
    ],
    "decisions": [
        {
            "source": "ler_arquitetura",
            "decision": "LER usa Python puro (stdlib only) — zero dependencias externas intencionalmente.",
            "rationale": "Portabilidade maxima, sem conflitos de versao, instalavel em qualquer ambiente com Python.",
        },
        {
            "source": "ler_arquitetura",
            "decision": "Estado persiste em JSON (nao SQLite) — legivel, editavel fora do LER, sem migrations.",
            "rationale": "Mesma razao do Android Pure SDK: JSON e human-readable, debuggavel, versionavel no git.",
        },
        {
            "source": "ler_arquitetura",
            "decision": "Checkpoints salvos antes de cada iteracao — sobrevive a crash a qualquer momento.",
            "rationale": "Missao nunca recomeca do zero. restart/resume carrega ultimo checkpoint viavel.",
        },
        {
            "source": "ler_arquitetura",
            "decision": "Pontuacao ponderada com 6 categorias (Req 30%, Func 30%, Testes 10%, DoD 10%, Evidencias 10%, Auditoria 10%).",
            "rationale": "DoD granular com dod_satisfaction forcando verificacao de git commit + passos completados.",
        },
        {
            "source": "ler_arquitetura",
            "decision": "Estrategia selecionada por ranking (cost + risk + time + complexity + success_probability).",
            "rationale": "Estrategias falhas nunca repetidas sem alteracoes. Forca variacao de abordagem.",
        },
        {
            "source": "ler_arquitetura",
            "decision": "Supervisor monitora todos os modulos individualmente — nunca reinicia missao inteira por falha de um modulo.",
            "rationale": "Isolamento de falha: se o validator falha, recupera so o validator, nao o planner.",
        },
        {
            "source": "mp3player",
            "decision": "Metadata busca em multi-fontes: AcoustID -> iTunes BR -> MusicBrainz -> iTunes US fallback.",
            "rationale": "AcoustID falha sempre (API key invalida), mas e aceito — fallback natural para iTunes/MusicBrainz.",
        },
        {
            "source": "mp3player",
            "decision": "SearchMode.NORMAL -> RELAXED auto-fallback se NORMAL retorna null.",
            "rationale": "RELAXED usa thresholds mais baixos e queries mais amplas (title-only, artist-only).",
        },
        {
            "source": "mp3player",
            "decision": "Album art download com redirect loop manual (instanceFollowRedirects=false).",
            "rationale": "Cover Art Archive retorna 302 para archive.org, que falha com FileNotFoundException sem loop explicito.",
        },
        {
            "source": "android_pure_sdk",
            "decision": "Single Activity com FrameLayout + visibilidade (setVisibility) — sem Fragments.",
            "rationale": "Suficiente para ate 5 telas, mais simples, sem dependencias de suporte.",
        },
        {
            "source": "android_pure_sdk",
            "decision": "Form Starts Empty — input forms nunca auto-carregam arquivo ao trocar de aba.",
            "rationale": "Usuario espera blank slate em formularios. Carga explicita via file browser.",
        },
        {
            "source": "android_pure_sdk",
            "decision": "Salvar cria novo arquivo timestampado, nunca sobrescreve existente.",
            "rationale": "Preserva historico. Nao ha 'overwrite' no design — cada salvamento e um snapshot.",
        },
    ],
    "patterns": [
        {
            "source": "android_pure_sdk",
            "title": "aapt + javac + d8 + apksigner",
            "action": "complete_build_pipeline",
            "description": "Pipeline manual Android sem Gradle: aapt package (R.java) -> javac -> jar -> d8 -> aapt package (APK) -> aapt add (dex) -> zipalign -> apksigner",
        },
        {
            "source": "android_pure_sdk",
            "title": "EditText inline editing toggle",
            "action": "inline_editing",
            "description": "Desabilita EditText (enabled=false, focusable=false, cursorVisible=false, background=null) quando nao esta em edicao. Habilita ao editar. Remove TextWatcher velho antes de setText().",
        },
        {
            "source": "android_pure_sdk",
            "title": "Numpad with StringBuilder buffer",
            "action": "numpad_input",
            "description": "StringBuilder priceBuffer com virgula unica. Formatacao: raw -> pad left with zeros -> insert comma at len-2. setAlpha(0) em vez de setVisibility(GONE) para manter grid.",
        },
        {
            "source": "android_pure_sdk",
            "title": "JSON persistence com File parameter",
            "action": "json_persistence",
            "description": "loadFromFile() aceita File parameter (nao so default). saveToFile() cria timestamped file no Salvar. Limpar = screen only, nunca toca em arquivo salvo.",
        },
        {
            "source": "mp3player",
            "title": "Filename artist extraction (two strategies)",
            "action": "filename_parsing",
            "description": "Artist 'Desconhecido'/'<unknown>': Strategy 1 = dash-separated (first segment is artist, last is channel), Strategy 2 = double-space separated (second segment is artist). Segment validated: 2-50 chars, at least one uppercase.",
        },
        {
            "source": "mp3player",
            "title": "iTunes search with scoring thresholds",
            "action": "metadata_search_scoring",
            "description": "Artist exact match +8, partial +5, title word overlap +3 (words >2 chars), album match +3. NORMAL threshold: artist-known min=5, no-artist min=3. RELAXED: 3/2. Tracks best score across all results.",
        },
        {
            "source": "mp3player",
            "title": "AudioProcessor.isActive() must be dynamic",
            "action": "equalizer_dsp",
            "description": "isActive() retorna true apenas quando preampGainDb != 0 || any band gain != 0. queueInput() DEVE chamar inputBuffer.position(inputBuffer.limit()) apos processar. Se nao, ExoPlayer ve 0 bytes consumidos e o audio trava.",
        },
        {
            "source": "mp3player",
            "title": "RenderersFactory for custom AudioProcessor",
            "action": "exoplayer_wiring",
            "description": "MediaCodecAudioRenderer(context, selector, handler, listener, capabilities, eqProc as AudioProcessor) via RenderersFactory. Passing eqProc direkt in constructor ohne @UnstableApi annotation.",
        },
    ],
}


def seed():
    kc = KnowledgeConsolidator(BASE_DIR)
    # Bug fixes
    for fix in SEED["bug_fixes"]:
        if fix not in kc.graph["bug_fixes"]:
            kc.graph["bug_fixes"].append(fix)
    # Decisions
    for dec in SEED["decisions"]:
        if dec not in kc.graph["decisions"]:
            kc.graph["decisions"].append(dec)
    # Technical patterns
    for pat in SEED["patterns"]:
        if pat not in kc.graph["patterns"]:
            kc.graph["patterns"].append(pat)
    # Cognitive patterns
    for c in SEED["cognitive_patterns"]:
        if c not in kc.graph["cognitive_patterns"]:
            kc.graph["cognitive_patterns"].append(c)
    # Heuristics
    for h in SEED["heuristics"]:
        if h not in kc.graph["heuristics"]:
            kc.graph["heuristics"].append(h)
    # Frameworks
    for fw in SEED["frameworks"]:
        if fw not in kc.graph["frameworks"]:
            kc.graph["frameworks"].append(fw)
    kc._smart_merge_all()
    kc._save_graph()
    report = kc.generate_report()
    print(report)
    return {
        "patterns": len(kc.graph["patterns"]),
        "decisions": len(kc.graph["decisions"]),
        "bug_fixes": len(kc.graph["bug_fixes"]),
        "cognitive_patterns": len(kc.graph["cognitive_patterns"]),
        "heuristics": len(kc.graph["heuristics"]),
        "frameworks": len(kc.graph["frameworks"]),
    }


if __name__ == "__main__":
    stats = seed()
    print(
        f"\nSeed concluido: {stats['patterns']} padroes, "
        f"{stats['decisions']} decisoes, {stats['bug_fixes']} bug fixes, "
        f"{stats['cognitive_patterns']} padroes cognitivos, "
        f"{stats['heuristics']} heuristicas, "
        f"{stats['frameworks']} frameworks"
    )
