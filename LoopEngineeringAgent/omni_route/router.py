import json
import os
import subprocess

class OmniRoute:
    def __init__(self, config_dir):
        self.config_dir = config_dir
        self.routes_file = os.path.join(config_dir, "routes.json")
        self.config_file = os.path.join(config_dir, "config.json")
        self.routes = self._load_routes()
        self.config = self._load_config()
        self.providers = {}
        self._init_providers()

    def _load_routes(self):
        if os.path.exists(self.routes_file):
            with open(self.routes_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"routes": [], "routing_strategy": "priority", "failover": True}

    def _load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _init_providers(self):
        self.providers = {
            "opencode": OpenCodeProvider(self),
            "shell": ShellProvider(self),
            "nvidia_build": NVIDIAProvider(self),
            "openai": OpenAIProvider(self),
        }

    def route(self, request):
        strategy = self.routes.get("routing_strategy", "priority")
        routes = sorted(
            [r for r in self.routes.get("routes", []) if r.get("enabled", False)],
            key=lambda r: r.get("priority", 999)
        )

        if strategy == "priority":
            return self._route_by_priority(request, routes)
        return self._route_by_priority(request, routes)

    def _route_by_priority(self, request, routes):
        errors = []
        for route in routes:
            name = route["name"]
            provider = self.providers.get(name)
            if not provider:
                continue
            try:
                result = provider.execute(request)
                if result.get("status") == "success":
                    return result
                errors.append({"provider": name, "error": result.get("error")})
            except Exception as e:
                errors.append({"provider": name, "error": str(e)})

            if not self.routes.get("failover", True):
                break

        return {"status": "error", "errors": errors, "message": "All providers failed"}

    def execute(self, request):
        return self.route(request)

class OpenCodeProvider:
    def __init__(self, router):
        self.router = router

    def execute(self, request):
        action = request.get("action", "")
        target = request.get("target", "")
        if action == "command":
            return self._run_command(target)
        return {"status": "error", "error": f"Unknown action: {action}"}

    def _run_command(self, command):
        try:
            proc = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            return {
                "status": "success",
                "provider": "opencode",
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "exit_code": proc.returncode
            }
        except subprocess.TimeoutExpired:
            return {"status": "error", "provider": "opencode", "error": "timeout"}
        except Exception as e:
            return {"status": "error", "provider": "opencode", "error": str(e)}

class ShellProvider:
    def __init__(self, router):
        self.router = router

    def execute(self, request):
        action = request.get("action", "")
        target = request.get("target", "")
        if action == "command":
            return self._run(target)
        return {"status": "error", "error": f"Unknown action: {action}"}

    def _run(self, command):
        try:
            proc = subprocess.run(
                ["powershell", "-Command", command],
                capture_output=True,
                text=True,
                timeout=120
            )
            return {
                "status": "success",
                "provider": "shell",
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "exit_code": proc.returncode
            }
        except Exception as e:
            return {"status": "error", "provider": "shell", "error": str(e)}

class NVIDIAProvider:
    def __init__(self, router):
        self.router = router

    def execute(self, request):
        api_key = os.environ.get("NVIDIA_API_KEY")
        if not api_key:
            return {"status": "error", "provider": "nvidia_build", "error": "NVIDIA_API_KEY not configured"}
        return {"status": "error", "provider": "nvidia_build", "error": "NVIDIA API not yet integrated"}

class OpenAIProvider:
    def __init__(self, router):
        self.router = router

    def execute(self, request):
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return {"status": "error", "provider": "openai", "error": "OPENAI_API_KEY not configured"}
        return {"status": "error", "provider": "openai", "error": "OpenAI API not yet integrated"}
