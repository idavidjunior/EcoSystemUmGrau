# CLI-Anything — Metodologia Soberana do Ecossistema

## Propósito
Transformar qualquer software com código-fonte disponível numa interface de linha de comando (CLI) controlável por agentes de IA, seguindo metodologia padronizada de 7 fases. O agente opera o software sem interface gráfica, via CLI + REPL + saída JSON.

## Origem e soberania
- Derivado do projeto externo HKUDS/CLI-Anything (licença MIT), internalizado neste ecossistema.
- Referência completa preservada LOCALMENTE: `references/HARNESS.md` nesta pasta. Nunca depender do GitHub para consultar a metodologia.
- Comandos globais instalados em `~/.config/opencode/commands/`: `/cli-anything`, `/cli-anything-refine`, `/cli-anything-test`, `/cli-anything-validate`, `/cli-anything-list` mais `HARNESS.md`.
- Se os comandos externos forem perdidos ou descontinuados, esta skill mais `references/HARNESS.md` bastam para reconstruir tudo sozinho. Autossuficiência total.

## As 7 fases da metodologia
1. ANALISE DO CODEBASE. Identificar o motor backend separado da apresentação, mapear cada ação da GUI para chamadas de API, identificar o modelo de dados (XML, JSON, binário, banco), encontrar CLIs já existentes do backend (são blocos de construção) e catalogar o sistema de comandos/undo se houver.
2. ARQUITETURA DA CLI. Escolher modelo de interação: REPL com estado para sessões interativas, subcomandos para operações pontuais, ou ambos (recomendado). Definir grupos de comandos por domínio: gerência de projeto, operações nucleares, import/export, configuração, estado/sessão. Projetar o modelo de estado persistido e o formato de saída duplo, legível para humanos e JSON para agentes via flag --json.
3. IMPLEMENTACAO. Começar pela camada de dados. Adicionar comandos de inspeção antes dos de mutação (agente inspeciona antes de modificar). Módulo backend que localiza o executável real via shutil.which, invoca via subprocess.run com tratamento de erro claro e instruções de instalação. Gerenciamento de sessão com travamento exclusivo de arquivo para evitar corrupção concorrente. REPL como comportamento padrão quando a CLI roda sem argumentos.
4. PLANO DE TESTES ANTES DO CODIGO. Criar TEST.md com inventário planejado de testes unitários e E2E, casos extremos e fluxos de trabalho realistas multi-etapa. Nenhum código de teste escrito antes deste plano.
5. TESTES. Unitarios isolados com dados sintéticos. E2E que invocam o software REAL, sem degradação graciosa: se o software não está instalado, o teste falha, não pula. Verificação programática de saída: magic bytes, estrutura ZIP/OOXML, análise de pixels e áudio. Testes de subprocesso usando resolução dinâmica do comando instalado, nunca caminhos fixos. Teste round-trip (cria via CLI, abre na GUI, valida) e teste por agente (tarefa real usando só a CLI).
6. DOCUMENTACAO DOS RESULTADOS. Anexar ao TEST.md a saida completa do pytest, estatísticas de aprovação, tempo e lacunas de cobertura. O TEST.md vira registro completo do processo.
7. SKILL E REFINAMENTO. Gerar SKILL.md autocontida para descoberta por agentes. O comando /refine executa análise de lacunas entre capacidade total do software e cobertura atual da CLI, implementando incrementalmente novos comandos, testes e documentação. Rodar /refine várias vezes até cobertura de produção.

## Regras do ecossistema ao aplicar esta metodologia
- Toda comunicação, documentação gerada e mensagens de commit em pt-BR.
- Seguir o Protocolo Permanente de Engenharia: classificar tarefa, entender antes de codificar, testes adversariais, quality gates.
- Alterações de config passam pelo preflight_check.py antes de aplicar.
- Persistência em git exclusivamente via gate scripts/persistencia.ps1.
- Registrar aprendizado ao final de cada harness construído (memory_engine add tipo padrao).
- Modelos fracos produzem CLIs incompletas; software fechado compilado degrada cobertura. Preferir código-fonte aberto e iterar com /refine.

## Como usar
Via comandos globais do OpenCode: /cli-anything ./caminho-do-software para construir, /cli-anything-refine ./software "área foco" para expandir, /cli-anything-test ./software para testar, /cli-anything-validate ./software para validar, /cli-anything-list para listar harnesses existentes.
Sem os comandos (fallback soberano): ler references/HARNESS.md completo e executar as 7 fases manualmente nesta ordem.
