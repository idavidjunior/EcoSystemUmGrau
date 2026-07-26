# Resultado: Migracao de schema sem downtime

## objetivo
Planejar migracao expand-contract com rollback seguro.

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
