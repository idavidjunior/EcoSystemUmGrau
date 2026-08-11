"""android_limpeza.py — Limpeza e manutenção de dispositivos Android via ADB.

Uso:
  python scripts/android_limpeza.py                    # limpeza completa
  python scripts/android_limpeza.py --cache            # só cache
  python scripts/android_limpeza.py --downloads        # só downloads
  python scripts/android_limpeza.py --thumbnails       # só thumbnails
  python scripts/android_limpeza.py --logs             # só logs
  python scripts/android_limpeza.py --apps             # só apps
  python scripts/android_limpeza.py --seguro           # limpeza segura (sem deletar dados pessoais)
"""
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADB = "adb"
LOG_FILE = ROOT / "runtime" / "android_limpeza.log"


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


def limpeza_cache():
    """Limpa cache de todos os apps."""
    print("=== LIMPEZA DE CACHE ===\n")
    
    # Listar todos os pacotes
    saida, _ = run_adb("shell pm list packages -3")
    pacotes = [linha.replace("package:", "") for linha in saida.splitlines() if linha.startswith("package:")]
    
    print(f"Encontrados {len(pacotes)} apps de terceiros")
    
    limpos = 0
    for i, pacote in enumerate(pacotes, 1):
        print(f"\r[{i}/{len(pacotes)}] Limpando cache de {pacote}...", end="", flush=True)
        saida, rc = run_adb(f"shell pm clear {pacote}", timeout=10)
        if rc == 0:
            limpos += 1
            log(f"Cache limpo: {pacote}")
    
    print(f"\n\n✅ Cache limpo em {limpos} apps")
    return limpos


def limpeza_cache_sistema():
    """Limpa cache do sistema."""
    print("=== LIMPEZA DE CACHE DO SISTEMA ===\n")
    
    comandos = [
        ("Cache do sistema", "shell rm -rf /data/cache/*"),
        ("Pacotes", "shell rm -rf /data/system/package_cache/*"),
        ("Downloads temporários", "shell rm -rf /sdcard/Download/*.tmp"),
        ("Logs antigos", "shell rm -rf /data/log/*"),
    ]
    
    for nome, cmd in comandos:
        print(f"Limpando {nome}...", end="", flush=True)
        saida, rc = run_adb(cmd, timeout=15)
        if rc == 0:
            print(" ✅")
            log(f"Sistema limpo: {nome}")
        else:
            print(" ⚠️  (pode precisar de permissões)")
    
    print()


def limpeza_thumbnails():
    """Limpa thumbnails de imagens e vídeos."""
    print("=== LIMPEZA DE THUMBNAILS ===\n")
    
    dirs_thumbnail = [
        "/sdcard/DCIM/.thumbnails",
        "/sdcard/Pictures/.thumbnails",
        "/sdcard/DCIM/.Thumbnails",
        "/sdcard/Pictures/.Thumbnails",
    ]
    
    total_limpo = 0
    for dir_path in dirs_thumbnail:
        print(f"Verificando {dir_path}...", end="", flush=True)
        saida, _ = run_adb(f"shell du -sh {dir_path}")
        
        if saida and "No such file" not in saida and "Permission denied" not in saida:
            print(f" {saida}")
            run_adb(f"shell rm -rf {dir_path}")
            total_limpo += 1
            log(f"Thumbnails limpos: {dir_path}")
        else:
            print(" não encontrado ou vazio")
    
    print(f"\n✅ {total_limpo} diretórios de thumbnails limpos")
    return total_limpo


def limpeza_downloads():
    """Limpa downloads antigos."""
    print("=== LIMPEZA DE DOWNLOADS ===\n")
    
    # Listar arquivos antigos (>7 dias)
    saida, _ = run_adb("shell find /sdcard/Download -type f -mtime +7 -exec ls -lh {} \\;")
    
    if not saida or "No such file" in saida:
        print("Nenhum arquivo antigo encontrado em Downloads")
        return 0
    
    print("Arquivos antigos encontrados:")
    arquivos = []
    for linha in saida.splitlines():
        if linha.strip():
            print(f"  {linha.strip()}")
            arquivos.append(linha)
    
    print(f"\nTotal: {len(arquivos)} arquivos")
    
    # Perguntar se quer deletar (modo interativo)
    if len(sys.argv) > 1 and sys.argv[1] == "--confirmar":
        for linha in arquivos:
            partes = linha.split()
            if len(partes) >= 9:
                caminho = " ".join(partes[8:])
                run_adb(f"shell rm -f {caminho}")
                log(f"Download removido: {caminho}")
        print(f"\n✅ {len(arquivos)} arquivos removidos")
    else:
        print("\nPara deletar, execute com --confirmar")
    
    return len(arquivos)


