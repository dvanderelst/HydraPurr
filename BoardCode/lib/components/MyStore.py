import os
import board
import sdcardio
import storage

path_separator = os.sep
separator = ','
mount_point = '/sd'

# simple module-level guard
SD_IS_MOUNTED = False

def ensure_dir(path):
    try:
        os.mkdir(path)
    except OSError:
        pass  # already exists

def mount_sd():
    """Mount /sd exactly once; safe to call repeatedly."""
    global SD_IS_MOUNTED
    if SD_IS_MOUNTED:
        return True

    # If CircuitPython already has it mounted, remember that and bail out.
    try:
        storage.getmount(mount_point)  # raises if not mounted
        SD_IS_MOUNTED = True
        return True
    except Exception:
        pass

    ensure_dir(mount_point)

    # Only create the SD objects if we truly need to mount now
    spi = board.SPI()
    cs = board.D10
    sdcard = sdcardio.SDCard(spi, cs)
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, mount_point)  # readonly=False by default for VfsFat
    SD_IS_MOUNTED = True
    return True

def print_directory(path, tabs=0):
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
        isdir = bool(st[0] & 0x4000)
        size = st[6]
        if isdir:
            sizestr = "<DIR>"
        elif size < 1000:
            sizestr = f"{size} bytes"
        elif size < 1_000_000:
            sizestr = f"{size/1000:.1f} KB"
        else:
            sizestr = f"{size/1_000_000:.1f} MB"
        print(f'{"   "*tabs}{name + ("/" if isdir else ""):<40} Size: {sizestr:>10}')
        if isdir:
            print_directory(full, tabs + 1)

def file_exists(path):
    try:
        with open(path, 'r'):
            return True
    except OSError:
        return False

def create_file(path):
    try:
        with open(path, 'w'):
            return True
    except OSError as e:
        print(f"Warning: Unable to create file, filesystem may be read-only. {e}")
        return False

def write_line(path, line):
    try:
        with open(path, 'a') as f:
            f.write(str(line) + '\n')
        return True
    except OSError as e:
        print(f"Warning: Unable to write line. {e}")
        return False

def write_list(path, lst):
    try:
        with open(path, 'a') as f:
            f.write(separator.join(map(str, lst)) + '\n')
        return True
    except OSError as e:
        print(f"Warning: Unable to write list. {e}")
        return False

def read_lines(path, split=True):
    try:
        with open(path, 'r') as f:
            lines = [s.rstrip('\n') for s in f.readlines()]
        if split:
            out = []
            for s in lines:
                row = []
                for x in s.split(separator):
                    try:
                        row.append(float(x))
                    except ValueError:
                        row.append(x)
                out.append(row)
            return out
        return lines
    except OSError as e:
        print(f"Warning: Unable to read lines. {e}")
        return False

class MyStore:
    def __init__(self, file_name="measurements.csv"):
        mount_sd()
        self.file_name = file_name
        self.file_path = mount_point + path_separator + file_name
        if not file_exists(self.file_path): create_file(self.file_path)

    def empty(self):
        return create_file(self.file_path)

    def add(self, data):
        if isinstance(data, (list, tuple)):
            return write_list(self.file_path, data)
        return write_line(self.file_path, data)

    def read(self):
        return read_lines(self.file_path)
    

# Example:
# ms = MyStore()
#ms.add([1, 2, 3])
# print_directory()
