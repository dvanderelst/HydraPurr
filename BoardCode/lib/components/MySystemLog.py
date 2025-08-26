# lib/components/MySystemLog.py
# Minimal logger: prefer SD (/sd), else console. Requires components.MyStore.mount_sd()

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
_log_path = None  # actual file path in use

# small in-memory ring buffer so you can read logs during runtime
_mem_buf = []
_mem_max = 500  # number of recent lines to keep

# ---------------- basics ----------------

def set_time_fn(fn):
    """Provide a function that returns a timestamp string (e.g., rtc.get_time(as_string=True))."""
    global _time_fn
    _time_fn = fn

def _ts():
    if _time_fn:
        try:
            return _time_fn()
        except:
            pass
    try:
        import supervisor
        return f"{int(supervisor.ticks_ms()/1000)}s"
    except:
        return "0s"

def set_level(level):
    """Set minimum level to emit: DEBUG, INFO, WARN, ERROR."""
    global _level
    _level = int(level)

def get_level():
    return _level

def set_mirror_to_console(flag):
    global _mirror_to_console
    _mirror_to_console = bool(flag)

def set_mem_max(n):
    global _mem_max
    try:
        _mem_max = int(n)
    except:
        pass

def _fmt(level_name, msg):
    return f"[{_ts()}] {level_name}: {msg}"

def _emit(line):
    global _mem_buf
    if _sink:
        try:
            _sink(line)
        except:
            pass
    # keep a RAM mirror for quick access
    try:
        _mem_buf.append(line)
        if len(_mem_buf) > _mem_max:
            _mem_buf.pop(0)
    except:
        pass

# joiner that behaves like print(*parts)
_def_join = lambda parts: " ".join(str(p) for p in parts)

# ---- public logging API (varargs) ----

def debug(*parts):
    if _level <= DEBUG:
        _emit(_fmt("DEBUG\t", _def_join(parts)))

def info(*parts):
    if _level <= INFO:
        _emit(_fmt("INFO\t", _def_join(parts)))

def warn(*parts):
    if _level <= WARN:
        _emit(_fmt("WARN\t", _def_join(parts)))

def error(*parts):
    if _level <= ERROR:
        _emit(_fmt("ERROR\t", _def_join(parts)))

def critical(*parts):
    msg = _def_join(parts)
    error(msg)
    raise RuntimeError(msg)

# Optional printf-style helpers

def infof(fmt, *args):
    try:
        info(fmt % args)
    except Exception:
        info(fmt, *args)

def debugf(fmt, *args):
    try:
        debug(fmt % args)
    except Exception:
        debug(fmt, *args)

def warnf(fmt, *args):
    try:
        warn(fmt % args)
    except Exception:
        warn(fmt, *args)

def errorf(fmt, *args):
    try:
        error(fmt % args)
    except Exception:
        error(fmt, *args)

# ---------------- sinks ----------------

class _PrintSink:
    def __call__(self, line):
        print(line)

    def flush(self):
        try:
            import sys
            sys.stdout.flush()
        except:
            pass

class _SDSink:
    def __init__(self, path="/sd/system.log", autosync=False, keep_open=True):
        self.path = path
        self.autosync = autosync
        self.keep_open = keep_open
        self._fh = open(self.path, "a") if keep_open else None

    def __call__(self, line):
        try:
            if self.keep_open:
                self._fh.write(line + "\n")
                if self.autosync:
                    try:
                        self._fh.flush()
                        import os
                        try:
                            os.sync()
                        except:
                            pass
                    except:
                        pass
            else:
                with open(self.path, "a") as f:
                    f.write(line + "\n")
                    if self.autosync:
                        try:
                            f.flush()
                            import os
                            try:
                                os.sync()
                            except:
                                pass
                        except:
                            pass
        except Exception as e:
            try:
                print("[MySystemLog] SD write failed:", repr(e))
            except:
                pass

    def flush(self):
        if self.keep_open and self._fh:
            try:
                self._fh.flush()
                import os
                try:
                    os.sync()
                except:
                    pass
            except:
                pass

    def close(self):
        try:
            if self._fh:
                self._fh.flush()
                self._fh.close()
        except:
            pass
        self._fh = None

