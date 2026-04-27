"""
dashboard.py
Adaptive Resource Allocation — Multiprogramming Systems Monitor
Premium dark OS dashboard | Large text | 500ms refresh | Zero-lag graphs
"""

from collections import deque

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QFrame, QSizePolicy, QGridLayout, QAbstractItemView
)
from PyQt5.QtCore  import Qt, QTimer, QPointF, QRectF
from PyQt5.QtGui   import (
    QPainter, QColor, QPen, QBrush, QFont, QFontMetrics,
    QLinearGradient, QRadialGradient, QPainterPath, QPolygonF
)

from utils import timestamp, severity, LOG_COLORS, format_bytes, HISTORY_LEN

# ═══════════════════════════════════════════════════════════════════════════════
#  COLOUR SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════
BG      = "#05080d"
BG1     = "#080e18"
BG2     = "#0d1520"
BG3     = "#111d2e"
BG4     = "#172540"
BORDER  = "#1c3352"
BORDER2 = "#2a5080"
BORDER3 = "#3a6a9a"

CPU_C   = "#00ccff"
MEM_C   = "#bb66ff"
ALLOC_C = "#00ffaa"
PROC_C  = "#33ff88"
WARN_C  = "#ffaa00"
CRIT_C  = "#ff2244"
OK_C    = "#11cc77"
ACC_C   = "#0099dd"
TEXT    = "#e0f0ff"
TEXT2   = "#6699bb"
DIM     = "#2a4a66"
PLOT_BG = "#060d18"
GRID_C  = "#0d1e30"

# ── Font sizes (pixels) ───────────────────────────────────────────────────── #
FS = 12    # small  — table rows, log entries
FM = 14    # medium — section labels, axis labels
FL = 18    # large  — graph live values, gauge labels
FX = 24    # xlarge — section header titles
FJ = 36    # jumbo  — KPI card big numbers

def font(size, bold=False, family="Consolas"):
    f = QFont(family, size)
    if bold: f.setBold(True)
    return f

def qc(hex_str): return QColor(hex_str)


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION PANEL  — glowing bordered panel with header strip
# ═══════════════════════════════════════════════════════════════════════════════
def make_panel(title, accent=None):
    """Returns (outer_frame, body_layout)."""
    accent = accent or ACC_C

    outer = QFrame()
    outer.setObjectName("panel")
    outer.setStyleSheet(f"""
        QFrame#panel {{
            background: {BG1};
            border: 2px solid {BORDER2};
            border-radius: 6px;
        }}
    """)

    vbox = QVBoxLayout(outer)
    vbox.setContentsMargins(0, 0, 0, 0)
    vbox.setSpacing(0)

    # ── header strip ─────────────────────────────────────────────────── #
    hdr = QWidget()
    hdr.setFixedHeight(38)
    hdr.setObjectName("phdr")
    hdr.setStyleSheet(f"""
        QWidget#phdr {{
            background: {BG3};
            border-bottom: 2px solid {accent};
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
        }}
    """)
    hl = QHBoxLayout(hdr)
    hl.setContentsMargins(14, 0, 14, 0)
    hl.setSpacing(8)

    # accent indicator bar
    ind = QLabel()
    ind.setFixedSize(4, 20)
    ind.setStyleSheet(
        f"background:{accent};border-radius:2px;border:none")
    hl.addWidget(ind)

    lbl = QLabel(title)
    lbl.setStyleSheet(
        f"color:{TEXT}; font-size:{FM}px; font-weight:bold;"
        f"font-family:Consolas; letter-spacing:3px; border:none;"
        f"background:transparent;")
    hl.addWidget(lbl)
    hl.addStretch()

    vbox.addWidget(hdr)

    body = QWidget()
    body.setStyleSheet(f"background:{BG1}; border:none;")
    bl = QVBoxLayout(body)
    bl.setContentsMargins(10, 10, 10, 10)
    bl.setSpacing(6)
    vbox.addWidget(body, 1)

    return outer, bl


