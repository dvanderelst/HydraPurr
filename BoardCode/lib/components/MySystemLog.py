# lib/components/MySystemLog.py
# Minimal logger: prefer SD (/sd), else console.

DEBUG = 10
INFO  = 20
WARN  = 30
ERROR = 40

_level = INFO
_sink = None
_time_fn = None
_sd_ok = False
_mirror_to_console = True
_mount_point = "/sd"
_log_path = None  # track the actual file we’re logging to

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
        self._fh = open(self.path, "a") if keep_open else None

    def __call__(self, line):
        try:
            if self.keep_open:
                # Write to the persistent handle
                self._fh.write(line + "\n")
                if self.autosync:
                    try:
                        self._fh.flush()
                        import os
                        try: os.sync()
                        except: pass
                    except: pass
            else:
                # Open/append/flush/close per write
                with open(self.path, "a") as f:
                    f.write(line + "\n")
                    if self.autosync:
                        try:
                            f.flush()
                            import os
                            try: os.sync()
                            except: pass
                        except: pass
        except Exception as e:
            try: print("[MySystemLog] SD write failed:", repr(e))
            except: pass

    def flush(self):
        if self.keep_open and self._fh:
            try:
                self._fh.flush()
                import os
                try: os.sync()
                except: pass
            except: pass

    def close(self):
        try:
            if self._fh:
                self._fh.flush()
                self._fh.close()
        except: pass
        self._fh = None

def setup(filename="system.log", autosync=True, keep_open=True):
    """Initialize logging. Returns True if logging to SD, else False (console-only)."""
    global _sink, _sd_ok, _log_path
    from components.MyStore import mount_sd
    _sd_ok = bool(mount_sd())
    if _sd_ok:
        path = f"{_mount_point.rstrip('/')}/{filename}"
        _log_path = path
        try:
            sd_sink = _SDSink(path, autosync=autosync, keep_open=keep_open)
            if _mirror_to_console:
                ps = _PrintSink()
                _sink = lambda line, a=sd_sink, b=ps: (a(line), b(line))
            else:
                _sink = sd_sink
            info(f"[MySystemLog] Logging to SD: {path}")
            return True
        except Exception as e:
            print("[MySystemLog] SD sink init failed:", repr(e))
    # Fallback to console
    _log_path = None
    _sink = _PrintSink()
    info("[MySystemLog] SD not available → console-only")
    return False

def clear_system_log():
    """Erase the system log file if using SD, else no-op."""
    global _sink, _sd_ok, _log_path
    if not _sd_ok or not _log_path:
        print("[MySystemLog] No SD log to clear")
        return False
    # If we’re keeping the file open, close it before truncating
    try:
        # If _sink is a tee (lambda), it returns a tuple; get the SD sink if so
        sd_sink = None
        if callable(_sink) and hasattr(_sink, "__name__") and _sink.__name__ == "<lambda>":
            # We can't introspect closures easily; just try to truncate directly.
            pass
        else:
            sd_sink = _sink
        if hasattr(sd_sink, "close"):
            sd_sink.close()
    except: pass
    try:
        with open(_log_path, "w") as f:
            f.write("")
        print("[MySystemLog] System log cleared")
        # Recreate sink after clearing
        setup(_log_path.split("/")[-1], autosync=True, keep_open=True)
        return True
    except Exception as e:
        print("[MySystemLog] Clear failed:", repr(e))
        return False

def flush():
    """Force a flush to SD if possible."""
    try:
        # If _sink is our tee lambda, calling emits does nothing; try to reach underlying
        obj = _sink
        if hasattr(obj, "flush"):
            obj.flush()
    except: pass

def teardown():
    """Close SD sink (if open)."""
    global _sink
    try:
        obj = _sink
        if hasattr(obj, "close"):
            obj.close()
    except: pass

def sd_available(): return _sd_ok
