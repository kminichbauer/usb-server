import json
import os
import socket
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from common import attach_device, list_remote_devices

SERVER_IP = "192.168.1.100"
PORT = 5000


class UsbClientGui:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("USB-IP Client")
        self.root.geometry("700x520")
        self.remote_devices = []

        self._build_ui()
        if os.geteuid() != 0:
            self.log("Upozornění: klient běží bez root. Attach může selhat kvůli sudo.")
        self.server_ip_entry.insert(0, SERVER_IP)

    def _build_ui(self):
        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill="both", expand=True)

        header = ttk.Label(frame, text="USB-IP Client - připoj fyzické vzdálené USB zařízení", font=(None, 14, "bold"))
        header.pack(anchor="w", pady=(0, 10))

        settings_frame = ttk.Frame(frame)
        settings_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(settings_frame, text="Server IP:").pack(side="left")
        self.server_ip_entry = ttk.Entry(settings_frame, width=22)
        self.server_ip_entry.pack(side="left", padx=(4, 10))

        refresh_btn = ttk.Button(settings_frame, text="Obnovit dostupná zařízení", command=self.refresh_remote_devices)
        refresh_btn.pack(side="left")

        attach_btn = ttk.Button(settings_frame, text="Připojit vybrané", command=self.attach_selected)
        attach_btn.pack(side="left", padx=(10, 0))

        self.listbox = tk.Listbox(frame, selectmode="extended", height=14, activestyle="none")
        self.listbox.pack(fill="both", expand=False, pady=(0, 10))

        self.log_widget = ScrolledText(frame, height=16, state="disabled", wrap="word")
        self.log_widget.pack(fill="both", expand=True)

        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

    def refresh_remote_devices(self):
        self.listbox.delete(0, tk.END)
        self.remote_devices = []
        server_ip = self.server_ip_entry.get().strip()
        if not server_ip:
            self.log("Zadej prosím IP adresu serveru.")
            return

        try:
            devices = list_remote_devices(server_ip)
            for device in devices:
                title = f"{device['busid']} | {device['name']} {device['vendor_product']}"
                self.listbox.insert(tk.END, title)
                self.remote_devices.append(device)
            self.log(f"Dostupná zařízení ze serveru {server_ip} ({len(devices)})")
        except Exception as exc:
            self.log(f"Chyba při načítání vzdálených zařízení: {exc}")

    def _selected_busids(self):
        return [self.remote_devices[idx]["busid"] for idx in self.listbox.curselection()]

    def attach_selected(self):
        busids = self._selected_busids()
        if not busids:
            self.log("Vyber prosím alespoň jedno zařízení k připojení.")
            return

        server_ip = self.server_ip_entry.get().strip()
        for busid in busids:
            out, err, rc = attach_device(server_ip, busid)
            self.log(f"Attach {busid}: rc={rc} out={out or '<no output>'} err={err or '<no error>'}")

    def log(self, message):
        self.root.after(0, lambda: self._append_log(message))

    def _append_log(self, message):
        self.log_widget.configure(state="normal")
        self.log_widget.insert(tk.END, message + "\n")
        self.log_widget.see(tk.END)
        self.log_widget.configure(state="disabled")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    gui = UsbClientGui()
    gui.run()
