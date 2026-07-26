import json
import os
import subprocess
from datetime import datetime


class VaultBridge:
    def __init__(self, session, base_dir):
        self.session = session
        self.base_dir = base_dir
        self.vault_path = os.environ.get(
            "OBSIDIAN_VAULT_PATH",
            "C:\\Users\\Playtec-bancada\\Desktop\\Codigos"
        )
        self.mcp_available = False
        self._check_mcp()

    def _check_mcp(self):
        try:
            result = subprocess.run(
                ["cmd", "/c", "echo {} | npx @bitbonsai/mcpvault \""
                 + self.vault_path + "\" 2>nul"],
                capture_output=True, text=True, timeout=10
            )
            self.mcp_available = "\"tools\"" in result.stdout
        except Exception:
            self.mcp_available = False

    def _mcp_call(self, json_payload):
        if not self.mcp_available:
            return None
        try:
            temp_file = os.path.join(os.environ.get("TEMP", "."), "mcp_call.tmp")
            with open(temp_file, "w", encoding="ascii") as f:
                f.write(json_payload)
            cmd = f'type "{temp_file}" | npx @bitbonsai/mcpvault "{self.vault_path}"'
            result = subprocess.run(
                ["cmd", "/c", cmd], capture_output=True, text=True, timeout=15
            )
            return result.stdout
        except Exception as e:
            self.session.log(f"[VaultBridge] mcp_call error: {e}")
            return None

    def write_note(self, path, content, frontmatter=None):
        if not self.mcp_available:
            self.session.log("[VaultBridge] MCPVault not available, writing to local file")
            return self._write_local(path, content)
        try:
            payload = json.dumps({
                "jsonrpc": "2.0", "id": 1, "method": "tools/call",
                "params": {
                    "name": "write_note",
                    "arguments": {"path": path, "content": content, "mode": "overwrite"}
                }
            })
            result = self._mcp_call(payload)
            return result is not None
        except Exception as e:
            self.session.log(f"[VaultBridge] write_note error: {e}")
            return self._write_local(path, content)

    def _write_local(self, path, content):
        full_path = os.path.join(self.vault_path, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True

    def search_notes(self, query):
        if not self.mcp_available:
            self.session.log("[VaultBridge] MCPVault not available for search")
            return []
        try:
            payload = json.dumps({
                "jsonrpc": "2.0", "id": 1, "method": "tools/call",
                "params": {
                    "name": "search_notes",
                    "arguments": {"query": query, "limit": 10}
                }
            })
            return self._mcp_call(payload)
        except Exception as e:
            self.session.log(f"[VaultBridge] search error: {e}")
            return []

    def sync_learned_rules(self, rules_file):
        if not os.path.exists(rules_file):
            return
        try:
            with open(rules_file, "r", encoding="utf-8") as f:
                rules = json.load(f)
            content = "# Regras Aprendidas\n\n"
            content += f"_Ultima sincronizacao: {datetime.now().isoformat()}_\n\n"
            for rule in rules:
                content += f"- **{rule.get('pattern', 'Regra')}**\n"
                if "error" in rule:
                    content += f"  - Erro: `{rule['error']}`\n"
                if "fix" in rule:
                    content += f"  - Correcao: {rule['fix']}\n"
                content += "\n"
            self._write_local("LER/RegrasAprendidas.md", content)
            self.session.log(f"[VaultBridge] Synced {len(rules)} rules to vault")
        except Exception as e:
            self.session.log(f"[VaultBridge] sync_rules error: {e}")

    def sync_successful_patterns(self, patterns_file):
        if not os.path.exists(patterns_file):
            return
        try:
            with open(patterns_file, "r", encoding="utf-8") as f:
                patterns = json.load(f)
            content = "# Padroes de Sucesso\n\n"
            content += f"_Ultima sincronizacao: {datetime.now().isoformat()}_\n\n"
            for p in patterns:
                content += f"- {p.get('pattern', 'Padrao')}\n"
                if "context" in p:
                    content += f"  - Contexto: {p['context']}\n"
                content += "\n"
            self._write_local("LER/PadroesDeSucesso.md", content)
            self.session.log(f"[VaultBridge] Synced {len(patterns)} patterns to vault")
        except Exception as e:
            self.session.log(f"[VaultBridge] sync_patterns error: {e}")

    def get_vault_stats(self):
        if not self.mcp_available:
            return {"available": False}
        try:
            payload = json.dumps({
                "jsonrpc": "2.0", "id": 1, "method": "tools/call",
                "params": {"name": "get_vault_stats", "arguments": {"recentCount": 5}}
            })
            result = self._mcp_call(payload)
            return json.loads(result) if result else {"available": True}
        except Exception:
            return {"available": True}
