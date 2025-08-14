import os
import board
import busio
import sdcardio
import storage

# --- constants ---
BASE_PATH = "/sd"
SEP = ","

# --- singleton-ish mount state ---
_spi = None
_cs = board.D10
_mounted = False

def _is_mounted():
    # cheap check: is /sd present at root?
    try:
        return BASE_PATH[1:] in os.listdir("/")
    except Exception:
        return False

def mount_sd():
    global _spi, _mounted
    if _mounted or _is_mounted():
        _mounted = True
        return True
    # init once
    if _spi is None:
        _spi = board.SPI()
    sdcard = sdcardio.SDCard(_spi, _cs)
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, BASE_PATH)
    _mounted = True
    return True

# ---------- small file utils ----------
def file_exists(path):
    try:
        with open(path, "r"):
            return True
    except OSError:
        return False

def create_file(path):
    try:
        with open(path, "w"):
            return True
    except OSError as e:
        print(f"Warning: Unable to create file (read-only FS?) {e}")
        return False

def write_line(path, line):
    try:
        with open(path, "a") as f:
            f.write(str(line) + "\n")
        return True
    except OSError as e:
        print(f"Warning: Unable to write line. {e}")
        return False

def write_list(path, lst):
    try:
        with open(path, "a") as f:
            f.write(SEP.join(map(str, lst)) + "\n")
        return True
    except OSError as e:
        print(f"Warning: Unable to write list. {e}")
        return False

def read_lines(path, split=True):
    try:
        with open(path, "r") as f:
            lines = [s.rstrip("\n") for s in f.readlines()]
        if split:
            def _coerce(x):
                # handles ints/floats incl. negatives, but not scientific notation
                try:
                    return float(x)
                except ValueError:
                    return x
            lines = [[_coerce(x) for x in s.split(SEP)] for s in lines]
        return lines
    except OSError as e:
        print(f"Warning: Unable to read lines. {e}")
        return False

def print_directory(path=BASE_PATH, tabs=0):
    try:
        entries = os.listdir(path)
    except OSError as e:
        print(f"Unable to list {path}: {e}")
        return
    for name in entries:
        if name == "?":
            continue
        full = path + "/" + name
        st = os.stat(full)
        isdir = st[0] & 0x4000
        size = st[6]
        if isdir:
            sizestr = "<DIR>"
        elif size < 1000:
            sizestr = f"{size} bytes"
        elif size < 1_000_000:
            sizestr = f"{size/1000:.1f} KB"
        else:
            sizestr = f"{size/1_000_000:.1f} MB"
        indent = "   " * tabs
        print(f"{indent}{name + ('/' if isdir else ''):<40} Size: {sizestr:>10}")
        if isdir:
            print_directory(full, tabs + 1)


class MyStore:
    def __init__(self, file_name="measurements.csv"):
        mount_sd()  # safe if already mounted
        # ensure absolute path under /sd
        self.file_name = file_name
        self.file_path = BASE_PATH + "/" + file_name
        if not file_exists(self.file_path):
            create_file(self.file_path)

    def erase(self):
        return create_file(self.file_path)

    def add(self, data):
        # data can be a list/tuple; falls back to str if not iterable
        if isinstance(data, (list, tuple)):
            return write_list(self.file_path, data)
        return write_line(self.file_path, data)

    def read(self, split=True):
        return read_lines(self.file_path, split=split)
