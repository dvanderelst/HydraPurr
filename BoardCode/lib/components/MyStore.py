# lib/components/MyStore.py
# Simple CSV-ish store that always writes under /sd, using shared sd_mount

import os

BASE_PATH = "/sd"
SEP = ","

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
        print(f"[MyStore] Unable to create file: {e}")
        return False

def write_line(path, line):
    try:
        with open(path, "a") as f:
            f.write(str(line) + "\n")
        return True
    except OSError as e:
        print(f"[MyStore] Unable to write line: {e}")
        return False

def write_list(path, lst):
    try:
        with open(path, "a") as f:
            f.write(SEP.join(map(str, lst)) + "\n")
        return True
    except OSError as e:
        print(f"[MyStore] Unable to write list: {e}")
        return False

def read_lines(path, split=True):
    try:
        with open(path, "r") as f:
            lines = [s.rstrip("\n") for s in f.readlines()]
        if split:
            def _coerce(x):
                try: return float(x)
                except ValueError: return x
            lines = [[ _coerce(x) for x in s.split(SEP) ] for s in lines]
        return lines
    except OSError as e:
        print(f"[MyStore] Unable to read lines: {e}")
        return False

def print_directory(path=BASE_PATH, tabs=0):
    try:
        entries = os.listdir(path)
    except OSError as e:
        print(f"[MyStore] Unable to list {path}: {e}")
        return
    for name in entries:
        if name == "?": continue
        full = path + "/" + name
        st = os.stat(full)
        isdir = st[0] & 0x4000
        size = st[6]
        sizestr = "<DIR>" if isdir else (
            f"{size} bytes" if size < 1000 else
            f"{size/1000:.1f} KB" if size < 1_000_000 else
            f"{size/1_000_000:.1f} MB"
        )
        indent = "   " * tabs
        print(f"{indent}{name + ('/' if isdir else ''):<40} Size: {sizestr:>10}")
        if isdir:
            print_directory(full, tabs + 1)

class MyStore:
    def __init__(self, file_name="measurements.csv", cs_pin=None, spi=None):
        from components.sd_mount import ensure_mounted
        if not cs_pin:
            raise RuntimeError("MyStore requires cs_pin or a pre-mounted /sd.")
        if not ensure_mounted(cs_pin=cs_pin, spi=spi, mount_point=BASE_PATH):
            raise RuntimeError("SD not available (mount failed).")
        self.file_name = file_name
        self.file_path = BASE_PATH + "/" + file_name
        if not file_exists(self.file_path):
            create_file(self.file_path)
    def erase(self):
        return create_file(self.file_path)
    def add(self, data):
        if isinstance(data, (list, tuple)):
            return write_list(self.file_path, data)
        return write_line(self.file_path, data)
    def read(self, split=True):
        return read_lines(self.file_path, split=split)
