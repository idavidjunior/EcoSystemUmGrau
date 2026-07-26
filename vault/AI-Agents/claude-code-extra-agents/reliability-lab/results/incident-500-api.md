# Resultado: Incidente 500 apos deploy

## objetivo
API retornando 500 apos deploy. Encontrar causa raiz, hotfix e prevencao.

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
