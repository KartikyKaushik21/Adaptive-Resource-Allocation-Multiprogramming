import sys
import os

# ── HiDPI MUST be set before QApplication ──────────────────────────────── #
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtCore    import Qt
from PyQt5.QtWidgets import QApplication

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps,    True)

from system_monitor      import SystemMonitor
from adaptive_allocator  import AdaptiveAllocator
from dashboard           import Dashboard


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Adaptive Resource Allocation Monitor")

    # ── start monitor first ─────────────────────────────────────────── #
    monitor = SystemMonitor()
    monitor.start()

    # ── log buffer for messages before dashboard is ready ───────────── #
    pending   = []
    container = []   # will hold the Dashboard once created

    def log_cb(msg, kind="INFO"):
        if container:
            try:    container[0].append_log(msg, kind)
            except Exception: pass
        else:
            pending.append((msg, kind))

    # ── start allocator ─────────────────────────────────────────────── #
    allocator = AdaptiveAllocator(monitor, log_cb=log_cb, interval=3.0)
    allocator.start()

    # ── create dashboard normally ────────────────────────────────────── #
    dashboard = Dashboard(monitor, allocator)
    container.append(dashboard)

    # flush buffered log messages
    for msg, kind in pending:
        try:    dashboard.append_log(msg, kind)
        except Exception: pass

    dashboard.show()
    dashboard.append_log(
        "System monitor started  ─  CPU thread: 0.5s  |  MEM thread: 0.5s  "
        "|  PROC thread: 2.0s", "INFO")
    dashboard.append_log(
        "Adaptive allocator active  ─  reallocation cycle: every 3s", "ALLOC")

    ret = app.exec_()
    monitor.stop()
    allocator.stop()
    sys.exit(ret)


if __name__ == "__main__":
    main()
