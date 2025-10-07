#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Simple script to list serial ports across platforms

from serial.tools import list_ports

print("🔍 Detected serial ports:\n")

ports = list_ports.comports()
if not ports:
    print("No serial ports found.")
else:
    for p in ports:
        print(f"Device: {p.device}")
        print(f"  Description: {p.description}")
        print(f"  HWID: {p.hwid}")
        print(f"  Manufacturer: {p.manufacturer}")
        print(f"  VID:PID: {p.vid}:{p.pid}")
        print(f"  Location: {p.location}")
        print(f"  Serial Number: {p.serial_number}")
        print("-" * 50)
