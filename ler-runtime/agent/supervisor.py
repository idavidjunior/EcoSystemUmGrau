import json
import os
import traceback
from datetime import datetime


class Supervisor:
    def __init__(self, session, config, modules=None):
        self.session = session
        self.config = config
        self.modules = modules or {}
        self.module_states = {}
        self.health_history = []

    def register_module(self, name, module_instance):
        self.modules[name] = module_instance
        self.module_states[name] = {
            "status": "unknown",
            "last_check": None,
            "failures": 0,
            "restarts": 0,
        }

    def monitor_all(self):
        self.session.log("[Supervisor] Monitoring all modules...")
        results = {}
        for name, module in self.modules.items():
            results[name] = self._check_module(name, module)
        return results

    def _check_module(self, name, module):
        state = self.module_states.get(name, {"status": "unknown", "failures": 0, "restarts": 0})
        try:
            if hasattr(module, "get_statistics") and callable(getattr(module, "get_statistics")):
                stats = module.get_statistics()
                state["status"] = "healthy" if isinstance(stats, dict) else "degraded"
            elif hasattr(module, "session"):
                state["status"] = "healthy"
            else:
                state["status"] = "healthy"
            state["failures"] = 0
        except Exception as e:
            state["status"] = "failed"
            state["failures"] += 1
            state["last_error"] = str(e)
            self.session.log(f"[Supervisor] Module '{name}' FAILED: {e}", level="WARNING")

        state["last_check"] = datetime.now().isoformat()
        self.module_states[name] = state
        return state

    def get_unhealthy_modules(self):
        return {n: s for n, s in self.module_states.items()
                if s.get("status") in ("failed", "degraded")}

    def recover_module(self, name):
        if name not in self.modules:
            return {"success": False, "reason": f"Module '{name}' not registered"}
        state = self.module_states.get(name, {})
        state["restarts"] = state.get("restarts", 0) + 1

        max_restarts = self.config.get("supervisor", {}).get("max_module_restarts", 3)
        if state["restarts"] > max_restarts:
            return {"success": False, "reason": f"Max restarts ({max_restarts}) exceeded for '{name}'"}

        self.session.log(f"[Supervisor] Restarting module '{name}' (attempt {state['restarts']})")
        module = self.modules[name]

        try:
            if hasattr(module, "initialize") and callable(getattr(module, "initialize")):
                module.initialize()
            state["status"] = "recovered"
            self.session.log(f"[Supervisor] Module '{name}' recovered successfully")
            return {"success": True, "action": "restarted"}
        except Exception as e:
            state["status"] = "failed"
            state["last_error"] = str(e)
            return {"success": False, "reason": str(e)}

    def get_health_report(self):
        total = len(self.modules)
        healthy = sum(1 for s in self.module_states.values()
                      if s.get("status") in ("healthy", "recovered", "unknown"))
        failed = sum(1 for s in self.module_states.values()
                     if s.get("status") == "failed")
        return {
            "total_modules": total,
            "healthy": healthy,
            "failed": failed,
            "degraded": total - healthy - failed,
            "modules": dict(self.module_states),
            "inspected_at": datetime.now().isoformat(),
        }

    def supervise_operation(self, operation_name, operation_fn, *args, **kwargs):
        try:
            result = operation_fn(*args, **kwargs)
            return {"success": True, "result": result}
        except Exception as e:
            self.session.log(f"[Supervisor] Operation '{operation_name}' failed: {e}", level="WARNING")
            return {"success": False, "error": str(e), "traceback": traceback.format_exc()}
