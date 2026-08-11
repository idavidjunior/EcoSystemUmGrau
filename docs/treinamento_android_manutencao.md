# Treinamento Android Manutenção - Jarvis

## Objetivo
Capacitar o Jarvis a realizar diagnóstico, limpeza e manutenção preventiva em dispositivos Android via ADB.

## Comandos Essenciais

### 1. Diagnóstico
```bash
# Diagnóstico completo
python scripts/android_diagnostico.py

# Diagnóstico por categoria
python scripts/android_diagnostico.py --bateria
python scripts/android_diagnostico.py --armazenamento
python scripts/android_diagnostico.py --desempenho
python scripts/android_diagnostico.py --rede
python scripts/android_diagnostico.py --seguranca
```

### 2. Limpeza
```bash
# Limpeza completa
python scripts/android_limpeza.py

# Limpeza por tipo
python scripts/android_limpeza.py --cache
python scripts/android_limpeza.py --downloads
python scripts/android_limpeza.py --thumbnails
python scripts/android_limpeza.py --logs
python scripts/android_limpeza.py --apps

# Limpeza segura (sem dados pessoais)
python scripts/android_limpeza.py --seguro
```

### 3. Manutenção Preventiva
```bash
# Manutenção completa
python scripts/android_manutencao.py

# Manutenção por tipo
python scripts/android_manutencao.py --otimizar
python scripts/android_manutencao.py --atualizar
python scripts/android_manutencao.py --backup
python scripts/android_manutencao.py --relatorio
```

## Fluxos de Trabalho

### Fluxo 1: Diagnóstico Inicial
1. Verificar conexão ADB: `adb devices`
2. Executar diagnóstico completo: `python scripts/android_diagnostico.py`
3. Analisar resultados e identificar problemas
4. Criar plano de ação baseado nos achados

### Fluxo 2: Limpeza Periódica
1. Executar limpeza segura: `python scripts/android_limpeza.py --seguro`
2. Verificar espaço liberado
3. Documentar mudanças

### Fluxo 3: Manutenção Preventiva
1. Executar manutenção completa: `python scripts/android_manutencao.py`
2. Revisar relatório gerado
3. Aplicar recomendações
4. Agendar próxima manutenção

### Fluxo 4: Resolução de Problemas
1. Diagnosticar problema específico
2. Identificar causa raiz
3. Aplicar solução apropriada
4. Verificar eficácia

## Integração com Ecossistema

### Scripts Disponíveis
- `android_diagnostico.py` - Diagnóstico completo
- `android_limpeza.py` - Limpeza de cache, dados, logs
- `android_manutencao.py` - Manutenção preventiva

### Base de Conhecimento
- `conhecimento/android_manutencao.json` - Conhecimento completo
- `conhecimento/android_manutencao_resumo.md` - Resumo executivo

### Habilidade ADB
- `mcp/android/habilidades/adb-perito/SKILL.md` - Atualizada com comandos de manutenção

## Comandos ADB Úteis

### Diagnóstico
```bash
adb shell dumpsys battery          # Status da bateria
adb shell dumpsys meminfo          # Uso de memória
adb shell dumpsys cpuinfo          # Uso de CPU
adb shell df -h                    # Espaço em disco
adb shell du -sh /sdcard/*         # Uso por diretório
adb shell top -n 1                 # Processos ativos
```

### Limpeza
```bash
adb shell pm clear <package>       # Limpar cache do app
adb shell rm -rf /data/cache/*     # Limpar cache do sistema
adb shell rm -rf /sdcard/DCIM/.thumbnails/*  # Limpar thumbnails
adb shell logcat -c                # Limpar logs
```

### Manutenção
```bash
adb shell am kill-all              # Liberar memória
adb shell pm trim-caches 0         # Otimizar cache
adb shell dumpsys batterystats --reset  # Resetar estatísticas
```

## Boas Práticas

1. **Sempre verificar conexão ADB** antes de executar comandos
2. **Fazer backup** antes de limpezas profundas
3. **Não deletar dados pessoais** sem confirmação do usuário
4. **Documentar todas as operações** realizadas
5. **Verificar resultados** após cada operação

## Checklist de Manutenção

### Diário
- [ ] Verificar apps em background
- [ ] Fechar apps não utilizados
- [ ] Verificar nível de bateria

### Semanal
- [ ] Executar limpeza de cache
- [ ] Verificar atualizações
- [ ] Analisar uso de bateria
- [ ] Limpar downloads antigos

### Mensal
- [ ] Desinstalar apps não utilizados
- [ ] Verificar saúde da bateria
- [ ] Fazer backup de dados
- [ ] Atualizar sistema

### Trimestral
- [ ] Reset de configurações de rede
- [ ] Verificação completa de segurança
- [ ] Otimização de armazenamento
- [ ] Análise de desempenho geral

## Última Atualização
2026-08-11