# ═══════════════════════════════════════════════════════════════════════════════
#  KPI CARD  — large glowing number card
# ═══════════════════════════════════════════════════════════════════════════════
class KpiCard(QWidget):
    def __init__(self, title, unit="", color=CPU_C, parent=None):
        super().__init__(parent)
        self._title = title
        self._unit  = unit
        self._color = color
        self._val   = "—"
        self._sub   = ""
        self._pct   = 0.0
        self.setFixedHeight(120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumWidth(180)

    def set_value(self, val, sub="", pct=0.0):
        self._val = str(val)
        self._sub = str(sub)
        self._pct = max(0.0, min(100.0, float(pct)))
        self.update()

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # ── base ─────────────────────────────────────────────────────── #
        p.fillRect(0, 0, w, h, qc(BG2))

        # outer border
        p.setPen(QPen(qc(BORDER2), 2))
        p.drawRoundedRect(1, 1, w-2, h-2, 5, 5)

        # left glow stripe (5px)
        p.fillRect(0, 0, 5, h, qc(self._color))

        # top gradient tint
        g = QLinearGradient(0, 0, w, 0)
        c1 = qc(self._color); c1.setAlpha(45)
        c2 = qc(self._color); c2.setAlpha(0)
        g.setColorAt(0, c1); g.setColorAt(1, c2)
        p.fillRect(5, 0, w - 5, h, QBrush(g))

        # ── progress bar at bottom ────────────────────────────────────── #
        bar_h = 4
        p.fillRect(5, h - bar_h, w - 5, bar_h, qc(BG3))
        bar_w = int((w - 5) * self._pct / 100)
        if bar_w > 0:
            bar_col = qc(CRIT_C) if self._pct > 90 else \
                      qc(WARN_C) if self._pct > 75 else qc(self._color)
            p.fillRect(5, h - bar_h, bar_w, bar_h, bar_col)

        # ── TITLE ─────────────────────────────────────────────────────── #
        p.setPen(qc(TEXT2))
        p.setFont(font(FS, bold=True))
        p.drawText(14, 8, w - 18, 20,
                   Qt.AlignLeft | Qt.AlignVCenter, self._title)

        # ── BIG VALUE ─────────────────────────────────────────────────── #
        val_col = (qc(CRIT_C) if self._pct > 90
                   else qc(WARN_C) if self._pct > 75
                   else qc(self._color))
        p.setPen(val_col)
        p.setFont(font(FJ, bold=True))
        p.drawText(12, 24, w - 16, 60,
                   Qt.AlignLeft | Qt.AlignVCenter, self._val)

        # ── unit ──────────────────────────────────────────────────────── #
        p.setPen(qc(TEXT2))
        p.setFont(font(FM))
        p.drawText(14, 86, w - 18, 26,
                   Qt.AlignLeft | Qt.AlignVCenter,
                   f"  {self._unit}   {self._sub}")


# ═══════════════════════════════════════════════════════════════════════════════
#  CIRCULAR GAUGE
# ═══════════════════════════════════════════════════════════════════════════════
class GaugeWidget(QWidget):
    def __init__(self, label, color, parent=None):
        super().__init__(parent)
        self._label = label
        self._color = color
        self._pct   = 0.0
        self.setFixedSize(160, 120)

    def set_pct(self, v):
        self._pct = max(0.0, min(100.0, float(v)))
        self.update()

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        p.fillRect(0, 0, w, h, qc(BG2))
        p.setPen(QPen(qc(BORDER2), 2))
        p.drawRoundedRect(1, 1, w-2, h-2, 5, 5)

        cx, cy = w // 2, h // 2 + 8
        r = min(w, h) // 2 - 18

        # track shadow
        p.setPen(QPen(qc(BG3), 12, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(cx-r, cy-r, 2*r, 2*r, 225*16, -270*16)

        # coloured arc
        col = (qc(CRIT_C) if self._pct > 90
               else qc(WARN_C) if self._pct > 75
               else qc(self._color))
        p.setPen(QPen(col, 12, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(cx-r, cy-r, 2*r, 2*r,
                  225*16, int(-270*16 * self._pct / 100))

        # inner fill
        ir = r - 16
        p.setPen(Qt.NoPen)
        p.setBrush(qc(BG1))
        p.drawEllipse(QPointF(cx, cy), ir, ir)

        # value text
        p.setPen(col)
        p.setFont(font(FL + 2, bold=True))
        p.drawText(0, cy - 20, w, 36, Qt.AlignCenter,
                   f"{self._pct:.0f}%")

        # label
        p.setPen(qc(TEXT2))
        p.setFont(font(FM, bold=True))
        p.drawText(0, cy + 18, w, 24, Qt.AlignCenter, self._label)


# ═══════════════════════════════════════════════════════════════════════════════
#  REAL-TIME GRAPH  — clean, clipped, anti-aliased
# ═══════════════════════════════════════════════════════════════════════════════
class GraphCanvas(QWidget):
    def __init__(self, label, color, unit="%", maxval=100.0, parent=None):
        super().__init__(parent)
        self.label  = label
        self.color  = qc(color)
        self.unit   = unit
        self.maxval = float(maxval)
        self.data   = deque([0.0] * HISTORY_LEN, maxlen=HISTORY_LEN)
        self.setMinimumHeight(150)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_data(self, lst):
        if lst:
            self.data = deque(list(lst)[-HISTORY_LEN:], maxlen=HISTORY_LEN)
            self.update()

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # ── padding — generous so labels NEVER overlap graph ─────────── #
        PL, PR, PT, PB = 62, 16, 36, 30
        dw = w - PL - PR
        dh = h - PT - PB
        if dw < 40 or dh < 40:
            return

        data = list(self.data)
        n    = len(data)
        lv   = data[-1] if data else 0.0

        # dynamic colour based on value
        cur_col = (qc(CRIT_C) if lv > self.maxval * 0.9
                   else qc(WARN_C) if lv > self.maxval * 0.75
                   else qc(self.color))

        # ── outer widget background ───────────────────────────────────── #
        p.fillRect(0, 0, w, h, qc(BG1))

        # ── TITLE  (above graph — left) ──────────────────────────────── #
        p.setPen(qc(TEXT2))
        p.setFont(font(FM, bold=True))
        p.drawText(PL + 4, 0, dw // 2, PT,
                   Qt.AlignLeft | Qt.AlignVCenter, self.label)

        # ── LIVE VALUE  (above graph — right) ────────────────────────── #
        p.setPen(cur_col)
        p.setFont(font(FL, bold=True))
        p.drawText(PL, 0, dw - 4, PT,
                   Qt.AlignRight | Qt.AlignVCenter,
                   f"{lv:.1f}{self.unit}")

        # ── PLOT AREA ────────────────────────────────────────────────── #
        p.fillRect(PL, PT, dw, dh, qc(PLOT_BG))

        # strong 2-px border around plot area
        p.setPen(QPen(qc(BORDER2), 2))
        p.drawRect(PL, PT, dw, dh)

        # ── Y-AXIS labels + horizontal grid ──────────────────────────── #
        STEPS = 5
        p.setFont(font(FS))
        for i in range(STEPS + 1):
            frac = i / STEPS
            gy   = PT + dh * frac
            val  = self.maxval * (1.0 - frac)

            # dotted grid inside plot
            p.setPen(QPen(qc(GRID_C), 1, Qt.DotLine))
            p.drawLine(PL + 1, int(gy), PL + dw - 1, int(gy))

            # Y label — right-aligned in margin, large enough to read
            p.setPen(qc(TEXT2))
            lstr = f"{int(val)}{self.unit}" if i == 0 else f"{int(val)}"
            p.drawText(2, int(gy) - 12, PL - 6, 24,
                       Qt.AlignRight | Qt.AlignVCenter, lstr)

        # ── vertical grid (6 divisions = 10s each) ────────────────────── #
        for i in range(1, 6):
            vx = PL + dw * i / 6
            p.setPen(QPen(qc(GRID_C), 1, Qt.DotLine))
            p.drawLine(int(vx), PT + 1, int(vx), PT + dh - 1)

        # ── X-AXIS time labels BELOW plot ────────────────────────────── #
        p.setPen(qc(TEXT2))
        p.setFont(font(FS))
        p.drawText(PL, h - PB + 4, 70, 22, Qt.AlignLeft,  "60s")
        p.drawText(PL, h - PB + 4, dw, 22, Qt.AlignCenter, "30s")
        p.drawText(PL, h - PB + 4, dw, 22, Qt.AlignRight,  "0s")

        # ── DATA ─────────────────────────────────────────────────────── #
        if n < 2:
            return

        def py(v):
            v = max(0.0, min(self.maxval, float(v)))
            return PT + dh * (1.0 - v / self.maxval)

        # RIGHT-ALIGN: newest sample always at the far right ("now")
        # Each sample occupies dw/(HISTORY_LEN-1) pixels.
        # If we have fewer samples than HISTORY_LEN, the oldest point
        # sits at (right edge - n*step) so the line grows left→right.
        step = dw / (HISTORY_LEN - 1)

        def px(i):
            # i=0 is oldest, i=n-1 is newest (rightmost = PL+dw)
            return PL + dw - (n - 1 - i) * step

        # clip strictly to plot area
        p.setClipRect(PL + 1, PT + 1, dw - 2, dh - 2)

        # gradient fill under curve
        path = QPainterPath()
        path.moveTo(px(0), PT + dh)
        for i, v in enumerate(data):
            path.lineTo(px(i), py(v))
        path.lineTo(px(n - 1), PT + dh)
        path.closeSubpath()

        gfill = QLinearGradient(0, PT, 0, PT + dh)
        hi = qc(self.color); hi.setAlpha(100)
        lo = qc(self.color); lo.setAlpha(6)
        gfill.setColorAt(0, hi)
        gfill.setColorAt(1, lo)
        p.fillPath(path, QBrush(gfill))

        # line
        pen = QPen(cur_col, 2)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        line = QPainterPath()
        for i, v in enumerate(data):
            pt = QPointF(px(i), py(v))
            if i == 0: line.moveTo(pt)
            else:      line.lineTo(pt)
        p.drawPath(line)

        # endpoint dot at the right edge ("now") — remove clip so dot isn't cut
        p.setClipping(False)
        ex = px(n - 1)          # always = PL + dw (right edge)
        ey = max(PT + 5, min(PT + dh - 5, py(lv)))
        p.setPen(QPen(qc(BG), 2))
        p.setBrush(cur_col)
        p.drawEllipse(QPointF(ex, ey), 5, 5)


# ═══════════════════════════════════════════════════════════════════════════════
#  MINI LED INDICATOR
# ═══════════════════════════════════════════════════════════════════════════════
class Led(QWidget):
    def __init__(self, color=OK_C, parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedSize(14, 14)

    def set_color(self, c):
        self._color = c
        self.update()

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        p.setBrush(qc(self._color))
        p.drawEllipse(2, 2, 10, 10)


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN DASHBOARD WINDOW
# ═══════════════════════════════════════════════════════════════════════════════
class Dashboard(QMainWindow):
    def __init__(self, monitor, allocator):
        super().__init__()
        self.monitor    = monitor
        self.allocator  = allocator
        self._log_buf   = []
        self._alert_buf = []

        self.setWindowTitle(
            "Adaptive Resource Allocation — Multiprogramming Systems Monitor")
        self._apply_base_style()
        self.resize(1600, 1000)
        self._build_ui()

        # 500ms refresh — smooth, no lag
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(500)

    # ── global stylesheet ────────────────────────────────────────────── #
    def _apply_base_style(self):
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background: {BG};
                color: {TEXT};
                font-family: Consolas;
            }}
            QScrollBar:vertical {{
                background: {BG1}; width: 8px; border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {BORDER2}; border-radius: 3px; min-height: 24px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height: 0px; }}
            QScrollBar:horizontal {{ height: 0px; }}
        """)

    # ════════════════════════════════════════════════════════════════════ #
    #  UI CONSTRUCTION
    # ════════════════════════════════════════════════════════════════════ #
    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        main = QVBoxLayout(root)
        main.setContentsMargins(12, 12, 12, 12)
        main.setSpacing(10)

        main.addWidget(self._build_header())         # project title
        main.addWidget(self._build_kpi_strip())      # KPI gauges + cards

        centre = QHBoxLayout()
        centre.setSpacing(10)
        centre.addWidget(self._build_graph_panel(), 56)
        centre.addWidget(self._build_proc_panel(),  44)
        main.addLayout(centre, 1)

        main.addWidget(self._build_log_strip())      # logs / decisions / alerts

    # ── HEADER ───────────────────────────────────────────────────────── #
    def _build_header(self):
        bar = QFrame()
        bar.setObjectName("hbar")
        bar.setFixedHeight(80)
        bar.setStyleSheet(f"""
            QFrame#hbar {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0b1e38, stop:0.6 {BG3}, stop:1 {BG1}
                );
                border: 2px solid {BORDER2};
                border-radius: 6px;
            }}
        """)
        h = QHBoxLayout(bar)
        h.setContentsMargins(20, 8, 20, 8)
        h.setSpacing(16)

        # left: title + description
        lv = QVBoxLayout()
        lv.setSpacing(4)

        title = QLabel(
            "ADAPTIVE RESOURCE ALLOCATION  ─  MULTIPROGRAMMING SYSTEMS")
        title.setStyleSheet(
            f"color:{CPU_C}; font-size:{FM+2}px; font-weight:bold;"
            f"letter-spacing:2px; background:transparent; border:none;")
        lv.addWidget(title)

        desc = QLabel(
            "Dynamically adjusts resource allocation among multiple programs "
            "to optimize CPU & memory utilization.  Monitors system "
            "performance and reallocates resources in real-time to prevent bottlenecks.")
        desc.setStyleSheet(
            f"color:{TEXT2}; font-size:{FS+1}px;"
            f"background:transparent; border:none;")
        desc.setWordWrap(True)
        lv.addWidget(desc)
        h.addLayout(lv, 1)

        # right: clock + severity
        rv = QVBoxLayout()
        rv.setSpacing(6)
        rv.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self._ts_lbl = QLabel()
        self._ts_lbl.setStyleSheet(
            f"color:{ACC_C}; font-size:{FL}px; font-weight:bold;"
            f"background:transparent; border:none;")
        self._ts_lbl.setAlignment(Qt.AlignRight)
        rv.addWidget(self._ts_lbl)

        sh = QHBoxLayout()
        sh.setSpacing(8)
        self._sev_led = Led(OK_C)
        sh.addStretch()
        sh.addWidget(self._sev_led)
        self._sev_lbl = QLabel("NORMAL")
        self._sev_lbl.setFixedSize(180, 34)
        self._sev_lbl.setAlignment(Qt.AlignCenter)
        self._sev_lbl.setStyleSheet(
            f"color:{OK_C}; font-size:{FM}px; font-weight:bold;"
            f"border:2px solid {OK_C}; border-radius:4px;"
            f"background:{BG2}; letter-spacing:2px;")
        sh.addWidget(self._sev_lbl)
        rv.addLayout(sh)
        h.addLayout(rv)
        return bar

    # ── KPI STRIP ────────────────────────────────────────────────────── #
    def _build_kpi_strip(self):
        row = QWidget()
        row.setFixedHeight(128)
        row.setStyleSheet("background:transparent;")
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(10)

        self._g_cpu = GaugeWidget("CPU",    CPU_C)
        self._g_mem = GaugeWidget("MEMORY", MEM_C)
        h.addWidget(self._g_cpu)
        h.addWidget(self._g_mem)

        # vertical separator
        sep = QFrame()
        sep.setFixedWidth(2)
        sep.setStyleSheet(f"background:{BORDER};")
        h.addWidget(sep)

        self._c_cpu  = KpiCard("CPU USAGE",    "%",       CPU_C)
        self._c_mem  = KpiCard("MEMORY USAGE", "%",       MEM_C)
        self._c_proc = KpiCard("PROCESSES",    "active",  PROC_C)
        self._c_load = KpiCard("SYSTEM LOAD",  "avg",     WARN_C)
        for c in (self._c_cpu, self._c_mem, self._c_proc, self._c_load):
            h.addWidget(c, 1)
        return row

    # ── GRAPH PANEL ──────────────────────────────────────────────────── #
    def _build_graph_panel(self):
        outer, bl = make_panel("REAL-TIME PERFORMANCE GRAPHS", CPU_C)

        grid = QGridLayout()
        grid.setSpacing(10)

        self._gr_cpu   = GraphCanvas("CPU Usage",             CPU_C,   "%",  100)
        self._gr_mem   = GraphCanvas("Memory Usage",          MEM_C,   "%",  100)
        self._gr_alloc = GraphCanvas("Allocation Efficiency", ALLOC_C, "%",  100)
        self._gr_proc  = GraphCanvas("Process Count",         PROC_C,  "",   400)

        grid.addWidget(self._gr_cpu,   0, 0)
        grid.addWidget(self._gr_mem,   0, 1)
        grid.addWidget(self._gr_alloc, 1, 0)
        grid.addWidget(self._gr_proc,  1, 1)

        for i in range(2):
            grid.setRowStretch(i, 1)
            grid.setColumnStretch(i, 1)

        bl.addLayout(grid)
        return outer

    # ── PROCESS TABLE ────────────────────────────────────────────────── #
    def _build_proc_panel(self):
        outer, bl = make_panel("ACTIVE PROCESS MONITOR", PROC_C)

        # ── status legend — proper NORMAL / WARNING / CRITICAL badges ── #
        leg = QWidget()
        leg.setStyleSheet("background:transparent;")
        lh = QHBoxLayout(leg)
        lh.setContentsMargins(0, 0, 0, 6)
        lh.setSpacing(10)

        status_lbl = QLabel("CPU STATUS:")
        status_lbl.setStyleSheet(
            f"color:{TEXT2}; font-size:{FS}px; font-weight:bold;"
            f"border:none; background:transparent;")
        lh.addWidget(status_lbl)

        for txt, fg, bg_col, bdr in [
            ("✖  CRITICAL",  CRIT_C, "#1a0008", CRIT_C),
            ("▲  WARNING",   WARN_C, "#1a1000", WARN_C),
            ("●  NORMAL",    OK_C,   "#061a0e", OK_C),
        ]:
            badge = QLabel(txt)
            badge.setStyleSheet(
                f"color:{fg}; font-size:{FS}px; font-weight:bold;"
                f"background:{bg_col}; border:1px solid {bdr};"
                f"border-radius:3px; padding:2px 10px;")
            lh.addWidget(badge)

        lh.addStretch()
        bl.addWidget(leg)

        cols = ["PID", "PROCESS NAME", "CPU %", "MEM %", "NICE", "STATUS"]
        self._tbl = QTableWidget(0, len(cols))
        self._tbl.setHorizontalHeaderLabels(cols)
        self._tbl.setStyleSheet(f"""
            QTableWidget {{
                background: {BG1};
                color: {TEXT};
                gridline-color: {BORDER};
                border: 2px solid {BORDER2};
                font-size: {FS+1}px;
                font-family: Consolas;
                selection-background-color: {BG4};
                selection-color: {CPU_C};
                outline: none;
            }}
            QHeaderView::section {{
                background: {BG3};
                color: {ACC_C};
                border: 1px solid {BORDER2};
                padding: 6px 6px;
                font-size: {FS+1}px;
                font-weight: bold;
                font-family: Consolas;
                letter-spacing: 1px;
            }}
            QTableWidget::item {{
                padding: 5px 8px;
                border-bottom: 1px solid {BORDER};
            }}
            QTableWidget::item:alternate {{
                background: {BG2};
            }}
            QTableWidget::item:selected {{
                background: {BG4};
                color: {CPU_C};
            }}
        """)
        hdr = self._tbl.horizontalHeader()
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        for i in (0, 2, 3, 4, 5):
            hdr.setSectionResizeMode(i, QHeaderView.Fixed)
        self._tbl.setColumnWidth(0,  68)
        self._tbl.setColumnWidth(2,  76)
        self._tbl.setColumnWidth(3,  76)
        self._tbl.setColumnWidth(4,  56)
        self._tbl.setColumnWidth(5,  92)
        self._tbl.verticalHeader().setVisible(False)
        self._tbl.setAlternatingRowColors(True)
        self._tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._tbl.verticalHeader().setDefaultSectionSize(30)
        self._tbl.setShowGrid(True)
        bl.addWidget(self._tbl, 1)
        return outer

    # ── LOG STRIP ────────────────────────────────────────────────────── #
    def _build_log_strip(self):
        row = QWidget()
        row.setFixedHeight(210)
        row.setStyleSheet("background:transparent;")
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(10)

        specs = [
            ("_log_box",   "SYSTEM LOG",                    TEXT2),
            ("_dec_box",   "ADAPTIVE ALLOCATION DECISIONS", ALLOC_C),
            ("_alert_box", "ALERTS & WARNINGS",             CRIT_C),
        ]
        for attr, title, color in specs:
            outer, bl = make_panel(title, color)
            tb = self._make_tb()
            bl.addWidget(tb)
            setattr(self, attr, tb)
            h.addWidget(outer, 1)
        return row

    def _make_tb(self):
        tb = QTextEdit()
        tb.setReadOnly(True)
        tb.setStyleSheet(f"""
            QTextEdit {{
                background: {BG};
                color: {TEXT};
                border: none;
                font-size: {FM}px;
                font-family: Consolas;
                line-height: 160%;
            }}
        """)
        return tb

    # ════════════════════════════════════════════════════════════════════ #
    #  REFRESH  — every 500ms
    # ════════════════════════════════════════════════════════════════════ #
    def _refresh(self):
        snap = self.monitor.snapshot()
        cpu  = snap["cpu"]
        mem  = snap["mem"]
        load = snap["load"]
        sev  = severity(cpu, mem)

        # clock
        self._ts_lbl.setText(f"⏱  {timestamp()}")

        # gauges
        self._g_cpu.set_pct(cpu)
        self._g_mem.set_pct(mem)

        # KPI cards
        self._c_cpu.set_value( f"{cpu:.1f}", f"Load: {load}", cpu)
        self._c_mem.set_value( f"{mem:.1f}",
                               f"{format_bytes(snap['mem_used'])}", mem)
        self._c_proc.set_value(str(snap["procs"]), "running")
        self._c_load.set_value(f"{load:.2f}",
                               "HIGH" if load > 3 else "NORMAL")

        # severity badge
        sev_map = {
            "CRITICAL": (CRIT_C, "🔴 CRITICAL"),
            "WARNING":  (WARN_C, "🟡 WARNING"),
            "ELEVATED": (ACC_C,  "🔵 ELEVATED"),
            "NORMAL":   (OK_C,   "🟢 NORMAL"),
        }
        sc, st = sev_map.get(sev, (OK_C, "NORMAL"))
        self._sev_led.set_color(sc)
        self._sev_lbl.setText(st)
        self._sev_lbl.setStyleSheet(
            f"color:{sc}; font-size:{FM}px; font-weight:bold;"
            f"border:2px solid {sc}; border-radius:4px;"
            f"background:{BG2}; letter-spacing:2px;")

        # graphs
        self._gr_cpu.set_data(snap["cpu_hist"])
        self._gr_mem.set_data(snap["mem_hist"])

        ah = self.allocator.get_alloc_history()
        self._gr_alloc.set_data(ah if ah else [0.0] * HISTORY_LEN)

        ph = snap["proc_hist"]
        if ph:
            mx = max(max(ph), 10)
            self._gr_proc.maxval = mx * 1.3
            self._gr_proc.set_data(ph)

        # process table
        procs = snap["processes"]
        self._tbl.setRowCount(len(procs))
        for r, pr in enumerate(procs):
            cells = [
                str(pr["pid"]),
                pr["name"],
                f"{pr['cpu']:.1f}",
                f"{pr['mem']:.2f}",
                str(pr.get("nice", 0)),
                pr.get("status", "?"),
            ]
            for ci, txt in enumerate(cells):
                item = QTableWidgetItem(txt)
                item.setTextAlignment(Qt.AlignCenter)
                if ci == 2:
                    item.setForeground(qc(
                        CRIT_C if pr["cpu"] > 50
                        else WARN_C if pr["cpu"] > 20
                        else PROC_C))
                if ci == 5:
                    st_txt = txt.lower()
                    item.setForeground(qc(
                        OK_C   if "running" in st_txt
                        else CRIT_C if ("zombie" in st_txt or "dead" in st_txt)
                        else TEXT2))
                self._tbl.setItem(r, ci, item)

        self._update_logs(cpu, mem, sev)

    # ── LOGS ─────────────────────────────────────────────────────────── #
    def _update_logs(self, cpu, mem, sev):
        ts  = timestamp()
        col = LOG_COLORS.get(sev, TEXT)

        # system log — every 500ms
        self._log_buf.append(
            f'<span style="color:{DIM};font-size:{FM}px">[{ts}]</span> '
            f'<span style="color:{col};font-size:{FM}px">'
            f'CPU {cpu:.1f}%  &nbsp; MEM {mem:.1f}%  &nbsp; [{sev}]</span>'
        )
        if len(self._log_buf) > 500:
            self._log_buf = self._log_buf[-500:]
        self._log_box.setHtml(
            f'<div style="font-family:Consolas;font-size:{FM}px;line-height:1.7">'
            + "<br>".join(self._log_buf[-80:]) + "</div>")
        sb = self._log_box.verticalScrollBar()
        sb.setValue(sb.maximum())

        # decisions
        decs = self.allocator.get_decisions()
        if decs:
            rows = [
                f'<span style="color:{DIM};font-size:{FM}px">[{t}]</span> '
                f'<span style="color:{ALLOC_C};font-size:{FM}px">{m}</span>'
                for t, m in decs[-60:]
            ]
            html = ("<br>".join(rows))
        else:
            html = (f'<span style="color:{DIM};font-size:{FM}px">'
                    f'Monitoring active — no allocation events yet.</span>')
        self._dec_box.setHtml(
            f'<div style="font-family:Consolas;font-size:{FM}px;line-height:1.7">'
            + html + "</div>")
        sb2 = self._dec_box.verticalScrollBar()
        sb2.setValue(sb2.maximum())

        # alerts (append only on breach)
        if cpu > 90 or mem > 90:
            self._alert_buf.append(
                f'<span style="color:{CRIT_C};font-size:{FM}px;font-weight:bold">'
                f'[{ts}] &#9888; CRITICAL — CPU={cpu:.1f}%  MEM={mem:.1f}%</span>')
        elif cpu > 75 or mem > 75:
            self._alert_buf.append(
                f'<span style="color:{WARN_C};font-size:{FM}px;font-weight:bold">'
                f'[{ts}] &#9888; WARNING — CPU={cpu:.1f}%  MEM={mem:.1f}%</span>')

        if len(self._alert_buf) > 400:
            self._alert_buf = self._alert_buf[-400:]

        if self._alert_buf:
            self._alert_box.setHtml(
                f'<div style="font-family:Consolas;font-size:{FM}px;line-height:1.7">'
                + "<br>".join(self._alert_buf[-60:]) + "</div>")
            sb3 = self._alert_box.verticalScrollBar()
            sb3.setValue(sb3.maximum())
        else:
            self._alert_box.setHtml(
                f'<span style="color:{OK_C};font-size:{FM}px">'
                f'&#10003; &nbsp;System operating within normal thresholds.</span>')

    # ── external log callback (from allocator thread) ─────────────────── #
    def append_log(self, msg, kind="INFO"):
        col = LOG_COLORS.get(kind, TEXT)
        ts  = timestamp()
        self._log_buf.append(
            f'<span style="color:{DIM};font-size:{FM}px">[{ts}]</span> '
            f'<span style="color:{col};font-size:{FM}px">{msg}</span>'
        )