class _TeeSink:
    def __init__(self, *sinks):
        self.sinks = list(sinks)
    def __call__(self, line):
        for s in self.sinks:
            try:
                s(line)
            except:
                pass
    def flush(self):
        for s in self.sinks:
            if hasattr(s, "flush"):
                try:
                    s.flush()
                except:
                    pass
    def close(self):
        for s in self.sinks:
            if hasattr(s, "close"):
                try:
                    s.close()
                except:
                    pass

# ---------------- setup / teardown ----------------

def setup(filename="system.log", autosync=True, keep_open=True):
    """Initialize logging. Returns True if logging to SD, else False (console-only)."""
    global _sink, _sd_ok, _log_path
    from components.MyStore import mount_sd
    _sd_ok = bool(mount_sd())

    # Determine path (absolute vs relative to mount point)
    if filename.startswith("/"):
        path = filename
    else:
        path = f"{_mount_point.rstrip('/')}/{filename}"

    if _sd_ok:
        _log_path = path
        try:
            sd_sink = _SDSink(path, autosync=autosync, keep_open=keep_open)
            if _mirror_to_console:
                _sink = _TeeSink(sd_sink, _PrintSink())
            else:
                _sink = sd_sink
            info("[MySystemLog] Logging to SD:", path)
            return True
        except Exception as e:
            print("[MySystemLog] SD sink init failed:", repr(e))

    # fallback to console
    _log_path = None
    _sink = _PrintSink()
    info("[MySystemLog] SD not available → console-only")
    return False

def flush():
    """Force a flush to SD if possible."""
    try:
        obj = _sink
        if hasattr(obj, "flush"):
            obj.flush()
    except:
        pass

def teardown():
    """Close SD sink (if open)."""
    global _sink
    try:
        obj = _sink
        if hasattr(obj, "close"):
            obj.close()
    except:
        pass

# ---------------- utilities: clear / read / tail / snapshot ----------------

def clear_system_log():
    """Erase the system log file if using SD; recreate sink after clearing."""
    global _sink, _sd_ok, _log_path
    if not _sd_ok or not _log_path:
        print("[MySystemLog] No SD log to clear")
        return False
    # best effort: close file handle before truncating
    try:
        obj = _sink
        if hasattr(obj, "close"):
            obj.close()
    except:
        pass
    try:
        with open(_log_path, "w") as f:
            f.write("")
        print("[MySystemLog] System log cleared")
        # re-setup with same filename
        setup(_log_path.split("/")[-1], autosync=True, keep_open=True)
        return True
    except Exception as e:
        print("[MySystemLog] Clear failed:", repr(e))
        return False

def _resolve_path(default_name="system.log"):
    if _log_path:
        return _log_path
    return f"{_mount_point.rstrip('/')}/{default_name}"

def read_log(last_n=None):
    """
    Return log lines as list[str]. If last_n is set, return only the last N lines.
    Falls back to the in-memory buffer if file not accessible.
    """
    try:
        flush()
    except:
        pass
    path = _resolve_path()
    try:
        with open(path, "r") as f:
            lines = [s.rstrip("\n") for s in f.readlines()]
        return lines[-last_n:] if (last_n and last_n > 0) else lines
    except Exception:
        return _mem_buf[-last_n:] if (last_n and last_n > 0) else list(_mem_buf)

def tail(n=100):
    """Shorthand for last N lines."""
    return read_log(last_n=n)

def tail_to_console(n=100, prefix="> "):
    """Print the last N lines to console immediately."""
    lines = tail(n)
    for ln in lines:
        try:
            print(prefix + ln)
        except:
            pass
    return len(lines)

def snapshot_log(to_path=None, last_n=None):
    """
    Write a snapshot of the log to a file (default: /sd/system.snapshot.log).
    Returns number of lines written. Uses memory buffer if SD not available.
    """
    lines = read_log(last_n=last_n)
    if to_path is None:
        to_path = f"{_mount_point.rstrip('/')}/system.snapshot.log"
    try:
        with open(to_path, "w") as f:
            for ln in lines:
                f.write(ln + "\n")
        return len(lines)
    except Exception:
        # couldn't write snapshot; still return how many lines we had
        return len(lines)

def get_memory_log(last_n=None):
    """Return only the in-memory buffer (ignores file)."""
    return _mem_buf[-last_n:] if (last_n and last_n > 0) else list(_mem_buf)

def sd_available():
    return _sd_ok

