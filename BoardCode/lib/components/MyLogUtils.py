# lib/components/LogUtils.py
# Lightweight logger with pluggable sinks (console, file) and an in-RAM ring buffer.

# ---- levels ----
DEBUG = 10
INFO  = 20
WARN  = 30
ERROR = 40

_level = INFO
_sinks = []              # list of callables: sink(line: str) -> None
_BUFFER_MAX = 200        # tune to your RAM budget
_buffer = []             # ring buffer
_time_string_provider = None  # optional fn() -> str for timestamps (e.g., RTC)

# ---------- core ----------
def set_level(level: int):
    global _level
    _level = int(level)

def set_time_string_provider(fn):  # fn: () -> str
    """Optionally supply a function that returns a timestamp string."""
    global _time_string_provider
    _time_string_provider = fn

def _ts():
    if _time_string_provider:
        try:
            return _time_string_provider()
        except Exception:
            pass
    # fallback: seconds since boot (supervisor present on CircuitPython)
    try:
        import supervisor
        return f"{int(supervisor.ticks_ms()/1000)}s"
    except Exception:
        return "0s"

def _fmt(level_name: str, msg: str) -> str:
    return f"[{_ts()}] {level_name}: {msg}"

def _push(line: str):
    if len(_buffer) >= _BUFFER_MAX:
        _buffer.pop(0)
    _buffer.append(line)

def attach_sink(sink_callable, flush_buffer=True):
    """sink_callable(line:str) -> None"""
    if sink_callable not in _sinks:
        _sinks.append(sink_callable)
        if flush_buffer:
            for ln in _buffer:
                try: sink_callable(ln)
                except Exception: pass

def detach_sink(sink_callable):
    if sink_callable in _sinks:
        _sinks.remove(sink_callable)

def clear():
    """Clear RAM buffer and ask file sinks to clear if they implement .clear()."""
    _buffer.clear()
    for s in _sinks:
        try: s.clear()
        except Exception: pass

def _emit(line: str):
    _push(line)
    for s in _sinks:
        try: s(line)
        except Exception: pass

# ---------- API ----------
def debug(msg: str):
    if _level <= DEBUG: _emit(_fmt("DEBUG", str(msg)))

def info(msg: str):
    if _level <= INFO: _emit(_fmt("INFO", str(msg)))

def warn(msg: str):
    if _level <= WARN: _emit(_fmt("WARN", str(msg)))

def error(msg: str):
    if _level <= ERROR: _emit(_fmt("ERROR", str(msg)))

def dump_buffer() -> list:
    """Return a copy of the current in-RAM log buffer."""
    return list(_buffer)

# ---------- sinks ----------
class PrintSink:
    def __call__(self, line: str):
        print(line)

class FileSink:
    """
    Append-only file sink. Tries /sd first, then falls back to internal flash.
    Consider autosync=False if you log very frequently to reduce wear.
    """
    def __init__(self, path="/sd/system.log", fallback="/log.txt", autosync=True):
        self.path = None
        self.autosync = autosync
        for p in (path, fallback):
            try:
                with open(p, "a") as f:
                    f.write("")  # touch
                self.path = p
                break
            except OSError:
                continue

    def __call__(self, line: str):
        if not self.path: return
        try:
            with open(self.path, "a") as f:
                f.write(line + "\n")
            if self.autosync:
                try:
                    import os
                    os.sync()
                except Exception:
                    pass
        except OSError:
            pass

    def clear(self):
        if not self.path: return
        try:
            with open(self.path, "w") as f:
                f.write("")
            try:
                import os
                os.sync()
            except Exception:
                pass
        except OSError:
            pass