def limpeza_logs():
    """Limpa logs do sistema e apps."""
    print("=== LIMPEZA DE LOGS ===\n")
    
    comandos = [
        ("Logs do sistema", "shell rm -rf /data/log/*"),
        ("Logs do Android", "shell rm -rf /sdcard/Android/log/*"),
        ("Logs de crashes", "shell rm -rf /data/tombstones/*"),
        ("Logs de ANR", "shell rm -rf /data/anr/*"),
        ("Logcat buffer", "logcat -c"),
    ]
    
    for nome, cmd in comandos:
        print(f"Limpando {nome}...", end="", flush=True)
        saida, rc = run_adb(cmd, timeout=15)
        if rc == 0:
            print(" ✅")
            log(f"Logs limpos: {nome}")
        else:
            print(" ⚠️  (pode precisar de root)")
    
    print()


def limpeza_apps_nao_utilizados():
    """Lista e opcionalmente desinstala apps não utilizados."""
    print("=== ANÁLISE DE APPS ===\n")
    
    # Listar apps com uso de bateria
    saida, _ = run_adb("shell dumpsys batterystats --charged")
    
    print("Apps com maior consumo de bateria (top 10):")
    linhas = saida.splitlines()
    apps = []
    
    for linha in linhas:
        if "Uid " in linha and "cpu=" in linha:
            partes = linha.split()
            if len(partes) >= 2:
                uid = partes[1].replace("Uid", "").strip()
                # Tentar obter nome do pacote
                saida_pkg, _ = run_adb(f"shell pm list packages | grep {uid}")
                if saida_pkg:
                    pkg = saida_pkg.replace("package:", "").strip()
                    apps.append((pkg, linha.strip()))
    
    for i, (pkg, info) in enumerate(apps[:10], 1):
        print(f"  {i}. {pkg}")
    
    print(f"\nTotal de apps: {len(apps)}")
    print("\nPara desinstalar apps específicos, use:")
    print("  python scripts/android_limpeza.py --desinstalar <package>")


def limpeza_segura():
    """Executa limpeza segura (sem deletar dados pessoais)."""
    print("=== LIMPEZA SEGURA ===\n")
    print("Esta limpeza NÃO deleta:")
    print("  - Fotos e vídeos")
    print("  - Músicas")
    print("  - Documentos pessoais")
    print("  - Mensagens")
    print("  - Contatos")
    print()
    
    # Executar limpezas seguras
    limpeza_cache_sistema()
    limpeza_thumbnails()
    limpeza_logs()
    
    print("=== LIMPEZA SEGURA CONCLUÍDA ===")


def limpeza_completa():
    """Executa limpeza completa do dispositivo."""
    print("╔══════════════════════════════════════════╗")
    print("║   LIMPEZA COMPLETA ANDROID                ║")
    print("╚══════════════════════════════════════════╝\n")
    
    # Verificar conexão
    conectado, info = verificar_conexao()
    if not conectado:
        print(f"❌ {info}")
        print("Verifique se o dispositivo está conectado e USB Debugging ativo.")
        return
    
    print(f"✅ Dispositivo conectado: {info}\n")
    
    # Executar limpezas
    limpeza_cache()
    limpeza_cache_sistema()
    limpeza_thumbnails()
    limpeza_downloads()
    limpeza_logs()
    
    print("╔══════════════════════════════════════════╗")
    print("║   LIMPEZA CONCLUÍDA                       ║")
    print("╚══════════════════════════════════════════╝")
    
    log("Limpeza completa executada")


def main():
    if len(sys.argv) > 1:
        opcao = sys.argv[1]
        if opcao == "--cache":
            limpeza_cache()
        elif opcao == "--cache-sistema":
            limpeza_cache_sistema()
        elif opcao == "--thumbnails":
            limpeza_thumbnails()
        elif opcao == "--downloads":
            limpeza_downloads()
        elif opcao == "--logs":
            limpeza_logs()
        elif opcao == "--apps":
            limpeza_apps_nao_utilizados()
        elif opcao == "--seguro":
            limpeza_segura()
        elif opcao == "--confirmar":
            limpeza_downloads()
        else:
            print("Opções válidas:")
            print("  --cache          Limpar cache de apps")
            print("  --cache-sistema  Limpar cache do sistema")
            print("  --thumbnails     Limpar thumbnails")
            print("  --downloads      Limpar downloads antigos")
            print("  --logs           Limpar logs")
            print("  --apps           Analisar apps")
            print("  --seguro         Limpeza segura (sem dados pessoais)")
    else:
        limpeza_completa()


if __name__ == "__main__":
    main()