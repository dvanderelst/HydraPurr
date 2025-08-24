# MyStore.py
import os, time as _time, board, sdcardio, storage
from components.MyRTC import MyRTC


path_separator = os.sep
separator = ','
mount_point = '/sd'
sd_is_mounted = False
rtc = None            # shared RTC instance
t0_mono = None        # baseline monotonic at init
timebase_ready = False

def ensure_dir(path): 
    try: os.mkdir(path)
    except OSError: pass

def ensure_dir_recursive(path):
    if not path or path == '/': return
    parts = path.strip('/').split('/')
    cur = ''
    for p in parts:
        cur = (cur + '/' + p) if cur else '/' + p
        try: os.mkdir(cur)
        except OSError: pass

def mount_sd():
    global sd_is_mounted
    if sd_is_mounted: return True
    try:
        storage.getmount(mount_point); sd_is_mounted = True; return True
    except Exception: pass
    ensure_dir(mount_point)
    spi = board.SPI(); cs = board.D10
    sdcard = sdcardio.SDCard(spi, cs)
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, mount_point)
    sd_is_mounted = True
    return True

def normalize_to_sd(name):
    if not name: name = "measurements.csv"
    n = name.replace('\\', '/')
    if n.startswith(mount_point + '/'): n = n[len(mount_point) + 1:]
    if n.startswith('/'): n = n[1:]
    return mount_point + '/' + n

def file_exists(path):
    try:
        with open(path, 'r'): return True
    except OSError: return False

def file_empty(path):
    try: return os.stat(path)[6] == 0
    except OSError: return True

def create_file(path):
    parent = '/'.join(path.split('/')[:-1])
    if parent and parent != '/': ensure_dir_recursive(parent)
    try:
        with open(path, 'w'): return True
    except OSError as e:
        print(f"Warning: Unable to create file. {e}"); return False

def write_line(path, line):
    try:
        with open(path, 'a') as f: f.write(str(line) + '\n'); return True
    except OSError as e:
        print(f"Warning: Unable to write line. {e}"); return False

def write_list(path, lst):
    try:
        with open(path, 'a') as f: f.write(separator.join(map(str, lst)) + '\n'); return True
    except OSError as e:
        print(f"Warning: Unable to write list. {e}"); return False

def read_lines(path, split=True):
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

def init_timebase():
    # One-time setup of RTC and monotonic baseline
    global rtc, t0_mono, timebase_ready
    if timebase_ready: return True
    rtc = rtc or MyRTC()
    t0_mono = _time.monotonic()
    timebase_ready = True
    return True

def timestamp(fmt='iso', with_ms=True):
    # Hybrid timestamp: RTC for wall time + monotonic for sub-second
    if not timebase_ready: init_timebase()
    t = rtc.now()
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
        frac_ms = int((_time.monotonic() - t0_mono) * 1000) % 1000
        return f"{base}.{frac_ms:03d}"
    return base


def print_directory(path=mount_point, tabs=0):
    # Pretty-print a directory tree (sizes are approximate)
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



class MyStore:
    def __init__(self, file_name="measurements.csv", fmt='iso', with_ms=True, auto_header=None, time_label="time"):
        # Mount, path, and time settings
        mount_sd()
        self.file_name = file_name
        self.file_path = normalize_to_sd(file_name)
        self.fmt = fmt; self.with_ms = with_ms
        if not file_exists(self.file_path): create_file(self.file_path)
        if auto_header: self.header(auto_header, label=time_label)

    def empty(self):
        return create_file(self.file_path)

    def header(self, cols, label="time"):
        if cols is None: return
        if not file_empty(self.file_path): return
        row = ([label] + list(cols)) if isinstance(cols, (list,tuple)) else [label, str(cols)]
        return write_list(self.file_path, row)

    def add(self, data):
        # Prepend hybrid timestamp to row
        ts = timestamp(self.fmt, self.with_ms)
        row = list(data) if isinstance(data, (list,tuple)) else [data]
        return write_list(self.file_path, [ts] + row)

    def read(self, split=True):
        return read_lines(self.file_path, split=split)
