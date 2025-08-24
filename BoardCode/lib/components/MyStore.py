# MyStore.py
import os, board, sdcardio, storage

path_separator = os.sep
separator = ','
mount_point = '/sd'
sd_is_mounted = False

def ensure_dir(path):
    # Create a single directory if missing
    try: os.mkdir(path)
    except OSError: pass

def ensure_dir_recursive(path):
    # Create nested directories under root, e.g., /sd/logs/licks
    if not path or path == '/': return
    parts = path.strip('/').split('/')
    cur = ''
    for p in parts:
        cur = (cur + '/' + p) if cur else '/' + p
        try: os.mkdir(cur)
        except OSError: pass

def mount_sd():
    # Mount /sd exactly once; safe to call repeatedly
    global sd_is_mounted
    if sd_is_mounted: return True
    try:
        storage.getmount(mount_point)  # already mounted by CP
        sd_is_mounted = True; return True
    except Exception: pass
    ensure_dir(mount_point)
    spi = board.SPI(); cs = board.D10
    sdcard = sdcardio.SDCard(spi, cs)
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, mount_point)
    sd_is_mounted = True
    return True

def normalize_to_sd(name):
    # Always return absolute path under /sd
    if not name: name = "measurements.csv"
    n = name.replace('\\', '/')
    if n.startswith(mount_point + '/'): n = n[len(mount_point) + 1:]
    if n.startswith('/'): n = n[1:]
    return mount_point + '/' + n

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
        sizestr = "<DIR>" if isdir else (f"{size} bytes" if size < 1000 else (f"{size/1000:.1f} KB" if size < 1_000_000 else f"{size/1_000_000:.1f} MB"))
        print(f'{"   "*tabs}{name + ("/" if isdir else ""):<40} Size: {sizestr:>10}')
        if isdir: print_directory(full, tabs + 1)

def file_exists(path):
    # Return True if file can be opened for reading
    try:
        with open(path, 'r'): return True
    except OSError: return False

def create_file(path):
    # Ensure parent dirs exist then create/truncate file
    parent = '/'.join(path.split('/')[:-1])
    if parent and parent != '/': ensure_dir_recursive(parent)
    try:
        with open(path, 'w'): return True
    except OSError as e:
        print(f"Warning: Unable to create file, filesystem may be read-only. {e}"); return False

def write_line(path, line):
    # Append a single line (with newline)
    try:
        with open(path, 'a') as f: f.write(str(line) + '\n'); return True
    except OSError as e:
        print(f"Warning: Unable to write line. {e}"); return False

def write_list(path, lst):
    # Append a CSV row using global separator
    try:
        with open(path, 'a') as f: f.write(separator.join(map(str, lst)) + '\n'); return True
    except OSError as e:
        print(f"Warning: Unable to write list. {e}"); return False

def read_lines(path, split=True):
    # Read file as list of lines; optionally split CSV and auto-cast numbers
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

class MyStore:
    def __init__(self, file_name="measurements.csv"):
        # Always work under /sd and ensure the file exists
        mount_sd()
        self.file_name = file_name
        self.file_path = normalize_to_sd(file_name)
        if not file_exists(self.file_path): create_file(self.file_path)

    def empty(self):
        # Truncate the file (preserves path)
        return create_file(self.file_path)

    def add(self, data):
        # Append data: list/tuple -> CSV row, else raw line
        if isinstance(data, (list, tuple)): return write_list(self.file_path, data)
        return write_line(self.file_path, data)

    def read(self, split=True):
        # Read lines from file (optionally split CSV)
        return read_lines(self.file_path, split=split)
