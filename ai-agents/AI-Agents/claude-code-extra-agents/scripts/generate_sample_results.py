#!/usr/bin/env python3
"""Generate sample reliability lab results for testing the feedback loop.

This script creates realistic result files for each scenario so that
the evaluation and feedback loop can be properly tested.
"""

import json
from pathlib import Path
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parent.parent
RELIABILITY_LAB = ROOT / "reliability-lab"
SCENARIOS_DIR = RELIABILITY_LAB / "scenarios"
RESULTS_DIR = RELIABILITY_LAB / "results"


def load_scenarios() -> list[dict]:
    """Load all scenario definitions."""
    scenarios = []
    for path in sorted(SCENARIOS_DIR.glob("*.json")):
        scenarios.append(json.loads(path.read_text(encoding="utf-8")))
    return scenarios


def generate_result(scenario: dict) -> str:
    """Generate a realistic result for a scenario.
    
    Args:
        scenario: Scenario definition.
        
    Returns:
        Markdown content for the result.
    """
    agent = scenario["agent"]
    title = scenario["title"]
    prompt = scenario["prompt"]
    must_include = scenario.get("must_include", [])
    
    # Generate content based on scenario type
    if "incident" in scenario["id"]:
        content = f"""# Resultado: {title}

## objetivo
{prompt}

## contexto
API retornando erro 500 após deploy em produção. Logs indicam timeout na conexão com banco de dados.

## analise
Causa raiz identificada: configuração de pool de conexões insuficiente para carga pós-deploy.
O novo serviço aumentou o número de conexões simultâneas em 40%.

## acoes
1. Aumentar max_connections no pool
2. Implementar circuit breaker
3. Adicionar monitoramento de saúde do pool

## passos
1. Editar config/database.yml
2. Alterar max_connections de 50 para 100
3. Reiniciar serviço gradualmente
4. Monitorar métricas por 24h

## comandos
```bash
kubectl rollout restart deployment/api-service
kubectl logs -f deployment/api-service | grep -i "connection pool"
```

## validacao
- API respondendo com status 200
- Tempo de resposta < 200ms
- Zero erros 500 por 1 hora consecutiva

## fontes
- Logs do CloudWatch (2024-01-15 14:00-15:00 UTC)
- Métricas do DataDog
- Configuração atual do database.yml

## limitacoes
- Analise baseada apenas em logs disponíveis
- Não foi possível reproduzir em ambiente de staging
- Suposição de que carga é similar ao horário de pico anterior

## nao_verificado
- Impacto em outros serviços dependentes
- Performance sob carga extrema (stress test)

## escopo
Focado exclusivamente no erro 500 e causa raiz no banco de dados.
Não cobre otimizações de performance além do necessário para resolver o incidente.

## resultado
Hotfix aplicado com sucesso. Rollback disponível se necessário via:
```bash
kubectl rollout undo deployment/api-service --to-revision=42
```

Prevenção futura: implementar auto-scaling do pool baseado em métricas em tempo real.
"""
    
    elif "migration" in scenario["id"]:
        content = f"""# Resultado: {title}

## objetivo
{prompt}

## contexto
Banco PostgreSQL 12 precisa ser migrado para versão 15. Sistema requer disponibilidade 24/7.

## analise
Estratégia recomendada: expand-contract pattern com replicação lógica.
Risco principal: incompatibilidade de tipos de dados entre versões.

Fases do expand-contract:
1. Expand: adicionar nova coluna/estrutura sem remover a antiga
2. Backfill: migrar dados gradualmente em lotes pequenos
3. Contract: remover estrutura antiga após validação completa

## acoes
1. Setup de replicação lógica
2. Migração incremental em lotes (backfill)
3. Validação de consistência
4. Cutover controlado
5. Rollback preparado

## passos
1. Instalar PostgreSQL 15 em novo servidor
2. Configurar publicação/assinatura de replicação
3. Executar pg_dump --schema-only para validação
4. Migrar tabelas em ordem de dependência
5. Validar checksums
6. Realizar cutover durante janela de menor carga

## comandos
```bash
pg_create_logical_replication_slot 'migration_slot' pgoutput
pg_basebackup -D /var/lib/postgresql/15/data -Fp -Xs -P -R
pg_logical_slot_get_changes 'migration_slot' NULL NULL
```

## validacao
- Todos os índices reconstruídos
- Contagem de linhas idêntica
- Checksums MD5 das tabelas críticas conferem
- Queries de benchmark dentro de 5% da performance original

## fontes
- Documentação oficial PostgreSQL 12->15
- Relatórios de incompatibilidades conhecidas
- Baseline de performance atual

## limitacoes
- Testado apenas com subset de 10% dos dados
- Assume rede estável entre servidores
- Não considera picos de carga imprevistos

## nao_verificado
- Performance de queries complexas não testadas em staging
- Integração com ferramentas de backup de terceiros

## escopo
Migração técnica do banco de dados usando expand-contract pattern.

## resultado
Plano de migração aprovado com estratégia de rollback seguro.
Rollback possível mantendo réplica antiga ativa por 48h pós-migração.
Backfill realizado em lotes de 10000 registros para minimizar impacto.
"""
    
    elif "review" in scenario["id"]:
        content = f"""# Resultado: {title}

## objetivo
{prompt}

## contexto
PR contém código gerado por Copilot para feature de autenticação OAuth2.

## analise
Código funcional mas com problemas de segurança identificados:
1. Tokens armazenados em localStorage (deveria ser httpOnly cookie)
2. Falta validação de estado OAuth
3. Timeout de sessão muito longo (24h)

Achados principais organizados por severidade.

## acoes
1. Refatorar armazenamento de tokens
2. Implementar PKCE flow
3. Reduzir timeout para 1h com refresh token
4. Adicionar testes de segurança

## passos
1. Criar middleware para cookies httpOnly
2. Implementar geração e validação de estado OAuth
3. Configurar refresh token rotation
4. Escrever testes de integração

## comandos
```bash
npm test -- --testPathPattern=auth
npm run lint:security
npx audit-ci --config .audit-ci.json
```

## validacao
- Todos os testes passando
- Zero vulnerabilidades críticas no audit
- Code coverage > 80% em módulos de auth
- Aprovação de pelo menos 2 revisores seniores

## fontes
- OWASP Authentication Cheat Sheet
- RFC 6749 (OAuth 2.0)
- RFC 7636 (PKCE)
- Guidelines internos de segurança

## limitacoes
- Revisão focada apenas em módulo de autenticação
- Não avalia performance sob carga
- Assume implementação correta do backend

## nao_verificado
- Compatibilidade com navegadores antigos (IE11)
- Integração com SSO corporativo

## escopo
Revisão de segurança e qualidade do código de autenticação.

## resultado
PR aprovado com mudanças solicitadas. Requer re-review após correções.

### Achados por Severidade

**Crítico:**
- Arquivo: `src/auth/token-storage.ts` - Tokens em localStorage

**Alto:**
- Arquivo: `src/auth/oauth-handler.ts` - Falta validação de estado

**Médio:**
- Arquivo: `src/auth/session-config.ts` - Timeout excessivo

Checklist de segurança anexo ao PR com teste específico para cada achado.
"""
    
    elif "security" in scenario["id"] or "dependency" in scenario["id"]:
        content = f"""# Resultado: {title}

## objetivo
{prompt}

## contexto
Projeto Node.js com 247 dependências diretas e indiretas.
Última auditoria há 3 meses.

## analise
Foram identificadas 12 vulnerabilidades CVE:
- 2 críticas (CVE-2024-1234, CVE-2024-5678)
- 4 altas
- 6 médias

Dependência crítica: lodash < 4.17.21 permite prototype pollution.

Impacto avaliado por categoria de risco.

## acoes
1. Atualizar lodash para 4.17.21+
2. Atualizar axios para 1.6.0+
3. Substituir pacote abandonado node-uuid por uuid
4. Configurar Dependabot para updates automáticos

## passos
1. npm audit --json > audit-before.json
2. npm update lodash axios uuid
3. npm install uuid@latest --save
4. npm test para validar compatibilidade
5. npm audit --json > audit-after.json
6. Configurar .github/dependabot.yml

## comandos
```bash
npm audit fix --force
npm ls lodash
npx npm-check-updates -u
npm test
```

## validacao
- npm audit reporta 0 vulnerabilidades críticas/altas
- Todos os testes passando
- Build CI verde
- Sem breaking changes em APIs públicas

## fontes
- npm audit
- GitHub Security Advisories
- CVE Details Database
- Snyk Vulnerability DB

## limitacoes
- Audit limitado a dependências npm
- Não verifica vulnerabilidades em runtime
- Assume lockfile atualizado

## nao_verificado
- Vulnerabilidades em dependências de desenvolvimento
- Compatibilidade com versões antigas do Node.js

## escopo
Auditoria de dependências JavaScript/Node.js apenas.

## resultado
10 vulnerabilidades resolvidas. 2 médias permanecem aguardando upstream.

### Matriz de Prioridade e Mitigação

| CVE | Impacto | Prioridade | Mitigação |
|-----|---------|------------|-----------|
| CVE-2024-1234 | Crítico | P0 | Update imediato para lodash 4.17.21+ |
| CVE-2024-5678 | Crítico | P0 | Patch de segurança aplicado |
| CVE-2024-9012 | Alto | P1 | Agendar update na próxima sprint |
| CVE-2024-3456 | Alto | P1 | Workaround implementado |

Plano de mitigação documentado para casos residuais.
"""
    
    else:
        # Generic fallback
        content = f"""# Resultado: {title}

## objetivo
{prompt}

## contexto
Análise realizada conforme especificação do cenário.

## analise
Problema identificado e analisado em detalhes.
Causa raiz determinada através de investigação sistemática.

## acoes
1. Ação prioritária imediata
2. Correção de curto prazo
3. Prevenção de longo prazo

## passos
1. Identificar componente afetado
2. Isolar causa do problema
3. Implementar solução
4. Validar resultado

## comandos
```bash
# Comandos específicos seriam listados aqui
echo "Implementação pendente"
```

## validacao
- Critérios de aceitação atendidos
- Testes relevantes passando
- Stakeholders satisfeitos

## fontes
- Documentação do projeto
- Logs disponíveis
- Entrevistas com equipe

## limitacoes
- Análise baseada em informações disponíveis
- Recursos limitados para investigação profunda

## nao_verificado
- Impactos colaterais não intencionais
- Performance em escala

## escopo
Conforme definido no cenário.

## resultado
Solução implementada e validada.
"""
    
    return content


def main() -> None:
    """Generate result files for all scenarios."""
    print("Generating sample reliability lab results...")
    
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    scenarios = load_scenarios()
    
    for scenario in scenarios:
        result_path = RESULTS_DIR / f"{scenario['id']}.md"
        content = generate_result(scenario)
        result_path.write_text(content, encoding="utf-8")
        print(f"  Generated: {result_path.name}")
    
    print(f"\nGenerated {len(scenarios)} result files.")
    print("You can now run evaluate_reliability_lab.py followed by orchestrate_feedback_loop.py")


if __name__ == "__main__":
    main()
