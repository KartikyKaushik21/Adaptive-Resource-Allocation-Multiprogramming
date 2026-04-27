import datetime
from collections import deque

HISTORY_LEN = 120   # 120 samples × 0.5s = 60 seconds of history

def timestamp():
    return datetime.datetime.now().strftime("%H:%M:%S")

def make_deque(maxlen=HISTORY_LEN):
    return deque([0.0] * maxlen, maxlen=maxlen)

def format_bytes(b):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"

def severity(cpu, mem):
    if cpu > 90 or mem > 90:  return "CRITICAL"
    if cpu > 75 or mem > 75:  return "WARNING"
    if cpu > 55 or mem > 55:  return "ELEVATED"
    return "NORMAL"

LOG_COLORS = {
    "CRITICAL": "#ff3c50",
    "WARNING":  "#ffba30",
    "ELEVATED": "#18b0e8",
    "NORMAL":   "#20dc84",
    "INFO":     "#7aaece",
    "ALLOC":    "#c47aff",
}
