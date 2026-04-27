# Adaptive Resource Allocation in Multiprogramming Systems

> **Course:** CSE-316 Operating Systems — CA2 Project  
> **Technology:** Python · PyQt5 · psutil · Real-Time Dashboard

---

## Project Description

Develop a system that dynamically adjusts resource allocation among multiple programs to optimize CPU and memory utilization. The solution monitors system performance and reallocates resources in real-time to prevent bottlenecks.

---

## Project Structure

adaptive_resource_monitor/
│
├── main.py                  # Entry point — wires all modules together
├── system_monitor.py        # Multi-threaded real-time system data collector
├── adaptive_allocator.py    # Adaptive resource reallocation algorithm
├── dashboard.py             # Full PyQt5 professional dark UI dashboard
├── utils.py                 # Shared constants, helpers, colour maps
└── requirements.txt         # Python dependencies

---

## Features

| Feature | Description |


| Real-Time CPU Monitoring | Sampled every 0.5s using blocking `psutil.cpu_percent` |
| Memory Usage Monitoring | Non-blocking memory poll every 0.5s |
| Process Monitoring | Top-60 processes sorted by CPU, refreshed every 2s |
| Adaptive Allocation Algorithm | Detects bottlenecks, renices heavy processes automatically |
| Real-Time Graphs | 4 live graphs: CPU, Memory, Allocation Efficiency, Process Count |
| Alerts System | NORMAL / WARNING / CRITICAL severity with colour-coded badges |
| Performance Metrics Panel | Circular gauges + large KPI cards with progress bars |

---

## Algorithm — Adaptive Resource Allocation

WHILE system is running:
    sample = monitor.snapshot()

    IF cpu > 75%:
        identify top-3 CPU-heavy processes
        renice them to nice=+5  (lower priority)
        log: "CPU bottleneck — throttling N process(es)"

    ELSE IF memory > 80%:
        identify top-2 memory-heavy processes
        renice them to nice=+5
        log: "Memory pressure — deprioritising consumers"

    ELSE IF cpu < 40% AND memory < 50%:
        find previously demoted processes
        restore nice=0  (normal priority)
        log: "Load normalised — restoring priorities"

    compute allocation_efficiency_score (0–100)
    append to history → shown in Allocation Efficiency graph
    sleep 3s

---

## Installation

bash

# 1. Clone the repository

git clone https://github.com/KartikyKaushik21/Adaptive-Resource-Allocation-Multiprogramming
cd adaptive-resource-monitor

# 2. (Optional) Create virtual environment

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS

# 3. Install dependencies

pip install -r requirements.txt

# 4. Run the dashboard

python main.py


**Requirements:** Python 3.9+, Windows / Linux / macOS

---

## UI Layout

