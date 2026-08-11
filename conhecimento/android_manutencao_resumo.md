# Conhecimento Android Manutenção

## Descrição
Base de conhecimento completa sobre limpeza e manutenção Android via ADB.

## Categorias

### 1. Diagnóstico
- **Comandos ADB**: `dumpsys battery`, `dumpsys meminfo`, `dumpsys cpuinfo`, `df -h`, `du -sh`
- **Diagnósticos**: Espaço em disco, memória RAM, CPU, bateria, rede, processos, cache, logs, atualizações

### 2. Limpeza
- **Cache**: `pm clear <package>`, `rm -rf /data/cache/*`, `rm -rf /sdcard/Android/data/<package>/cache/*`
- **Dados**: `rm -rf /sdcard/DCIM/.thumbnails/*`, `rm -rf /sdcard/Download/*.apk`
- **Logs**: `rm -rf /data/log/*`, `logcat -c`
- **Avançada**: `pm uninstall -k --user 0 <package>`, `pm disable-user --user 0 <package>`

### 3. Manutenção Preventiva
- **Diária**: Verificar apps em background, fechar apps não utilizados
- **Semanal**: Limpeza completa de cache, verificação de atualizações
- **Mensal**: Desinstalar apps não utilizados, verificação de saúde da bateria
- **Trimestral**: Reset de configurações de rede, verificação completa de segurança

### 4. Bateria
- **Comandos**: `dumpsys battery`, `dumpsys batterystats`, `cat /sys/class/power_supply/battery/*`
- **Dicas**: Manter entre 20%-80%, evitar carregamento prolongado, não usar durante carga

### 5. Armazenamento
- **Comandos**: `df -h`, `du -sh /sdcard/*`, `find /sdcard -name '*.mp4' -size +100M`
- **Estratégias**: Mover mídias para cloud, comprimir vídeos antigos, limpar downloads

### 6. Rede
- **Comandos**: `dumpsys connectivity`, `dumpsys wifi`, `ping 8.8.8.8`, `ip addr show`
- **Problemas**: WiFi desconectando, lentidão, DNS não resolve, IP conflitante

### 7. Segurança
- **Comandos**: `pm list packages -f`, `dumpsys package <package>`, `getprop ro.debuggable`
- **Verificações**: Permissões perigosas, root detection, USB debugging, apps suspeitos

### 8. Desempenho
- **Comandos**: `dumpsys meminfo`, `dumpsys cpuinfo`, `top -n 1`, `dumpsys gfxinfo`
- **Otimizações**: Limitar apps em background, desativar animações, limpar RAM

## Scripts Criados
1. `android_diagnostico.py` - Diagnóstico completo do dispositivo
2. `android_limpeza.py` - Limpeza de cache, dados, logs
3. `android_manutencao.py` - Manutenção preventiva e otimização

## Uso
```bash
# Diagnóstico completo
python scripts/android_diagnostico.py

# Limpeza segura
python scripts/android_limpeza.py --seguro

# Manutenção preventiva
python scripts/android_manutencao.py
```

## Última Atualização
2026-08-11