"""
system_monitor.py
=================
Three-thread design for zero lag on Windows & Linux:
  _cpu_thread   — psutil.cpu_percent(interval=0.5) — true blocking sample
  _mem_thread   — memory every 0.5s  (non-blocking, fast)
  _proc_thread  — process list every 2s (expensive, isolated)
"""

import psutil
import threading
import time
from utils import make_deque, HISTORY_LEN

class SystemMonitor:
    def __init__(self):
        self._lock   = threading.Lock()
        self._running = False

        self.cpu_history  = make_deque()
        self.mem_history  = make_deque()
        self.proc_history = make_deque()

        self.cpu_percent   = 0.0
        self.mem_percent   = 0.0
        self.mem_used      = 0
        self.mem_total     = 1
        self.process_count = 0
        self.load_avg      = 0.0
        self.processes     = []

    # ── start ─────────────────────────────────────────────────────────── #
    def start(self):
        self._running = True

        # Prime CPU counter — first call always returns 0, discard it
        psutil.cpu_percent(interval=None)
        time.sleep(0.1)
        psutil.cpu_percent(interval=None)   # second prime

        for t, fn in [
            ("mon-cpu",  self._cpu_loop),
            ("mon-mem",  self._mem_loop),
            ("mon-proc", self._proc_loop),
        ]:
            th = threading.Thread(target=fn, daemon=True, name=t)
            th.start()

    def stop(self):
        self._running = False

    # ── CPU thread: blocks 0.5s per sample → accurate, no lag ─────────── #
    def _cpu_loop(self):
        while self._running:
            cpu = psutil.cpu_percent(interval=0.5)   # blocking, accurate

            # Windows has no getloadavg — simulate with cpu/100
            try:
                load = round(psutil.getloadavg()[0], 2)
            except AttributeError:
                load = round(cpu / 25.0, 2)          # rough Windows equivalent

            with self._lock:
                self.cpu_percent = cpu
                self.load_avg    = load
                self.cpu_history.append(cpu)

    # ── MEM thread: non-blocking, 0.5s interval ────────────────────────── #
    def _mem_loop(self):
        while self._running:
            mem = psutil.virtual_memory()
            with self._lock:
                self.mem_percent = mem.percent
                self.mem_used    = mem.used
                self.mem_total   = mem.total
                self.mem_history.append(mem.percent)
            time.sleep(0.5)

    # ── PROC thread: expensive, runs every 2s ─────────────────────────── #
    def _proc_loop(self):
        while self._running:
            procs = []
            for p in psutil.process_iter(
                    ["pid", "name", "cpu_percent",
                     "memory_percent", "nice", "status"]):
                try:
                    info = p.info
                    procs.append({
                        "pid":    info["pid"],
                        "name":   (info["name"] or "?")[:26],
                        "cpu":    round(info["cpu_percent"] or 0.0, 1),
                        "mem":    round(info["memory_percent"] or 0.0, 2),
                        "nice":   info.get("nice", 0),
                        "status": info.get("status", "?"),
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            procs.sort(key=lambda x: x["cpu"], reverse=True)

            with self._lock:
                self.process_count = len(procs)
                self.processes     = procs[:60]
                self.proc_history.append(len(procs))

            time.sleep(2.0)

    # ── snapshot ──────────────────────────────────────────────────────── #
    def snapshot(self):
        with self._lock:
            return {
                "cpu":       self.cpu_percent,
                "mem":       self.mem_percent,
                "mem_used":  self.mem_used,
                "mem_total": self.mem_total,
                "procs":     self.process_count,
                "load":      self.load_avg,
                "processes": list(self.processes),
                "cpu_hist":  list(self.cpu_history),
                "mem_hist":  list(self.mem_history),
                "proc_hist": list(self.proc_history),
            }
