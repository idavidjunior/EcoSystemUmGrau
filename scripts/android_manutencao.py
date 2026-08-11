"""android_manutencao.py — Manutenção preventiva de dispositivos Android via ADB.

Uso:
  python scripts/android_manutencao.py                # manutenção completa
  python scripts/android_manutencao.py --otimizar     # só otimização
  python scripts/android_manutencao.py --atualizar    # só verifica atualizações
  python scripts/android_manutencao.py --backup       # só backup
  python scripts/android_manutencao.py --relatorio    # gera relatório completo
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADB = "adb"
LOG_FILE = ROOT / "runtime" / "android_manutencao.log"
REPORT_FILE = ROOT / "runtime" / "relatorio_android.json"


def log(mensagem):
    """Registra mensagem no log."""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {mensagem}\n")
    except:
        pass


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


def obter_info_dispositivo():
    """Obtém informações básicas do dispositivo."""
    info = {}
    
    comandos = {
        "modelo": "shell getprop ro.product.model",
        "fabricante": "shell getprop ro.product.manufacturer",
        "android": "shell getprop ro.build.version.release",
        "api": "shell getprop ro.build.version.sdk",
        "serial": "shell getprop ro.serialno",
        "bateria_level": "shell dumpsys battery | grep level",
        "bateria_status": "shell dumpsys battery | grep status",
        "armazenamento_total": "shell df -h /data | tail -1 | awk '{print $2}'",
        "armazenamento_usado": "shell df -h /data | tail -1 | awk '{print $3}'",
        "memoria_total": "shell cat /proc/meminfo | grep MemTotal",
    }
    
    for chave, cmd in comandos.items():
        saida, _ = run_adb(cmd)
        if saida and "ERRO" not in saida:
            # Limpar saída
            saida = saida.replace("package:", "").replace("level:", "").replace("status:", "").strip()
            info[chave] = saida
    
    return info


def otimizar_dispositivo():
    """Otimiza performance do dispositivo."""
    print("=== OTIMIZAÇÃO DO DISPOSITIVO ===\n")
    
    comandos = [
        ("Liberar memória", "shell am kill-all"),
        ("Limpar cache do runtime", "shell pm trim-caches 0"),
        ("Otimizar bateria", "shell dumpsys batterystats --reset"),
        ("Limpar DNS", "shell ndc resolver clearnetdns wlan0"),
        ("Sincronizar dados", "shell cmd jobscheduler run -f com.android.providers.downloads 0"),
    ]
    
    for nome, cmd in comandos:
        print(f"Executando {nome}...", end="", flush=True)
        saida, rc = run_adb(cmd, timeout=15)
        if rc == 0:
            print(" ✅")
            log(f"Otimização: {nome}")
        else:
            print(" ⚠️  (pode precisar de permissões)")
    
    print()


def verificar_atualizacoes():
    """Verifica atualizações disponíveis."""
    print("=== VERIFICAÇÃO DE ATUALIZAÇÕES ===\n")
    
    # Verificar atualização do sistema
    print("--- Sistema ---")
    saida, _ = run_adb("shell pm list packages -s")
    pacotes_sistema = len(saida.splitlines())
    print(f"  Pacotes do sistema: {pacotes_sistema}")
    
    # Verificar permissões pendentes
    print("\n--- Permissões ---")
    saida, _ = run_adb("shell pm list permissions -d")
    permissoes_pendentes = len(saida.splitlines())
    print(f"  Permissões negadas: {permissoes_pendentes}")
    
    # Verificar apps desatualizados
    print("\n--- Apps ---")
    saida, _ = run_adb("shell pm list packages -3")
    pacotes_terceiros = len(saida.splitlines())
    print(f"  Apps de terceiros: {pacotes_terceiros}")
    
    # Verificar segurança
    print("\n--- Segurança ---")
    saida, _ = run_adb("shell getprop ro.build.version.security_patch")
    print(f"  Padrão de segurança: {saida}")
    
    saida, _ = run_adb("shell getprop ro.build.date")
    print(f"  Última build: {saida}")
    
    print()


def criar_backup_config():
    """Cria backup de configurações importantes."""
    print("=== BACKUP DE CONFIGURAÇÕES ===\n")
    
    backup_dir = ROOT / "runtime" / "android_backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Backup de configurações
    configs = {
        "wifi": "shell dumpsys wifi > {}/wifi.txt",
        "bateria": "shell dumpsys battery > {}/battery.txt",
        "memoria": "shell dumpsys meminfo > {}/meminfo.txt",
        "apps": "shell pm list packages -3 > {}/packages.txt",
        "permissions": "shell dumpsys permissions > {}/permissions.txt",
    }
    
    for nome, cmd_template in configs.items():
        cmd = cmd_template.format(backup_dir)
        print(f"Backup de {nome}...", end="", flush=True)
        saida, rc = run_adb(cmd)
        if rc == 0:
            # Salvar saída em arquivo
            arquivo = backup_dir / f"{nome}.txt"
            arquivo.write_text(saida, encoding="utf-8")
            print(" ✅")
            log(f"Backup: {nome}")
        else:
            print(" ⚠️")
    
    print(f"\n✅ Backup salvo em: {backup_dir}")


def verificar_saude_bateria():
    """Verifica saúde da bateria."""
    print("=== SAÚDE DA BATERIA ===\n")
    
    saida, _ = run_adb("shell dumpsys battery")
    
    info_bateria = {}
    for linha in saida.splitlines():
        if ":" in linha:
            partes = linha.split(":", 1)
            chave = partes[0].strip().lower()
            valor = partes[1].strip()
            info_bateria[chave] = valor
    
    # Exibir informações
    campos_importantes = ["level", "status", "health", "temperature", "voltage", "technology"]
    for campo in campos_importantes:
        if campo in info_bateria:
            print(f"  {campo.title()}: {info_bateria[campo]}")
    
    # Análise de saúde
    print("\n--- Análise ---")
    try:
        temp = int(info_bateria.get("temperature", "0")) / 10
        level = int(info_bateria.get("level", "100"))
        
        if temp > 45:
            print("  ⚠️  Temperatura alta - pode causar degradação")
        elif temp < 10:
            print("  ⚠️  Temperatura baixa - performance reduzida")
        else:
            print("  ✅ Temperatura normal")
        
        if level < 20:
            print("  ⚠️  Bateria baixa - recarregue em breve")
        elif level > 80:
            print("  ✅ Bateria boa")
    except:
        print("  Não foi possível analisar saúde")
    
    print()


def gerar_relatorio():
    """Gera relatório completo de manutenção."""
    print("=== GERAÇÃO DE RELATÓRIO ===\n")
    
    relatorio = {
        "data": time.strftime("%Y-%m-%d %H:%M:%S"),
        "dispositivo": obter_info_dispositivo(),
        "status": {},
        "recomendacoes": []
    }
    
    # Verificar status
    saida, _ = run_adb("shell dumpsys battery")
    for linha in saida.splitlines():
        if "level" in linha.lower():
            try:
                nivel = int(linha.split(":")[1].strip())
                relatorio["status"]["bateria"] = nivel
                if nivel < 20:
                    relatorio["recomendacoes"].append("Bateria baixa - recarregue")
            except:
                pass
    
    # Verificar armazenamento
    saida, _ = run_adb("shell df -h /data")
    for linha in saida.splitlines():
        if "/data" in linha:
            partes = linha.split()
            if len(partes) >= 4:
                try:
                    usado = partes[2]
                    total = partes[1]
                    relatorio["status"]["armazenamento"] = f"{usado}/{total}"
                except:
                    pass
    
    # Verificar memória
    saida, _ = run_adb("shell cat /proc/meminfo | grep MemFree")
    if saida:
        try:
            livre = int(saida.split(":")[1].strip().replace("kB", "").strip())
            relatorio["status"]["memoria_livre_kb"] = livre
            if livre < 100000:  # Menos de 100MB livre
                relatorio["recomendacoes"].append("Memória baixa - feche apps em segundo plano")
        except:
            pass
    
    # Salvar relatório
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(relatorio, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Relatório salvo em: {REPORT_FILE}")
    print(f"\n--- Resumo ---")
    print(f"  Bateria: {relatorio['status'].get('bateria', 'N/A')}%")
    print(f"  Armazenamento: {relatorio['status'].get('armazenamento', 'N/A')}")
    print(f"  Recomendações: {len(relatorio['recomendacoes'])}")
    
    for rec in relatorio["recomendacoes"]:
        print(f"    - {rec}")
    
    print()


def manutencao_completa():
    """Executa manutenção completa do dispositivo."""
    print("╔══════════════════════════════════════════╗")
    print("║   MANUTENÇÃO COMPLETA ANDROID             ║")
    print("╚══════════════════════════════════════════╝\n")
    
    # Verificar conexão
    conectado, info = verificar_conexao()
    if not conectado:
        print(f"❌ {info}")
        print("Verifique se o dispositivo está conectado e USB Debugging ativo.")
        return
    
    print(f"✅ Dispositivo conectado: {info}\n")
    
    # Executar manutenções
    otimizar_dispositivo()
    verificar_atualizacoes()
    verificar_saude_bateria()
    criar_backup_config()
    gerar_relatorio()
    
    print("╔══════════════════════════════════════════╗")
    print("║   MANUTENÇÃO CONCLUÍDA                    ║")
    print("╚══════════════════════════════════════════╝")
    
    log("Manutenção completa executada")


def main():
    if len(sys.argv) > 1:
        opcao = sys.argv[1]
        if opcao == "--otimizar":
            otimizar_dispositivo()
        elif opcao == "--atualizar":
            verificar_atualizacoes()
        elif opcao == "--backup":
            criar_backup_config()
        elif opcao == "--saude":
            verificar_saude_bateria()
        elif opcao == "--relatorio":
            gerar_relatorio()
        else:
            print("Opções válidas:")
            print("  --otimizar     Otimizar performance")
            print("  --atualizar    Verificar atualizações")
            print("  --backup       Criar backup de configurações")
            print("  --saude        Verificar saúde da bateria")
            print("  --relatorio    Gerar relatório completo")
    else:
        manutencao_completa()


if __name__ == "__main__":
    main()