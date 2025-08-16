# lib/components/MySystemLog.py
# Minimal logger: prefer SD (/sd), else console. Uses sd_mount.ensure_mounted

DEBUG = 10
INFO  = 20
WARN  = 30
ERROR = 40

_level = INFO
_sink = None
_time_fn = None
_sd_ok = False

def set_time_fn(fn):
    global _time_fn
    _time_fn = fn

def _ts():
    if _time_fn:
        try: return _time_fn()
        except: pass
    try:
        import supervisor
        return f"{int(supervisor.ticks_ms()/1000)}s"
    except:
        return "0s"

def set_level(level):
    global _level
    _level = int(level)

def _fmt(level_name, msg): return f"[{_ts()}] {level_name}: {msg}"

def _emit(line):
    if _sink:
        try: _sink(line)
        except: pass

def debug(msg):
    if _level <= DEBUG: _emit(_fmt("DEBUG", str(msg)))

def info(msg):
    if _level <= INFO: _emit(_fmt("INFO", str(msg)))

def warn(msg):
    if _level <= WARN: _emit(_fmt("WARN", str(msg)))

def error(msg):
    if _level <= ERROR: _emit(_fmt("ERROR", str(msg)))
    
def critical(msg):
    error(msg)
    raise RuntimeError(msg)

class _PrintSink:
    def __call__(self, line): print(line)

class _SDSink:
    def __init__(self, path="/sd/system.log", autosync=False, keep_open=True):
        self.path = path
        self.autosync = autosync
        self.keep_open = keep_open
        self._fh = open(self.path, "a")
        self._fh.write("")
    def __call__(self, line):
        try:
            if self._fh:
                self._fh.write(line + "\n")
            else:
                with open(self.path, "a") as f:
                    f.write(line + "\n")
            if self.autosync:
                try:
                    import os; os.sync()
                except: pass
        except Exception as e:
            try: print("[MySystemLog] SD write failed:", repr(e))
            except: pass
    def close(self):
        try:
            if self._fh:
                self._fh.flush()
                self._fh.close()
        except: pass
        self._fh = None

def setup(filename="system.log", cs_pin=None, spi=None,
          autosync=False, keep_open=True, mount_point="/sd",
          mirror_to_console=False):
    global _sink, _sd_ok
    from components.sd_mount import ensure_mounted
    if cs_pin is None:
        _sd_ok = False
    else:
        _sd_ok = ensure_mounted(cs_pin=cs_pin, spi=spi, mount_point=mount_point)
    if _sd_ok:
        path = f"{mount_point.rstrip('/')}/{filename}"
        try:
            sd_sink = _SDSink(path, autosync=autosync, keep_open=keep_open)
            if mirror_to_console:
                ps = _PrintSink()
                _sink = lambda line, a=sd_sink, b=ps: (a(line), b(line))
            else:
                _sink = sd_sink
            info(f"[MySystemLog] Logging to SD: {path}")
            return True
        except Exception as e:
            print("[MySystemLog] SD sink init failed:", repr(e))
            _sink = _PrintSink()
            info("[MySystemLog] Falling back to console-only")
            return False
    else:
        _sink = _PrintSink()
        info("[MySystemLog] SD not available → console-only")
        return False
    
def clear_system_log():
    """Erase the system log file if using SD, else no-op."""
    global _sink, _sd_ok
    if not _sd_ok:
        print("[MySystemLog] No SD mounted, nothing to clear")
        return False
    try:
        with open("/sd/system.log", "w") as f:
            f.write("")  # overwrite with empty
        print("[MySystemLog] System log cleared")
        return True
    except Exception as e:
        print("[MySystemLog] Clear failed:", repr(e))
        return False

def sd_available(): return _sd_ok
