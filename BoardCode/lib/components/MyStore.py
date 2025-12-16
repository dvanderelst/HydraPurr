# lib/components/MyStore.py
import os, time as _time, board  # sdcardio/storage no longer needed here
from components.MyRTC import MyRTC
from components import MySD  # ← NEW: centralize SD ops

# ---------------------------------------------------------------------
# Global variables and constants
# ---------------------------------------------------------------------
path_separator = os.sep
separator = ','
mount_point = '/sd'
sd_is_mounted = False
rtc = None            # shared RTC instance
t0_mono = None        # baseline monotonic at init
timebase_ready = False

# ---------------------------------------------------------------------
# Filesystem utilities (path helpers remain local)
# ---------------------------------------------------------------------
def ensure_dir(path):
    try:
        os.mkdir(path)
    except OSError:
        pass

def ensure_dir_recursive(path):
    if not path or path == '/': return
    parts = path.strip('/').split('/')
    cur = ''
    for p in parts:
        cur = (cur + '/' + p) if cur else '/' + p
        try: os.mkdir(cur)
        except OSError: pass

def mount_sd():
    """Compat wrapper to the new SD module; preserves old API."""
    global sd_is_mounted
    ok = bool(MySD.mount_sd_card())
    sd_is_mounted = ok
    return ok

def normalize_to_sd(name):
    if not name:
        name = "measurements.csv"
    n = name.replace('\\', '/')
    if n.startswith(mount_point + '/'):
        n = n[len(mount_point) + 1:]
    if n.startswith('/'):
        n = n[1:]
    return mount_point + '/' + n

def file_exists(path):
    try:
        with open(path, 'r'):
            return True
    except OSError:
        return False

def file_empty(path):
    try:
        return os.stat(path)[6] == 0
    except OSError:
        return True

def create_file(path):
    if not MySD.is_mounted():
        print("Warning: SD not mounted; create_file skipped")
        return False
    parent = '/'.join(path.split('/')[:-1])
    if parent and parent != '/': ensure_dir_recursive(parent)
    try:
        with open(path, 'w'): return True
    except OSError as e:
        print(f"Warning: Unable to create file. {e}"); return False

def write_line(path, line):
    if not MySD.is_mounted():
        print("Warning: SD not mounted; write_line skipped")
        return False
    try:
        with open(path, 'a') as f: f.write(str(line) + '\n'); return True
    except OSError as e:
        print(f"Warning: Unable to write line. {e}"); return False

def write_list(path, lst):
    if not MySD.is_mounted():
        print("Warning: SD not mounted; write_list skipped")
        return False
    try:
        with open(path, 'a') as f: f.write(separator.join(map(str, lst)) + '\n'); return True
    except OSError as e:
        print(f"Warning: Unable to write list. {e}"); return False

def read_lines(path, split=True):
    if not MySD.is_mounted():
        print("Warning: SD not mounted; read_lines skipped")
        return False
    try:
        with open(path, 'r') as f: lines = [s.rstrip('\n') for s in f.readlines()]
        if not split: return lines
        out = []
        for s in lines:
            row = []
            for x in s.split(separator):
                try: row.append(float(x))
                except ValueError: row.append(x)
            out.append(row)
        return out
    except OSError as e:
        print(f"Warning: Unable to read lines. {e}"); return False

def delete_file(name):
    """Delete a file via the new SD module."""
    return bool(MySD.delete(name))

def print_directory(path=mount_point, tabs=0):
    if not MySD.is_mounted():
        print("Warning: SD not mounted; print_directory skipped")
        return
    try: entries = os.listdir(path)
    except OSError as e:
        print(f"Unable to list {path}: {e}"); return
    for name in entries:
        if name == "?": continue
        full = path + "/" + name
        try: st = os.stat(full)
        except OSError: continue
        isdir = bool(st[0] & 0x4000); size = st[6]
        if isdir: sizestr = "<DIR>"
        elif size < 1000: sizestr = f"{size} bytes"
        elif size < 1_000_000: sizestr = f"{size/1000:.1f} KB"
        else: sizestr = f"{size/1_000_000:.1f} MB"
        print(f'{"   "*tabs}{name + ("/" if isdir else ""):<40} Size: {sizestr:>10}')
        if isdir: print_directory(full, tabs + 1)

# ---------------------------------------------------------------------
# Time handling
# ---------------------------------------------------------------------
# Store the last RTC time we used to detect when seconds change
_last_rtc_time = None

