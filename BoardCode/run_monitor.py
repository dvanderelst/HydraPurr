import time
import Cats

from components.MySystemLog import setup, set_level, DEBUG, INFO, WARN, ERROR
from components.MySystemLog import clear_system_log
from components.MySystemLog import debug, info, warn, error
from components.MyPixel import MyPixel

from LickCounter import LickCounter
from TagReader import TagReader     # new non-blocking, scheduled-reset version
from HydraPurr import HydraPurr

def now_ms(): return int(time.monotonic() * 1000)

# ---------------- config ----------------
TAG_REQUIRED     = True   # gatekeeper mode; False = logger mode
ALLOW_UNKNOWN    = False  # allow unknown tags to open gate
HOLD_MS          = 3000   # presence window after last RFID hit
LOCK_RELEASE_MS  = 2000   # require quiet gap before switching cats
# ----------------------------------------

# Get all cats (by name) and build per-name counters
all_cat_names = Cats.get_all_names()

# Logging
setup(filename="system.log", autosync=True)
clear_system_log()
set_level(INFO)
info("[Run] Start")

# Hardware / objects
reader = TagReader()          # resets are handled inside; poll() never sleeps
hydrapurr = HydraPurr()
pixel = MyPixel()

lickcounters = {name: LickCounter(name=name) for name in all_cat_names}
if not TAG_REQUIRED:
    lickcounters.setdefault("unknown", LickCounter(name="unknown"))

info(f'[Monitor] all defined cats: {all_cat_names}')

# pixel control
pixel.toggle_colors = ['red', 'green', 'blue']
last_toggle = now_ms()
# Presence/attribution state
active_tag = None
active_name = None
last_seen_ms = 0

previous_ctr_state = None


while True:
    t_ms = now_ms()
    
    # --- Swap color of NEO pixel every xx seconds
    elapsed_time = t_ms - last_toggle
    if elapsed_time > 500:
        pixel.cycle()
        hydrapurr.indicator_toggle()
        last_toggle = t_ms
        
    # --- RFID: non-blocking poll; updates presence on edges only ---
    pkt = reader.poll()  # returns None or a dict with "tag_key"/"tag"
    if pkt:
        tag = pkt.get("tag_key")
        if tag:
            # Map to a name (or decide if unknown is allowed)
            name = Cats.get_name(tag)
            if (name is None) and not ALLOW_UNKNOWN:
                # Unknown -> ignore in gatekeeper; in logger mode you could use "unknown"
                pass
            else:
                # Lock-to-first: switch only if we've been quiet for LOCK_RELEASE_MS
                if active_tag is None:
                    active_tag = tag
                    active_name = name
                    last_seen_ms = t_ms
                    info(f"[Monitor] Activating {active_name or 'unknown'}")
                elif tag == active_tag:
                    # same cat: refresh presence
                    last_seen_ms = t_ms
                else:
                    # different tag arrived
                    quiet_ms = t_ms - last_seen_ms
                    if quiet_ms >= LOCK_RELEASE_MS:
                        info(f"[Monitor] Switch {active_name or 'unknown'} → {name or 'unknown'}")
                        active_tag = tag
                        active_name = name
                        last_seen_ms = t_ms
                    else:
                        # conflict within lock window; ignore the new tag
                        warn("[Monitor] tag conflict ignored (within lock window)")

    # Presence gate (stays on for HOLD_MS after last hit)
    # Consider a cat present iff (1) we currently have an active tag, and (2) the last RFID hit was not longer ago than HOLD_MS milliseconds.
    gate_on = (active_tag is not None) and ((t_ms - last_seen_ms) <= HOLD_MS)

    # If presence fully expired, cleanly deactivate and ensure a trailing 0 goes to the last counter
    if (active_tag is not None) and not gate_on:
        if TAG_REQUIRED and (active_name is not None):
            # ensure the active counter sees a '0' to close any ongoing lick cleanly
            try:
                lickcounters[active_name].process_sample(0)
            except KeyError:
                pass
        info(f"[Monitor] Deactivating {active_name or 'unknown'}")
        # write the screen when the cat gets deactivated - to avoid using to much screen update time
        hydrapurr.write_line(0, f"{active_name}")
        hydrapurr.write_line(1, f"B:{ctr.bout_count}")
        
        active_tag = None
        active_name = None

    # --- Lick sampling (fast; never blocked by RFID) ---
    lick_state = 1 if hydrapurr.read_lick(binary=True) else 0

    if TAG_REQUIRED:
        # Gatekeeper: only route samples when a cat is present
        if active_name is not None and gate_on:
            ctr = lickcounters.get(active_name)
            if ctr:
                ctr.process_sample(lick_state)
                current_ctr_state = ctr.get_state()
                if previous_ctr_state != current_ctr_state:
                    info(f'[Monitor] current counter state {current_ctr_state}')
                    previous_ctr_state = current_ctr_state
        else:
            # No active cat: you can optionally feed a 0 to all counters or do nothing.
            # Doing nothing keeps per-cat counters quiet between sessions.
            pass
    else:
        # Logger mode: count always; stamp by current/unknown
        name = active_name if gate_on and (active_name is not None) else "unknown"
        ctr = lickcounters.setdefault(name, LickCounter(name=name))
        ctr.process_sample(lick_state)
        current_ctr_state = ctr.get_state()
        if previous_ctr_state != current_ctr_state:
            info(f'[Monitor] current counter state {current_ctr_state}')
            previous_ctr_state = current_ctr_state
