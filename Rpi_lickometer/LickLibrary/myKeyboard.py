import evdev
from evdev import InputDevice, categorize, ecodes


def print_devices():
    msg = 'If you do not see any devices, ensure that your user is in the correct group (typically input) to have read/write access.'
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    if len(devices) == 0: print(msg)
    for device in devices: print(device.path, device.name, device.phys)


def is_key_pressed(device_path, keycode=None):
    if keycode is None: keycode = ecodes.KEY_A
    dev = InputDevice(device_path)
    return keycode in dev.active_keys()
