Script QWEN FLUTTER v1


#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path

def create_file_if_not_exists(filepath: str, content: str):
    """Cria um arquivo com o conteúdo especificado, se ele ainda não existir."""
    path = Path(filepath)
    if path.exists():
        print(f"⚠️  Arquivo {filepath} já existe. Pulando criação.")
    else:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content.strip())
        print(f"✅ Arquivo criado: {filepath}")

def append_to_file(filepath: str, line_to_append: str):
    """Acrescenta uma linha ao final de um arquivo."""
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write("\n" + line_to_append)
    print(f"✅ Linha adicionada ao arquivo: {filepath}")

def run_command(cmd: list, desc: str):
    """Executa um comando shell e verifica se foi bem-sucedido."""
    print(f"\n🔧 Executando: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {desc}")
        if result.stdout:
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar '{' '.join(cmd)}': {e.stderr}")
        sys.exit(1)

def main():
    repo_root = Path.cwd()
    print(f"📁 Diretório atual: {repo_root}")
    
    # Garantir que estamos na branch main
    print("\n--- Verificando Branch Atual ---")
    run_command(["git", "checkout", "main"], "Trocando para a branch 'main'")
    
    # --- PASSO 1: Criar arquivos ---
    print("\n--- Criando arquivos ---")

    create_file_if_not_exists(".env.example", """
# Chaves de API para Modelos de IA (Opcional, o sistema usa fallback para KB local se ausente)
OPENAI_API_KEY=sua_chave_aqui
ANTHROPIC_API_KEY=sua_chave_aqui
GOOGLE_API_KEY=sua_chave_aqui

# Configurações do Orquestrador
MAX_RETRIES=3
ENABLE_PARALLEL_BUILD=false
MAX_WORKERS=4
LOG_LEVEL=INFO
""".strip())

    create_file_if_not_exists("Dockerfile", """
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# 1. Instalar dependências do sistema (JDK 17, Python 3.11, ferramentas de build)
RUN apt-get update && apt-get install -y \\
    curl \\
    git \\
    unzip \\
    xz-utils \\
    zip \\
    libglu1-mesa \\
    openjdk-17-jdk \\
    python3.11 \\
    python3-pip \\
    python3.11-venv \\
    && rm -rf /var/lib/apt/lists/*

# 2. Instalar Flutter SDK
ENV FLUTTER_HOME=/opt/flutter
ENV PATH="${FLUTTER_HOME}/bin:${PATH}"
RUN git clone https://github.com/flutter/flutter.git -b stable ${FLUTTER_HOME} \\
    && flutter doctor \\
    && flutter precache

# 3. Configurar ambiente Python do projeto
WORKDIR /app
COPY requirements.txt .
RUN python3.11 -m pip install --upgrade pip && \\
    python3.11 -m pip install -r requirements.txt

# 4. Copiar código fonte
COPY . .

# 5. Comando padrão (pode ser sobrescrito pelo docker-compose)
CMD ["python3.11", "run_orchestrator.py", "--help"]
""".strip())

    create_file_if_not_exists("docker-compose.yml", """
version: '3.8'
services:
  orchestrator:
    build: .
    volumes:
      - .:/app
      - flutter_cache:/opt/flutter/.pub-cache # Cache de dependências do Flutter para builds mais rápidas
    env_file:
      - .env
    environment:
      - PYTHONUNBUFFERED=1
    command: python3.11 run_orchestrator.py --project /app/meu_projeto_flutter

volumes:
  flutter_cache:
""".strip())

    create_file_if_not_exists(".dockerignore", """
.git
__pycache__
*.pyc
.env
.venv
build/
dist/
*.apk
*.ipa
.DS_Store
""".strip())

    # Pasta e arquivos específicos do orquestrador
    os.makedirs("orchestrator", exist_ok=True)

    create_file_if_not_exists("orchestrator/parallel_builder.py", """
import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

# Ajuste a importação abaixo conforme o nome exato da sua classe principal
from orchestrator.main_orchestrator import FlutterBuildOrchestrator 

logger = logging.getLogger(__name__)

def build_single_project(project_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
    \"\"\"Executa o build de um único projeto e retorna o resultado padronizado.\"\"\"
    try:
        logger.info(f\"🚀 Iniciando build em: {project_path}\")
        orchestrator = FlutterBuildOrchestrator(project_path, config)
        result = orchestrator.run()
        return {
            \"project\": project_path,
            \"status\": \"success\" if result.get(\"success\") else \"failed\",
            \"details\": result
        }
    except Exception as e:
        logger.error(f\"❌ Erro crítico ao construir {project_path}: {str(e)}\")
        return {
            \"project\": project_path,
            \"status\": \"error\",
            \"details\": {\"error\": str(e)}
        }

def run_parallel_builds(project_paths: List[str], config: Dict[str, Any], max_workers: int = 4) -> List[Dict[str, Any]]:
    \"\"\"Orquestra builds em paralelo usando ThreadPoolExecutor (ideal para I/O e subprocessos).\"\"\"
    results = []
    logger.info(f\"⚡ Iniciando build paralelo para {len(project_paths)} projetos com {max_workers} workers.\")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_project = {
            executor.submit(build_single_project, path, config): path 
            for path in project_paths
        }
        
        for future in as_completed(future_to_project):
            project = future_to_project[future]
            try:
                result = future.result()
                results.append(result)
                status_icon = \"✅\" if result[\"status\"] == \"success\" else \"❌\"
                logger.info(f\"{status_icon} Build concluído para: {project} ({result['status']})\")
            except Exception as exc:
                logger.error(f\"💥 Projeto {project} gerou uma exceção não tratada: {exc}\")
                results.append({\"project\": project, \"status\": \"error\", \"details\": {\"error\": str(exc)}})
                
    return results
""".strip())

    create_file_if_not_exists("orchestrator/ios_builder.py", """
import os
import subprocess
import logging
import platform
from typing import Dict, Any

logger = logging.getLogger(__name__)

class IOSBuildOrchestrator:
    def __init__(self, project_path: str, config: Dict[str, Any]):
        self.project_path = os.path.abspath(project_path)
        self.config = config
        self.ios_path = os.path.join(self.project_path, \"ios\")
        self.is_macos = platform.system() == \"Darwin\"

    def check_prerequisites(self) -> bool:
        \"\"\"Verifica se as ferramentas nativas da Apple estão presentes.\"\"\"
        if not self.is_macos:
            logger.error(\"❌ Build iOS só é suportado em ambiente macOS (Darwin).\")
            return False
            
        try:
            subprocess.run([\"xcodebuild\", \"-version\"], check=True, capture_output=True)
            logger.info(\"✅ Xcode detectado e configurado.\")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error(\"❌ Xcode não encontrado. Execute 'xcode-select --install' ou abra o Xcode.\")
            return False

    def install_pods(self) -> bool:
        \"\"\"Garante que as dependências nativas do iOS estejam instaladas.\"\"\"
        try:
            logger.info(\"📦 Instalando CocoaPods...\")
            subprocess.run([\"pod\", \"install\"], cwd=self.ios_path, check=True, capture_output=True, text=True)
            logger.info(\"✅ CocoaPods instalados com sucesso.\")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error(f\"❌ Falha ao instalar CocoaPods: {e}\")
            return False

    def build_ipa(self, export_options_path: str = None) -> Dict[str, Any]:
        \"\"\"Executa o pipeline completo de build do arquivo .ipa.\"\"\"
        if not self.check_prerequisites():
            return {\"success\": False, \"error\": \"Pré-requisitos de sistema não atendidos\"}

        self.install_pods()

        try:
            logger.info(\"🛠️ Iniciando build do iOS (Archive & Export)...\")
            
            # Comando padrão do Flutter para gerar IPA
            cmd = [\"flutter\", \"build\", \"ipa\"]
            if export_options_path:
                cmd.extend([\"--export-options-plist\", export_options_path])
            else:
                cmd.append(\"--no-codesign\") # Fallback para testes sem certificado

            result = subprocess.run(
                cmd, 
                cwd=self.project_path, 
                check=True, 
                capture_output=True, 
                text=True
            )
            
            output_dir = os.path.join(self.project_path, \"build/ios/ipa\")
            logger.info(f\"✅ Build iOS (.ipa) concluído com sucesso! Artefatos em: {output_dir}\")
            
            return {
                \"success\": True,
                \"platform\": \"ios\",
                \"output_path\": output_dir,
                \"message\": \"IPA gerado com sucesso\",
                \"logs\": result.stdout
            }
        except subprocess.CalledProcessError as e:
            logger.error(f\"❌ Falha no build iOS. Stderr: {e.stderr}\")
            return {\"success\": False, \"platform\": \"ios\", \"error\": e.stderr}
        except Exception as e:
            logger.error(f\"❌ Erro inesperado no build iOS: {str(e)}\")
            return {\"success\": False, \"platform\": \"ios\", \"error\": str(e)}
""".strip())

    # --- PASSO 2: Modificar arquivos existentes ---
    print("\n--- Modificando arquivos existentes ---")

    requirements_path = repo_root / "requirements.txt"
    if requirements_path.exists():
        append_to_file("requirements.txt", "python-dotenv>=1.0.0")
    else:
        print("❌ Arquivo requirements.txt não encontrado. Verifique o diretório.")

    run_orchestrator_path = repo_root / "run_orchestrator.py"
    if run_orchestrator_path.exists():
        new_content = '''
import os
import sys
from dotenv import load_dotenv

def setup_environment():
    """Carrega variáveis de ambiente de forma segura a partir de um arquivo .env."""
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print("✅ Variáveis de ambiente carregadas com sucesso a partir de .env")
    else:
        print("⚠️ Arquivo .env não encontrado. Usando variáveis do sistema ou padrões.")

if __name__ == "__main__":
    setup_environment()
    
    # Importação tardia para garantir que o ambiente esteja configurado antes de qualquer lógica
    from orchestrator.main_orchestrator import main as orchestrator_main
    orchestrator_main()
'''
        with open(run_orchestrator_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("✅ Arquivo run_orchestrator.py atualizado com carregamento de .env.")
    else:
        print("⚠️ Arquivo run_orchestrator.py não encontrado. Atualize manualmente.")

    # --- PASSO 3: Executar comandos do Git ---
    print("\n--- Executando comandos do Git ---")
    run_command(["git", "add", "."], "Adicionando todos os arquivos modificados e novos ao staging")
    run_command(["git", "commit", "-m", "feat: adiciona containerização, gestão de segredos, concorrência e base para build iOS"], "Realizando commit das alterações na branch 'main'")
    run_command(["git", "pull", "origin", "main", "--rebase"], "Puxando últimas alterações remotas para evitar conflitos")
    run_command(["git", "push", "origin", "main"], "Enviando alterações diretamente para a branch 'main' no GitHub")

    print("\n🎉 Sucesso! As melhorias foram aplicadas e enviadas diretamente para a branch 'main'.")

if __name__ == "__main__":
    main()
