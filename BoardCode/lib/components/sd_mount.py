# lib/components/sd_mount.py

import os, board

# --- constants ---
DEFAULT_CS_PIN = board.D10   # <--- your fixed wiring
DEFAULT_MOUNT_POINT = "/sd"

_spi = None
_mounted = False

def is_mounted():
    """Return True if /sd is already mounted."""
    try:
        return DEFAULT_MOUNT_POINT[1:] in os.listdir("/")
    except Exception:
        return False

def ensure_mounted(spi=None):
    """
    Mount SD card using DEFAULT_CS_PIN.
    Call multiple times safely.
    """
    global _spi, _mounted
    if _mounted or is_mounted():
        _mounted = True
        return True
    try:
        import storage, sdcardio, busio
        if spi is None:
            _spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
        else:
            _spi = spi
        sd = sdcardio.SDCard(_spi, DEFAULT_CS_PIN)
        vfs = storage.VfsFat(sd)
        storage.mount(vfs, DEFAULT_MOUNT_POINT)
        _mounted = True
        return True
    except Exception as e:
        print("[sd_mount] Mount failed:", repr(e))
        _mounted = False
        return False
