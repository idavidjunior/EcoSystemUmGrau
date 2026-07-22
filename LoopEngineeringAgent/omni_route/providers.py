import json
import os
import subprocess
import urllib.request
import urllib.parse

class BaseProvider:
    def __init__(self, name, config):
        self.name = name
        self.config = config

    def execute(self, request):
        raise NotImplementedError

class OpenCodeProvider(BaseProvider):
    def __init__(self, config):
        super().__init__("opencode", config)

    def execute(self, request):
        command = request.get("command", "")
        if not command:
            return {"status": "error", "error": "No command provided"}
        try:
            proc = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=int(self.config.get("timeout_seconds", 60))
            )
            return {
                "status": "success",
                "provider": self.name,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "exit_code": proc.returncode
            }
        except subprocess.TimeoutExpired:
            return {"status": "error", "provider": self.name, "error": "timeout"}
        except Exception as e:
            return {"status": "error", "provider": self.name, "error": str(e)}

class ShellProvider(BaseProvider):
    def __init__(self, config):
        super().__init__("shell", config)

    def execute(self, request):
        command = request.get("command", "")
        shell = request.get("shell", "powershell")
        if not command:
            return {"status": "error", "error": "No command provided"}
        try:
            if shell == "powershell":
                args = ["powershell", "-NoProfile", "-Command", command]
            else:
                args = ["cmd", "/c", command]
            proc = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=int(self.config.get("timeout_seconds", 120))
            )
            return {
                "status": "success",
                "provider": self.name,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "exit_code": proc.returncode
            }
        except Exception as e:
            return {"status": "error", "provider": self.name, "error": str(e)}

class APIProvider(BaseProvider):
    def __init__(self, name, config, api_key_env):
        super().__init__(name, config)
        self.api_key_env = api_key_env
        self.api_key = os.environ.get(api_key_env)

    def _make_request(self, url, data, headers):
        if not self.api_key:
            return {"status": "error", "error": f"{self.api_key_env} not set"}
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                return {"status": "success", "data": json.loads(resp.read().decode("utf-8"))}
        except Exception as e:
            return {"status": "error", "error": str(e)}
