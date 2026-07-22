import json
import os
from datetime import datetime


class LearningEngine:
    def __init__(self, session, base_dir):
        self.session = session
        self.base_dir = base_dir
        self.memory_dir = os.path.join(base_dir, "memory")
        self.learned_file = os.path.join(self.memory_dir, "learned_rules.json")
        self.success_file = os.path.join(self.memory_dir, "successful_patterns.json")
        self.failed_file = os.path.join(self.memory_dir, "failed_patterns.json")

    def initialize(self):
        os.makedirs(self.memory_dir, exist_ok=True)
        for path in [self.learned_file, self.success_file, self.failed_file]:
            if not os.path.exists(path):
                with open(path, "w", encoding="utf-8") as f:
                    json.dump({"rules": []} if "rules" in path else {"patterns": []}, f, indent=2)

    def learn_from_error(self, error, context, step_info=None):
        self._ensure_initialized()
        rules = self._load_json(self.learned_file)
        failed = self._load_json(self.failed_file)

        error_key = self._normalize_error(error)

        existing = [r for r in rules.get("rules", []) if r.get("error_key") == error_key]
        if existing:
            existing[0]["count"] += 1
            existing[0]["last_seen"] = datetime.now().isoformat()
        else:
            rule = {
                "error_key": error_key,
                "error_message": error[:200],
                "context": context[:100] if context else "",
                "step": step_info.get("action") if step_info else "",
                "count": 1,
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
                "suggested_fix": self._suggest_fix(error_key),
                "applied_successfully": False,
            }
            rules["rules"].append(rule)

        pattern = {
            "error": error[:200],
            "context": context[:200] if context else "",
            "timestamp": datetime.now().isoformat(),
            "step": step_info,
        }
        failed["patterns"].append(pattern)

        self._save_json(self.learned_file, rules)
        self._save_json(self.failed_file, failed)

        return rules

    def learn_from_success(self, step_info, result):
        self._ensure_initialized()
        success = self._load_json(self.success_file)
        pattern = {
            "action": step_info.get("action") if step_info else "",
            "description": step_info.get("description", "")[:100] if step_info else "",
            "validation": step_info.get("validation", "") if step_info else "",
            "duration": result.get("duration", 0),
            "timestamp": datetime.now().isoformat(),
        }
        success["patterns"].append(pattern)
        self._save_json(self.success_file, success)

    def get_relevant_rules(self, error_message):
        self._ensure_initialized()
        rules = self._load_json(self.learned_file)
        error_lower = error_message.lower()
        relevant = []
        for rule in rules.get("rules", []):
            if rule.get("applied_successfully", False):
                if rule.get("error_key", "") in error_lower:
                    relevant.append(rule)
                elif any(w in error_lower for w in rule.get("error_key", "").split("_")):
                    relevant.append(rule)
        return relevant

    def mark_rule_applied(self, error_key):
        rules = self._load_json(self.learned_file)
        for rule in rules.get("rules", []):
            if rule.get("error_key") == error_key:
                rule["applied_successfully"] = True
                break
        self._save_json(self.learned_file, rules)

    def get_statistics(self):
        self._ensure_initialized()
        rules = self._load_json(self.learned_file)
        success = self._load_json(self.success_file)
        failed = self._load_json(self.failed_file)
        return {
            "total_learned_rules": len(rules.get("rules", [])),
            "total_successes": len(success.get("patterns", [])),
            "total_failures": len(failed.get("patterns", [])),
            "success_rate": self._calculate_success_rate(success, failed),
        }

    def _normalize_error(self, error):
        error = error.lower().strip()
        error = error.split("\n")[0] if "\n" in error else error
        error = error[:60]
        error = error.replace(" ", "_").replace("'", "").replace('"', "")
        return error

    def _suggest_fix(self, error_key):
        suggestions = {
            "not_found": "Verificar se o caminho/arquivo existe. Usar caminho absoluto.",
            "timeout": "Aumentar timeout ou dividir operacao em partes menores.",
            "permission": "Verificar permissoes de leitura/escrita. Executar como administrador.",
            "syntax": "Verificar sintaxe do comando/arquivo. Validar antes de executar.",
            "compile": "Verificar versao do compilador. Corrigir erros de sintaxe no codigo.",
            "connection": "Verificar conectividade de rede. Tentar novamente.",
            "json": "Verificar formato do JSON. Validar com ferramenta apropriada.",
        }
        for key, suggestion in suggestions.items():
            if key in error_key:
                return suggestion
        return "Analisar erro manualmente e ajustar abordagem."

    def _ensure_initialized(self):
        if not os.path.exists(self.learned_file):
            self.initialize()
        os.makedirs(self.memory_dir, exist_ok=True)

    def _load_json(self, path):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"rules": []}

    def _save_json(self, path, data):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _calculate_success_rate(self, success, failed):
        s = len(success.get("patterns", []))
        f = len(failed.get("patterns", []))
        total = s + f
        if total == 0:
            return 0
        return round((s / total) * 100, 1)
