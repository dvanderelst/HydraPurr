import os
import myStore

import board
import busio
import sdcardio
import storage

spi = board.SPI()
cs = board.D10


path_separator = os.sep
separator = ','
base_path = 'sd'

def print_directory():
    tabs = 0
    for file in os.listdir(base_path):
        if file == "?":
            continue  # Issue noted in Learn
        stats = os.stat(base_path + "/" + file)
        filesize = stats[6]
        isdir = stats[0] & 0x4000

        if filesize < 1000:
            sizestr = str(filesize) + " bytes"
        elif filesize < 1000000:
            sizestr = "%0.1f KB" % (filesize / 1000)
        else:
            sizestr = "%0.1f MB" % (filesize / 1000000)

        prettyprintname = ""
        for _ in range(tabs):
            prettyprintname += "   "
        prettyprintname += file
        if isdir:
            prettyprintname += "/"
        print('{0:<40} Size: {1:>10}'.format(prettyprintname, sizestr))

        # recursively print directory contents
        if isdir:
            print_directory(path + "/" + file, tabs + 1)


def file_exists(path):
    try:
        with open(path, 'r') as f: return True
    except OSError as e:
        return False

def create_file(path):
    try:
        with open(path, 'w') as f: return True
    except OSError as e:
        print(f"Warning: Unable to create file, filesystem may be read-only. {e}")
        return False
    
def write_line(path, line):
    try:
        with open(path, 'a') as f:
            line = str(line)
            f.write(line + '\n')
            return True
    except OSError as e:
        print(f"Warning: Unable to write line. {e}")
        return False

def write_list(path, lst):
    try:
        with open(path, 'a') as f:
            line = separator.join(map(str, lst))
            f.write(line + '\n')
            return True
    except OSError as e:
        print(f"Warning: Unable to write list. {e}")
        return False
    
def read_lines(path, split = True):
    try:
        with open(path, 'r') as f:
            lines = f.readlines()
            # Remove trailing newlines
            lines = [s.rstrip('\n') for s in lines]
            if split:
                # Split and convert numeric entries
                lines = [[float(x) if x.replace('.', '', 1).isdigit() else x for x in s.split(separator)] for s in lines]
            return lines
    except OSError as e:
        print(f"Warning: Unable to read lines. {e}")
        return False
    
    
class myStore:
    def __init__(self, file_name="measurements.csv"):
        self.mount_SD()
        self.file_name = file_name
        self.file_path = base_path + path_separator + file_name
        exists = file_exists(self.file_path)
        if not exists: create_file(self.file_path)
    
    def mount_SD(self):
        sdcard = sdcardio.SDCard(spi, cs)
        vfs = storage.VfsFat(sdcard)
        storage.mount(vfs, "/sd")
    
    def erase(self):
        result = create_file(self.file_path)
        return result
        
    def add(self, data):
        result = write_list(self.file_path, data)
        return result
    
    def read(self):
        result = read_lines(self.file_path)
        return result
        
        
    
        
        
        
        
        
        
        
        
        
        
        
        
        
        