import psutil
import threading
import time
from utils import timestamp, HISTORY_LEN

CPU_HIGH = 75.0
MEM_HIGH = 80.0
CPU_LOW  = 40.0
MEM_LOW  = 50.0

class AdaptiveAllocator:
    def __init__(self, monitor, log_cb, interval=3.0):
        self.monitor   = monitor
        self.log_cb    = log_cb
        self.interval  = interval
        self._running  = False
        self._thread   = None
        self._lock     = threading.Lock()
        self.decisions     = []
        self.alloc_history = []

    def start(self):
        self._running = True
        self._thread  = threading.Thread(
            target=self._loop, daemon=True, name="allocator")
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            self._cycle()
            time.sleep(self.interval)

    def _cycle(self):
        snap  = self.monitor.snapshot()
        cpu   = snap["cpu"]
        mem   = snap["mem"]
        procs = snap["processes"]
        made  = []

        if cpu > CPU_HIGH:
            top = [p for p in procs if p["cpu"] > 5.0][:3]
            for p in top:
                m = self._renice(p["pid"], p["name"], 5,
                    f"CPU={cpu:.0f}% → demote PID {p['pid']} ({p['name']})")
                if m: made.append(m)
            self.log_cb(
                f"CPU bottleneck {cpu:.0f}% — throttling {len(top)} process(es)", "ALLOC")

        elif mem > MEM_HIGH:
            hungry = [p for p in procs if p["mem"] > 1.0][:2]
            for p in hungry:
                m = self._renice(p["pid"], p["name"], 5,
                    f"MEM={mem:.0f}% → deprioritise PID {p['pid']} ({p['name']})")
                if m: made.append(m)
            self.log_cb(
                f"Memory pressure {mem:.0f}% — deprioritising consumers", "ALLOC")

        elif cpu < CPU_LOW and mem < MEM_LOW:
            demoted = [p for p in procs if (p.get("nice") or 0) > 0][:3]
            for p in demoted:
                m = self._renice(p["pid"], p["name"], 0,
                    f"Load normal → restore PID {p['pid']} ({p['name']})")
                if m: made.append(m)
            if demoted:
                self.log_cb("Load normalised — restoring priorities", "ALLOC")

        score = max(0.0, min(100.0,
                    100 - abs(cpu - 45) - abs(mem - 45) * 0.5))

        with self._lock:
            self.alloc_history.append(score)
            if len(self.alloc_history) > HISTORY_LEN:
                self.alloc_history = self.alloc_history[-HISTORY_LEN:]
            if made:
                ts = timestamp()
                for d in made:
                    self.decisions.append((ts, d))
                if len(self.decisions) > 300:
                    self.decisions = self.decisions[-300:]

    def _renice(self, pid, name, nice_val, reason):
        try:
            proc = psutil.Process(pid)
            if proc.nice() == nice_val:
                return None
            proc.nice(nice_val)
            return reason
        except Exception:
            return None

    def get_alloc_history(self):
        with self._lock:
            return list(self.alloc_history)

    def get_decisions(self):
        with self._lock:
            return list(self.decisions)
