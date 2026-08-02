#!/usr/bin/env python3
"""
nvidia_quota_monitor.py — Monitor local de cotas NVIDIA NIM
Token Bucket (40 RPM account-wide) + Concurrency Cap (5 in-flight)
Classificação de erro: 429 = rate limit | 502/503/504 = saturação
"""
import threading, time, json, os, requests
from pathlib import Path
from collections import deque
from dataclasses import dataclass, asdict
from typing import Optional

STATE_FILE = Path(__file__).with_name("nvidia_quota_state.json")

@dataclass
class QuotaState:
    rpm_used: int = 0
    last_reset: float = 0.0
    tokens: float = 40.0
    last_429: Optional[str] = None
    fallbacks_triggered: int = 0
    total_requests: int = 0
    total_429: int = 0
    total_5xx: int = 0

class TokenBucket:
    """40 RPM account-wide → 40/60 = 0.667 tokens/sec refill"""
    def __init__(self, capacity=40, refill_rate=40/60):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill = time.time()
        self._lock = threading.Lock()

    def consume(self, n=1, timeout=30) -> bool:
        """Bloqueia até ter tokens ou timeout. Retorna True se consumiu."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self._lock:
                now = time.time()
                elapsed = now - self.last_refill
                self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
                self.last_refill = now
                if self.tokens >= n:
                    self.tokens -= n
                    return True
            time.sleep(0.05)
        return False

    def get_available(self) -> float:
        with self._lock:
            now = time.time()
            elapsed = now - self.last_refill
            return min(self.capacity, self.tokens + elapsed * self.refill_rate)

class ConcurrencyCap:
    """Max 5 in-flight requests simultâneos NVIDIA"""
    def __init__(self, max_concurrent=5):
        self.sem = threading.Semaphore(max_concurrent)
        self.current = 0
        self._lock = threading.Lock()

    def __enter__(self):
        self.sem.acquire()
        with self._lock:
            self.current += 1
        return self

    def __exit__(self, *args):
        with self._lock:
            self.current -= 1
        self.sem.release()

    def get_current(self) -> int:
        with self._lock:
            return self.current

class NVIDIAQuotaMonitor:
    def __init__(self):
        self.bucket = TokenBucket()
        self.cap = ConcurrencyCap()
        self.state = self._load_state()
        self.request_log = deque(maxlen=1000)
        self._lock = threading.Lock()
        self._start_refill_thread()

    def _load_state(self) -> QuotaState:
        if STATE_FILE.exists():
            try:
                data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
                return QuotaState(**data)
            except Exception:
                pass
        return QuotaState(last_reset=time.time())

    def _save_state(self):
        self.state.last_reset = time.time()
        STATE_FILE.write_text(json.dumps(asdict(self.state), indent=2), encoding="utf-8")

    def _start_refill_thread(self):
        def loop():
            while True:
                time.sleep(10)
                self._save_state()
        threading.Thread(target=loop, daemon=True).start()

    def record_request(self, model: str, status: int, latency_ms: int, retry_after: Optional[int]=None):
        now = time.time()
        with self._lock:
            self.state.total_requests += 1
            self.request_log.append({
                "ts": now, "model": model, "status": status,
                "latency_ms": latency_ms, "retry_after": retry_after
            })
            # reset RPM counter a cada minuto
            if now - self.state.last_reset >= 60:
                self.state.rpm_used = 0
                self.state.last_reset = now

            if status == 429:
                self.state.total_429 += 1
                self.state.last_429 = time.strftime("%Y-%m-%dT%H:%M:%S")
                if retry_after:
                    time.sleep(min(retry_after, 60))
            elif 500 <= status < 600:
                self.state.total_5xx += 1

    def record_fallback(self):
        with self._lock:
            self.state.fallbacks_triggered += 1
            self._save_state()

    def get_status(self) -> dict:
        with self._lock:
            return {
                "rpm_used": self.state.rpm_used,
                "rpm_budget": 40,
                "rpm_available": 40 - self.state.rpm_used,
                "tokens_available": round(self.bucket.get_available(), 2),
                "concurrency": self.cap.get_current(),
                "concurrency_max": 5,
                "fallbacks_triggered": self.state.fallbacks_triggered,
                "total_requests": self.state.total_requests,
                "total_429": self.state.total_429,
                "total_5xx": self.state.total_5xx,
                "last_429": self.state.last_429,
                "bucket_refill_rate": round(self.bucket.refill_rate, 3),
            }

    def wait_for_budget(self, timeout=30) -> bool:
        """Bloqueia até ter token no bucket. Para uso antes de cada request NVIDIA."""
        return self.bucket.consume(1, timeout=timeout)

    def classify_error(self, status: int) -> str:
        if status == 429:
            return "rate_limit"
        elif status in (502, 503, 504):
            return "saturation"
        elif status >= 500:
            return "server_error"
        return "unknown"

# Singleton global
_monitor = None
def get_monitor() -> NVIDIAQuotaMonitor:
    global _monitor
    if _monitor is None:
        _monitor = NVIDIAQuotaMonitor()
    return _monitor

# --- Helper para uso no bridge ---
def nvidia_request_with_quota(model: str, messages: list, **kwargs):
    """Wrapper que aplica quota monitor + classificação de erro + fallback trigger."""
    monitor = get_monitor()
    if not monitor.wait_for_budget(timeout=30):
        raise RuntimeError("NVIDIA quota timeout (40 RPM exceeded)")

    with monitor.cap:
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {os.environ['NVIDIA_API_KEY']}",
            "Content-Type": "application/json"
        }
        data = {"model": model, "messages": messages, **kwargs}
        start = time.time()
        try:
            r = requests.post(url, headers=headers, json=data, timeout=kwargs.get("timeout", 30))
            latency = int((time.time() - start) * 1000)
            retry_after = int(r.headers.get("Retry-After", 0)) if r.headers.get("Retry-After") else None
            monitor.record_request(model, r.status_code, latency, retry_after)
            
            error_class = monitor.classify_error(r.status_code)
            if error_class == "rate_limit":
                monitor.record_fallback()
            return r
        except requests.Timeout:
            latency = int((time.time() - start) * 1000)
            monitor.record_request(model, 504, latency)
            monitor.record_fallback()
            raise

# CLI
if __name__ == "__main__":
    import sys
    m = get_monitor()
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        print(json.dumps(m.get_status(), indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "test":
        # Teste rápido
        print("Testando request NVIDIA com quota monitor...")
        try:
            r = nvidia_request_with_quota("meta/llama-3.1-8b-instruct", 
                                          [{"role": "user", "content": "ping"}], max_tokens=5)
            print(f"Status: {r.status_code}, Quota: {m.get_status()}")
        except Exception as e:
            print(f"Erro: {e}, Quota: {m.get_status()}")
    else:
        print(json.dumps(m.get_status(), indent=2))