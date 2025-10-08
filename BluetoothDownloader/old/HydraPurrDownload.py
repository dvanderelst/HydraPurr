#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# HydraPurr Desktop GUI (Tkinter) — with pyserial backend wired up
# Cross-platform: Windows / macOS / Linux
#
# Features:
# - Port picker with Refresh
# - Connect / Disconnect
# - Command entry + Send (auto-append '*' and optional CRLF)
# - Live RX log (non-blocking .after() poll)
# - Save / Clear log
#
# Notes:
# - For Linux Bluetooth SPP: create /dev/rfcommN after pairing (e.g. `sudo rfcomm bind 0 <MAC> 1`)
# - For Linux serial permissions: add your user to 'dialout' (e.g. `sudo usermod -a -G dialout $USER` then re-login)

import os
import sys
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from serial.tools import list_ports
import serial

APP_TITLE = "HydraPurr Control"
POLL_MS   = 150   # UI poll interval for incoming data (ms)

# ---------- helpers ----------

def _is_visible_port(p):
    """Filter to show meaningful ports per OS."""
    dev  = (p.device or "").lower()
    desc = (p.description or "").lower()

    # Common serial keywords
    good_keywords = [
        "usb", "serial", "uart", "acm", "modem",
        "cp210", "ch34", "ftdi", "cdc", "usbserial",
        "ttyusb", "ttyacm", "bluetooth"
    ]
    if any(k in dev or k in desc for k in good_keywords):
        return True

    # macOS often uses /dev/tty.* or /dev/cu.*
    if dev.startswith("/dev/tty.") or dev.startswith("/dev/cu."):
        return True

    # Windows COM ports
    if dev.startswith("com"):
        return True

    return False

# ---------- app ----------

class HydraPurrApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.minsize(780, 520)
        self._build_menu()
        self._build_widgets()
        self._bind_shortcuts()

        # Backend state
        self.conn = None
        self.connected = False
        self.polling = False

        # UI state
        self.eom = b"*"

        # Populate ports initially
        self.refresh_ports()

    # ---------------- UI construction ----------------
    def _build_menu(self):
        menubar = tk.Menu(self)
        # File
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Save Log…", command=self.save_log)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self._on_exit)
        menubar.add_cascade(label="File", menu=filemenu)
        # Help
        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="About", command=lambda: messagebox.showinfo(
            "About", f"{APP_TITLE}\nSimple desktop tool for HydraPurr\n© You"
        ))
        menubar.add_cascade(label="Help", menu=helpmenu)
        self.config(menu=menubar)

    def _build_widgets(self):
        # Top frame: connection controls
        top = ttk.Frame(self, padding=(10,10,10,5))
        top.grid(row=0, column=0, sticky="nsew")

        ttk.Label(top, text="Port:").grid(row=0, column=0, sticky="w")
        self.port_var = tk.StringVar()
        self.port_cb  = ttk.Combobox(top, textvariable=self.port_var, state="readonly", width=38, values=[])
        self.port_cb.grid(row=0, column=1, sticky="w", padx=(5,10))

        self.refresh_btn = ttk.Button(top, text="Refresh", command=self.refresh_ports)
        self.refresh_btn.grid(row=0, column=2, padx=(0,10))

        ttk.Label(top, text="Baud:").grid(row=0, column=3, sticky="e")
        self.baud_var = tk.StringVar(value="9600")
        self.baud_cb  = ttk.Combobox(top, textvariable=self.baud_var, state="readonly",
                                     width=10, values=["9600","19200","38400","57600","115200"])
        self.baud_cb.grid(row=0, column=4, sticky="w", padx=(5,10))

        self.connect_btn = ttk.Button(top, text="Connect", command=self.connect)
        self.connect_btn.grid(row=0, column=5, padx=(0,6))
        self.disconnect_btn = ttk.Button(top, text="Disconnect", command=self.disconnect, state="disabled")
        self.disconnect_btn.grid(row=0, column=6)

        # Middle frame: command + options
        mid = ttk.Frame(self, padding=(10,5,10,5))
        mid.grid(row=1, column=0, sticky="ew")
        mid.columnconfigure(1, weight=1)

        ttk.Label(mid, text="Command:").grid(row=0, column=0, sticky="w")
        self.cmd_var = tk.StringVar(value="system")  # default command
        self.cmd_entry = ttk.Entry(mid, textvariable=self.cmd_var)
        self.cmd_entry.grid(row=0, column=1, sticky="ew", padx=(5,5))

        self.add_star_var = tk.BooleanVar(value=True)   # append '*'
        self.add_crlf_var = tk.BooleanVar(value=True)   # append CRLF
        ttk.Checkbutton(mid, text="Append *", variable=self.add_star_var).grid(row=0, column=2, padx=(4,4))
        ttk.Checkbutton(mid, text="Append \\r\\n", variable=self.add_crlf_var).grid(row=0, column=3, padx=(4,4))

        self.send_btn = ttk.Button(mid, text="Send", command=self.send_cmd, state="disabled")
        self.send_btn.grid(row=0, column=4, padx=(10,0))

        # Log frame (Text + scrollbar)
        logf = ttk.Frame(self, padding=(10,5,10,10))
        logf.grid(row=2, column=0, sticky="nsew")
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)

        self.text = tk.Text(logf, wrap="none", height=18, undo=False)
        self.text.grid(row=0, column=0, sticky="nsew")
        logf.rowconfigure(0, weight=1)
        logf.columnconfigure(0, weight=1)

        yscroll = ttk.Scrollbar(logf, orient="vertical", command=self.text.yview)
        yscroll.grid(row=0, column=1, sticky="ns")
        self.text.configure(yscrollcommand=yscroll.set)

        # Bottom bar
        bot = ttk.Frame(self, padding=(10,0,10,10))
        bot.grid(row=3, column=0, sticky="ew")
        bot.columnconfigure(1, weight=1)

        self.clear_btn = ttk.Button(bot, text="Clear Log", command=self.clear_log)
        self.clear_btn.grid(row=0, column=0, padx=(0,10))
        self.save_btn  = ttk.Button(bot, text="Save Log…", command=self.save_log)
        self.save_btn.grid(row=0, column=1, sticky="w")

        self.status = ttk.Label(bot, text="Disconnected", anchor="w")
        self.status.grid(row=0, column=2, sticky="e")

    def _bind_shortcuts(self):
        self.bind("<Control-s>", lambda e: self.save_log())
        self.bind("<Control-S>", lambda e: self.save_log())
        self.protocol("WM_DELETE_WINDOW", self._on_exit)

    # ---------------- pyserial backend ----------------

    def _backend_list_ports(self):
        ports = []
        for p in list_ports.comports():
            label = f"{p.device}"
            if p.description: label += f"  ({p.description})"
            ports.append(label)
        return ports

    # def _backend_list_ports(self):
    #     ports = []
    #     for p in list_ports.comports():
    #         if _is_visible_port(p):
    #             label = f"{p.device}"
    #             if p.description:
    #                 label += f"  ({p.description})"
    #             ports.append(label)
    #     return ports

    def _resolve_device_path(self, label):
        return label.split()[0] if label else ""

    def _backend_connect(self, port_label, baud):
        dev = self._resolve_device_path(port_label)
        if not dev:
            raise RuntimeError("No port selected.")
        ser = serial.Serial(
            dev,
            baudrate=int(baud),
            timeout=0,          # non-blocking read
            write_timeout=2.0
        )
        try:
            ser.reset_input_buffer()
            ser.reset_output_buffer()
        except Exception:
            pass
        return ser

    def _backend_disconnect(self, handle):
        try:
            handle.close()
        except Exception:
            pass

    def _backend_send(self, handle, data_bytes):
        return handle.write(data_bytes)

    def _backend_read_some(self, handle, max_bytes=4096):
        try:
            return handle.read(max_bytes)  # non-blocking because timeout=0
        except Exception:
            return b""

    # ---------------- UI actions ----------------

    def refresh_ports(self):
        ports = self._backend_list_ports()
        self.port_cb["values"] = ports
        if ports:
            if not self.port_var.get():
                self.port_var.set(ports[0])
        else:
            self.port_var.set("")
        self._set_status("Ports refreshed.")

    def connect(self):
        if self.connected:
            return
        port = self.port_var.get().strip()
        baud = self.baud_var.get().strip()
        if not port:
            messagebox.showwarning("Connect", "Select a port first.")
            return
        try:
            self.conn = self._backend_connect(port, baud)
            self.connected = True
        except Exception as e:
            messagebox.showerror("Connect failed", str(e))
            self._set_status("Connect failed.")
            return

        self.connect_btn.config(state="disabled")
        self.disconnect_btn.config(state="normal")
        self.send_btn.config(state="normal")
        self._set_status(f"Connected: {port} @ {baud}")
        self._start_polling()

    def disconnect(self):
        if not self.connected:
            return
        try:
            self._backend_disconnect(self.conn)
        except Exception as e:
            self._set_status(f"Disconnect error: {e}")
        self.conn = None
        self.connected = False
        self.connect_btn.config(state="normal")
        self.disconnect_btn.config(state="disabled")
        self.send_btn.config(state="disabled")
        self._stop_polling()
        self._set_status("Disconnected.")

    def send_cmd(self):
        if not self.connected:
            messagebox.showwarning("Send", "Not connected.")
            return
        cmd = self.cmd_var.get()
        if cmd is None:
            return
        out = cmd
        if self.add_star_var.get() and not out.endswith("*"):
            out += "*"
        if self.add_crlf_var.get():
            out += "\r\n"
        try:
            n = self._backend_send(self.conn, out.encode("utf-8"))
            self._append_log(f">>> {cmd}  (sent {n} bytes)")
        except Exception as e:
            self._append_log(f"[Send error] {e}")
            self._set_status("Send error.")

    # ---------------- polling / RX ----------------

    def _start_polling(self):
        if not self.polling:
            self.polling = True
            self.after(POLL_MS, self._poll_once)

    def _stop_polling(self):
        self.polling = False

    def _poll_once(self):
        if not self.polling or not self.connected:
            return
        try:
            data = self._backend_read_some(self.conn, 4096)
        except Exception as e:
            self._append_log(f"[Read error] {e}")
            self._set_status("Read error; disconnecting.")
            self.disconnect()
            return

        if data:
            # If your device streams newline-delimited CSV or text, this will show it as-is.
            # If you prefer splitting on '*', you can buffer & split here.
            text = data.decode("utf-8", errors="ignore")
            text = text.replace('*', '\n')  # optional: make '*' a line break
            self._append_log(text, raw=True)

        if self.polling:
            self.after(POLL_MS, self._poll_once)

    # ---------------- log utils ----------------

    def _append_log(self, s, raw=False):
        if not raw:
            s = s + "\n"
        self.text.insert("end", s)
        self.text.see("end")

    def clear_log(self):
        self.text.delete("1.0", "end")

    def save_log(self):
        content = self.text.get("1.0", "end")
        if not content.strip():
            messagebox.showinfo("Save Log", "Nothing to save.")
            return
        fn = filedialog.asksaveasfilename(
            title="Save Log",
            defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("CSV", "*.csv"), ("All Files", "*.*")]
        )
        if not fn:
            return
        try:
            with open(fn, "w", encoding="utf-8") as f:
                f.write(content)
            self._set_status(f"Saved: {os.path.basename(fn)}")
        except Exception as e:
            messagebox.showerror("Save failed", str(e))

    def _set_status(self, msg):
        self.status.config(text=msg)

    # ---------------- exit ----------------

    def _on_exit(self):
        try:
            if self.connected and self.conn:
                self._backend_disconnect(self.conn)
        except Exception:
            pass
        self.destroy()

if __name__ == "__main__":
    app = HydraPurrApp()
    app.mainloop()
