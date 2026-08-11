"""android_diagnostico.py — Diagnóstico completo de dispositivos Android via ADB.

Uso:
  python scripts/android_diagnostico.py                # diagnóstico completo
  python scripts/android_diagnostico.py --bateria      # só bateria
  python scripts/android_diagnostico.py --armazenamento # só armazenamento
  python scripts/android_diagnostico.py --desempenho   # só desempenho
  python scripts/android_diagnostico.py --rede         # só rede
  python scripts/android_diagnostico.py --seguranca    # só segurança
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADB = "adb"


def run_adb(cmd, timeout=30):
    """Executa comando ADB e retorna saída."""
    try:
        result = subprocess.run(
            [ADB] + cmd.split(),
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
        return result.stdout.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "TIMEOUT", 1
    except Exception as e:
        return f"ERRO: {e}", 1


def verificar_conexao():
    """Verifica se há dispositivo Android conectado."""
    saida, rc = run_adb("devices")
    if rc != 0:
        return False, "ADB não encontrado ou não configurado"
    
    linhas = saida.splitlines()
    dispositivos = [l for l in linhas[1:] if l.strip() and "device" in l]
    
    if not dispositivos:
        return False, "Nenhum dispositivo conectado"
    
    return True, dispositivos[0].split()[0]


def diagnostico_bateria():
    """Diagnóstico completo de bateria."""
    print("=== DIAGNÓSTICO DE BATERIA ===\n")
    
    # Status da bateria
    saida, _ = run_adb("shell dumpsys battery")
    print("--- Status da Bateria ---")
    for linha in saida.splitlines():
        if any(k in linha.lower() for k in ["level", "status", "health", "temperature", "voltage", "technology"]):
            print(f"  {linha.strip()}")
    
    # Estatísticas de bateria
    saida, _ = run_adb("shell dumpsys batterystats --charged")
    linhas = saida.splitlines()
    
    print("\n--- Estatísticas ---")
    for linha in linhas[:20]:
        if any(k in linha.lower() for k in ["discharge", "charge", "screen", "wifi", "bluetooth", "mobile"]):
            print(f"  {linha.strip()}")
    
    # Temperatura
    try:
        temp_file = Path("/sys/class/power_supply/battery/temperature")
        if temp_file.exists():
            temp = int(temp_file.read_text().strip()) / 10
            print(f"\n--- Temperatura ---")
            print(f"  {temp}°C")
            if temp > 45:
                print("  ⚠️  ATENÇÃO: Temperatura alta!")
            elif temp < 10:
                print("  ⚠️  ATENÇÃO: Temperatura baixa!")
    except:
        pass
    
    print()


def diagnostico_armazenamento():
    """Diagnóstico de armazenamento."""
    print("=== DIAGNÓSTICO DE ARMAZENAMENTO ===\n")
    
    # Espaço total
    saida, _ = run_adb("shell df -h /data")
    print("--- Espaço em Disco ---")
    for linha in saida.splitlines():
        if "/data" in linha or "Filesystem" in linha:
            print(f"  {linha.strip()}")
    
    # Uso por diretório principal
    print("\n--- Uso por Diretório ---")
    diretorios = ["/sdcard", "/data/data", "/data/app", "/data/dalvik-cache"]
    for dir_path in diretorios:
        saida, rc = run_adb(f"shell du -sh {dir_path}", timeout=15)
        if rc == 0:
            print(f"  {saida}")
    
    # Arquivos grandes
    print("\n--- Arquivos Grandes (>100MB) ---")
    saida, _ = run_adb("shell find /sdcard -name '*.mp4' -size +100M -exec ls -lh {} \\;", timeout=30)
    if saida and "No such file" not in saida:
        for linha in saida.splitlines()[:5]:
            print(f"  {linha.strip()}")
    else:
        print("  Nenhum arquivo grande encontrado")
    
    # Thumbnails
    print("\n--- Thumbnails (podem ser limpos) ---")
    saida, _ = run_adb("shell du -sh /sdcard/DCIM/.thumbnails")
    if "No such file" not in saida:
        print(f"  {saida}")
    
    saida, _ = run_adb("shell du -sh /sdcard/Pictures/.thumbnails")
    if "No such file" not in saida:
        print(f"  {saida}")
    
    print()


def diagnostico_desempenho():
    """Diagnóstico de desempenho."""
    print("=== DIAGNÓSTICO DE DESEMPENHO ===\n")
    
    # Uso de memória
    saida, _ = run_adb("shell dumpsys meminfo")
    print("--- Uso de Memória ---")
    linhas = saida.splitlines()
    for linha in linhas[:15]:
        if any(k in linha.lower() for k in ["total", "free", "cached", "used"]):
            print(f"  {linha.strip()}")
    
    # Uso de CPU
    saida, _ = run_adb("shell dumpsys cpuinfo")
    print("\n--- Uso de CPU ---")
    linhas = saida.splitlines()
    for linha in linhas[:10]:
        if "%" in linha:
            print(f"  {linha.strip()}")
    
    # Processos top
    saida, _ = run_adb("shell top -n 1 -d 1")
    print("\n--- Top Processos ---")
    linhas = saida.splitlines()
    for i, linha in enumerate(linhas[1:11]):
        if linha.strip():
            print(f"  {linha.strip()}")
    
    # Graphics info
    saida, _ = run_adb("shell dumpsys gfxinfo")
    print("\n--- Graphics Info ---")
    linhas = saida.splitlines()
    for linha in linhas[:10]:
        if any(k in linha.lower() for k in ["janky", "frame", "render"]):
            print(f"  {linha.strip()}")
    
    print()


def diagnostico_rede():
    """Diagnóstico de rede."""
    print("=== DIAGNÓSTICO DE REDE ===\n")
    
    # WiFi
    saida, _ = run_adb("shell dumpsys wifi")
    print("--- WiFi ---")
    linhas = saida.splitlines()
    for linha in linhas[:10]:
        if any(k in linha.lower() for k in ["ssid", "bssid", "rssi", "link speed", "ip"]):
            print(f"  {linha.strip()}")
    
    # Conectividade
    saida, _ = run_adb("shell dumpsys connectivity")
    print("\n--- Conectividade ---")
    linhas = saida.splitlines()
    for linha in linhas[:10]:
        if any(k in linha.lower() for k in ["active", "wifi", "mobile", "network"]):
            print(f"  {linha.strip()}")
    
    # IP
    saida, _ = run_adb("shell ip addr show")
    print("\n--- Endereços IP ---")
    for linha in saida.splitlines():
        if "inet " in linha and "127.0.0.1" not in linha:
            print(f"  {linha.strip()}")
    
    # Ping
    saida, rc = run_adb("shell ping -c 3 8.8.8.8", timeout=10)
    print("\n--- Ping Google DNS ---")
    if rc == 0:
        for linha in saida.splitlines():
            if "rtt" in linha or "time=" in linha:
                print(f"  {linha.strip()}")
    else:
        print("  Falha no ping")
    
    print()


def diagnostico_seguranca():
    """Diagnóstico de segurança."""
    print("=== DIAGNÓSTICO DE SEGURANÇA ===\n")
    
    # USB Debugging
    saida, _ = run_adb("shell settings get global adb_enabled")
    print(f"--- USB Debugging ---")
    print(f"  Status: {'ATIVO' if saida.strip() == '1' else 'INATIVO'}")
    if saida.strip() == '1':
        print("  ⚠️  ATENÇÃO: USB Debugging ativo - risco de segurança")
    
    # Root status
    saida, rc = run_adb("shell su -c id")
    print(f"\n--- Root ---")
    if rc == 0 and "uid=0" in saida:
        print("  Status: ROOT DETECTADO")
        print("  ⚠️  ATENÇÃO: Dispositivo com root")
    else:
        print("  Status: Sem root")
    
    # Apps instalados
    saida, _ = run_adb("shell pm list packages -3")
    print(f"\n--- Apps de Terceiros ---")
    linhas = saida.splitlines()
    print(f"  Total: {len(linhas)} apps")
    
    # Permissões perigosas
    print(f"\n--- Permissões Críticas ---")
    permissoes_perigosas = [
        "android.permission.READ_SMS",
        "android.permission.SEND_SMS",
        "android.permission.CAMERA",
        "android.permission.RECORD_AUDIO",
        "android.permission.ACCESS_FINE_LOCATION",
        "android.permission.READ_CONTACTS",
        "android.permission.READ_CALL_LOG"
    ]
    
    for perm in permissoes_perigosas:
        saida, _ = run_adb(f"shell pm list packages -f | grep -i '{perm}'")
        if saida:
            print(f"  ⚠️  {perm}")
    
    # Verificar atualizações de segurança
    saida, _ = run_adb("shell getprop ro.build.version.security_patch")
    print(f"\n--- Padrão de Segurança ---")
    print(f"  Última atualização: {saida}")
    
    print()


def diagnostico_completo():
    """Executa diagnóstico completo."""
    print("╔══════════════════════════════════════════╗")
    print("║   DIAGNÓSTICO COMPLETO ANDROID           ║")
    print("╚══════════════════════════════════════════╝\n")
    
    # Verificar conexão
    conectado, info = verificar_conexao()
    if not conectado:
        print(f"❌ {info}")
        print("Verifique se o dispositivo está conectado e USB Debugging ativo.")
        return
    
    print(f"✅ Dispositivo conectado: {info}\n")
    
    # Informações básicas
    modelo, _ = run_adb("shell getprop ro.product.model")
    android, _ = run_adb("shell getprop ro.build.version.release")
    fabricante, _ = run_adb("shell getprop ro.product.manufacturer")
    
    print("--- Informações do Dispositivo ---")
    print(f"  Fabricante: {fabricante}")
    print(f"  Modelo: {modelo}")
    print(f"  Android: {android}")
    print()
    
    # Executar diagnósticos
    diagnostico_bateria()
    diagnostico_armazenamento()
    diagnostico_desempenho()
    diagnostico_rede()
    diagnostico_seguranca()
    
    print("╔══════════════════════════════════════════╗")
    print("║   DIAGNÓSTICO CONCLUÍDO                  ║")
    print("╚══════════════════════════════════════════╝")


def main():
    if len(sys.argv) > 1:
        opcao = sys.argv[1]
        if opcao == "--bateria":
            diagnostico_bateria()
        elif opcao == "--armazenamento":
            diagnostico_armazenamento()
        elif opcao == "--desempenho":
            diagnostico_desempenho()
        elif opcao == "--rede":
            diagnostico_rede()
        elif opcao == "--seguranca":
            diagnostico_seguranca()
        else:
            print("Opção inválida. Use: --bateria, --armazenamento, --desempenho, --rede, --seguranca")
    else:
        diagnostico_completo()


if __name__ == "__main__":
    main()