---
┌─────────────────────────────────────────────────────────────────┐
│  TITLE BAR — Project title · Description · Clock · Severity     │
├──────────┬──────────┬────────────┬────────────┬─────────────────┤
│ CPU Gauge│ MEM Gauge│ CPU USAGE  │ MEM USAGE  │ PROCESSES  LOAD │
│  (arc)   │  (arc)   │   22.1 %   │   75.1 %   │    269    0.11  │
├──────────┴──────────┴────────────┴────────────┴─────────────────┤
│  REAL-TIME GRAPHS (2×2)          │  ACTIVE PROCESS MONITOR      │
│  ┌──────────┐  ┌──────────┐      │  Status: ● NORMAL ▲ WARNING  │
│  │ CPU Graph│  │ MEM Graph│      │  ✖ CRITICAL                  │
│  └──────────┘  └──────────┘      │  ┌────────────────────────┐  │
│  ┌──────────┐  ┌──────────┐      │  │ PID │ Name │CPU%│MEM%  │  │
│  │ Alloc Eff│  │Proc Count│      │  │ ... │ ...  │... │...   │  │
│  └──────────┘  └──────────┘      │  └────────────────────────┘  │
├───────────────────┬───────────────────────────┬──────────────────┤
│   SYSTEM LOG      │  ADAPTIVE DECISIONS        │  ALERTS          │
│   [HH:MM:SS] ...  │  [HH:MM:SS] renice PID ... │  ⚠ WARNING ...   │
└───────────────────┴───────────────────────────┴──────────────────┘
'''

---

## Git Workflow — Branch Strategy

This project uses **feature branches** merged into `main` after testing.

### Branch Structure

---
main
├── feature/ui-dashboard          ← PyQt5 dark theme dashboard
├── feature/system-monitor        ← Multi-thread CPU/MEM/PROC monitoring
├── feature/adaptive-allocator    ← Reallocation algorithm
├── feature/realtime-graphs       ← Live graph canvases
├── feature/process-table         ← Process monitor with colour coding
├── feature/alerts-logging        ← Alert system + log panels
└── feature/ui-improvements       ← Font sizes, borders, graph fixes
---

### Commit History (7+ Revisions)

---
Rev 1  feat: initial project structure and requirements.txt
Rev 2  feat(monitor): add SystemMonitor with psutil CPU/MEM/PROC threads
Rev 3  feat(allocator): implement AdaptiveAllocator with renice algorithm
Rev 4  feat(dashboard): build PyQt5 dark UI with KPI cards and gauges
Rev 5  feat(graphs): add real-time GraphCanvas with clipped anti-aliased lines
Rev 6  fix(lag): fix time lag — separate CPU thread with interval=0.5s blocking sample
Rev 7  fix(ui): increase all font sizes (12–36px), fix graph right-alignment
Rev 8  fix(legend): replace CPU% thresholds with NORMAL/WARNING/CRITICAL badges
Rev 9  fix(windows): fix HiDPI attribute error and SystemMonitor interval arg
---

### Commands to Push with Branches

---bash
# ── Initial setup ──────────────────────────────────────────────
git init
git remote add origin https://github.com/<your-username>/adaptive-resource-monitor.git

# ── Rev 1: project scaffold ────────────────────────────────────
git checkout -b feature/project-scaffold
git add requirements.txt utils.py
git commit -m "feat: initial project structure and requirements.txt"
git push origin feature/project-scaffold
git checkout main
git merge feature/project-scaffold
git push origin main

# ── Rev 2: system monitor ──────────────────────────────────────
git checkout -b feature/system-monitor
git add system_monitor.py
git commit -m "feat(monitor): add SystemMonitor with psutil CPU/MEM/PROC threads"
git push origin feature/system-monitor
git checkout main
git merge feature/system-monitor
git push origin main

# ── Rev 3: adaptive allocator ──────────────────────────────────
git checkout -b feature/adaptive-allocator
git add adaptive_allocator.py
git commit -m "feat(allocator): implement AdaptiveAllocator with renice algorithm"
git push origin feature/adaptive-allocator
git checkout main
git merge feature/adaptive-allocator
git push origin main

# ── Rev 4: dashboard UI ────────────────────────────────────────
git checkout -b feature/ui-dashboard
git add dashboard.py main.py
git commit -m "feat(dashboard): build PyQt5 dark UI with KPI cards, gauges, graphs"
git push origin feature/ui-dashboard
git checkout main
git merge feature/ui-dashboard
git push origin main

# ── Rev 5: real-time graphs ────────────────────────────────────
git checkout -b feature/realtime-graphs
git add dashboard.py
git commit -m "feat(graphs): add GraphCanvas with clipped anti-aliased lines and gradient fill"
git push origin feature/realtime-graphs
git checkout main
git merge feature/realtime-graphs
git push origin main

# ── Rev 6: lag fix ─────────────────────────────────────────────
git checkout -b fix/time-lag
git add system_monitor.py dashboard.py
git commit -m "fix(lag): separate CPU thread blocking 0.5s sample, 500ms UI refresh"
git push origin fix/time-lag
git checkout main
git merge fix/time-lag
git push origin main

# ── Rev 7: font and border improvements ────────────────────────
git checkout -b feature/ui-improvements
git add dashboard.py
git commit -m "fix(ui): increase fonts to 12-36px, add progress bars, fix graph right-align"
git push origin feature/ui-improvements
git checkout main
git merge feature/ui-improvements
git push origin main

# ── Rev 8: legend fix ──────────────────────────────────────────
git checkout -b fix/process-legend
git add dashboard.py
git commit -m "fix(legend): replace CPU% thresholds with NORMAL/WARNING/CRITICAL status badges"
git push origin fix/process-legend
git checkout main
git merge fix/process-legend
git push origin main

# ── Rev 9: Windows compatibility ───────────────────────────────
git checkout -b fix/windows-compat
git add main.py system_monitor.py
git commit -m "fix(windows): HiDPI before QApplication, remove interval arg, getloadavg fallback"
git push origin fix/windows-compat
git checkout main
git merge fix/windows-compat
git push origin main

# ── Final: add README ──────────────────────────────────────────
git add README.md
git commit -m "docs: add README with setup, algorithm, UI layout, and git workflow"
git push origin main
---

---

## Module Details

### `system_monitor.py`
Three dedicated threads for zero lag:
- **`_cpu_thread`** — `psutil.cpu_percent(interval=0.5)` blocking call → accurate, no zero-return bug
- **`_mem_thread`** — virtual memory every 0.5s (non-blocking)
- **`_proc_thread`** — full process scan every 2s (isolated so it never blocks CPU/MEM threads)

### `adaptive_allocator.py`
- Runs in its own daemon thread every 3 seconds
- Detects: CPU > 75% → demote heavy processes; MEM > 80% → deprioritise consumers
- Restores priorities when system normalises (CPU < 40%, MEM < 50%)
- Computes **allocation efficiency score** (0–100) for the Efficiency graph

### `dashboard.py`
- `KpiCard` — large 36px number with progress bar and colour-coded value
- `GaugeWidget` — circular arc gauge with dynamic colour (green → orange → red)
- `GraphCanvas` — right-aligned scrolling graph, clipped to plot area, anti-aliased
- `Dashboard` — main `QMainWindow`, refreshes every 500ms via `QTimer`

### `utils.py`
- `HISTORY_LEN = 120` — 120 samples × 0.5s = 60 seconds of history
- `severity(cpu, mem)` — returns NORMAL / ELEVATED / WARNING / CRITICAL
- `format_bytes(b)` — human-readable byte formatting

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| `psutil` | ≥ 5.9.0 | System metrics — CPU, memory, processes |
| `PyQt5` | ≥ 5.15.9 | GUI framework — widgets, painting, timers |
| `numpy` | ≥ 1.24.0 | Numerical utilities |
| `matplotlib` | ≥ 3.7.0 | Available for extended graph features |

---

## License

free to use for academic and educational purposes.