def init_timebase():
    global rtc, t0_mono, timebase_ready, _last_rtc_time
    if timebase_ready: return True
    rtc = rtc or MyRTC()
    t0_mono = _time.monotonic()
    _last_rtc_time = rtc.now()
    timebase_ready = True
    return True

def timestamp(fmt='iso', with_ms=True):
    global _last_rtc_time
    
    if not timebase_ready: init_timebase()
    
    # Get current time from both sources
    t = rtc.now()
    mono_now = _time.monotonic()
    
    # Check if RTC seconds have changed since last call
    seconds_changed = False
    if _last_rtc_time is not None:
        if t.tm_sec != _last_rtc_time.tm_sec:
            seconds_changed = True
    _last_rtc_time = t
    
    # If seconds changed, reset our monotonic reference to avoid backward milliseconds
    if seconds_changed:
        t0_mono = mono_now
    
    if fmt == 'iso':
        base = f"{t.tm_year:04d}-{t.tm_mon:02d}-{t.tm_mday:02d} {t.tm_hour:02d}:{t.tm_min:02d}:{t.tm_sec:02d}"
    elif fmt == 'dt':
        days = ("Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday")
        base = f"{days[t.tm_wday]} {t.tm_mday}/{t.tm_mon}/{t.tm_year} {t.tm_hour:02d}:{t.tm_min:02d}:{t.tm_sec:02d}"
    elif fmt == 'epoch':
        try: base = str(int(_time.mktime(t)))
        except Exception: base = f"{t.tm_year:04d}-{t.tm_mon:02d}-{t.tm_mday:02d} {t.tm_hour:02d}:{t.tm_min:02d}:{t.tm_sec:02d}"
    else:
        base = f"{t.tm_year:04d}-{t.tm_mon:02d}-{t.tm_mday:02d} {t.tm_hour:02d}:{t.tm_min:02d}:{t.tm_sec:02d}"
    
    if with_ms:
        # Calculate milliseconds since the last RTC second boundary
        # This ensures milliseconds are always increasing and don't go backward
        time_since_reset = mono_now - t0_mono
        # Handle potential monotonic time wrap-around (though unlikely in CircuitPython)
        if time_since_reset < 0:
            # If monotonic time wrapped around, reset our reference
            t0_mono = mono_now
            frac_ms = 0
        else:
            frac_ms = int(time_since_reset * 1000) % 1000
        return f"{base}.{frac_ms:03d}"
    return base

# ---------------------------------------------------------------------
# MyStore class
# ---------------------------------------------------------------------
class MyStore:
    """Logs time-stamped rows (CSV-like text format) to SD card."""

    def __init__(self, filename, fmt='iso', with_ms=True, auto_header=None, time_label="time"):
        mount_sd()
        self.file_name = filename
        self.file_path = normalize_to_sd(filename)
        self.fmt = fmt; self.with_ms = with_ms
        if MySD.is_mounted() and not file_exists(self.file_path): create_file(self.file_path)
        if auto_header: self.header(auto_header, label=time_label)

    def empty(self):
        if not MySD.is_mounted(): return False
        return create_file(self.file_path)

    def header(self, cols, label="time"):
        if cols is None or not MySD.is_mounted(): return
        if not file_empty(self.file_path): return
        row = ([label] + list(cols)) if isinstance(cols, (list,tuple)) else [label, str(cols)]
        return write_list(self.file_path, row)

    def add(self, data):
        if not MySD.is_mounted(): return False
        ts = timestamp(self.fmt, self.with_ms)
        row = list(data) if isinstance(data, (list,tuple)) else [data]
        return write_list(self.file_path, [ts] + row)

    def read(self, split=True):
        if not MySD.is_mounted(): return False
        return read_lines(self.file_path, split=split)

    def iter_lines(self, split=True):
        """Yield one line at a time (optionally split)."""
        if not MySD.is_mounted():
            print("Warning: SD not mounted; iter_lines skipped")
            return
        try:
            with open(self.file_path, 'r') as f:
                for line in f:
                    line = line.rstrip('\n')
                    if not split:
                        yield line
                    else:
                        parts = []
                        for x in line.split(separator):
                            try: parts.append(float(x))
                            except ValueError: parts.append(x)
                        yield parts
        except OSError as e:
            print(f"Warning: Unable to iterate lines. {e}")
            return
