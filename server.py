import json
import os
import socket
import threading
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from common import bind_device, list_usb_devices, start_usbipd, unbind_device

HOST = "0.0.0.0"
PORT = 5000


class UsbServerGui:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("USB-IP Server")
        self.root.geometry("700x520")
        self.device_list = []
        self.server_socket = None
        self.running = False

        self._build_ui()
        if os.geteuid() != 0:
            self.log("Upozornění: server běží bez root. Bind/unbind může selhat kvůli sudo.")
        start_usbipd()
        self._start_server_thread()
        self.refresh_devices()

    def _build_ui(self):
        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill="both", expand=True)

        header = ttk.Label(frame, text="USB-IP Server - sdílej fyzická USB zařízení přes síť", font=(None, 14, "bold"))
        header.pack(anchor="w", pady=(0, 10))

        control_frame = ttk.Frame(frame)
        control_frame.pack(fill="x", pady=(0, 10))

        self.status_label = ttk.Label(control_frame, text=f"Server běží na {HOST}:{PORT}")
        self.status_label.pack(side="left")

        refresh_btn = ttk.Button(control_frame, text="Obnovit zařízení", command=self.refresh_devices)
        refresh_btn.pack(side="right", padx=(4, 0))

        button_frame = ttk.Frame(frame)
        button_frame.pack(fill="x", pady=(0, 10))

        bind_btn = ttk.Button(button_frame, text="Bind selected", command=self.bind_selected)
        bind_btn.pack(side="left")
        unbind_btn = ttk.Button(button_frame, text="Unbind selected", command=self.unbind_selected)
        unbind_btn.pack(side="left", padx=(8, 0))

        self.listbox = tk.Listbox(frame, selectmode="extended", height=12, activestyle="none")
        self.listbox.pack(fill="both", expand=False, pady=(0, 10))

        self.log_widget = ScrolledText(frame, height=14, state="disabled", wrap="word")
        self.log_widget.pack(fill="both", expand=True)

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _start_server_thread(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen()
        self.server_socket.settimeout(1.0)
        self.running = True

        thread = threading.Thread(target=self._run_server, daemon=True)
        thread.start()
        self.log("Server spuštěn, čekám na klienty...")

    def _run_server(self):
        while self.running:
            try:
                conn, addr = self.server_socket.accept()
            except OSError:
                break
            except Exception:
                continue

            thread = threading.Thread(target=self._handle_client, args=(conn, addr), daemon=True)
            thread.start()

    def _handle_client(self, conn, addr):
        self.log(f"Klient připojen: {addr}")
        try:
            data = conn.recv(8192).decode()
            req = json.loads(data)
            action = req.get("action")

            if action == "list":
                devices = list_usb_devices()
                conn.send(json.dumps({"devices": devices}).encode())
                self.log(f"Posílám seznam USB zařízení klientovi {addr}")

            elif action == "bind":
                results = []
                for busid in req.get("busids", []):
                    out, err, rc = bind_device(busid)
                    results.append({"busid": busid, "rc": rc, "out": out, "err": err})
                conn.send(json.dumps({"results": results}).encode())
                self.log(f"Provádím bind pro klienta {addr}: {req.get('busids')}")

            elif action == "unbind":
                results = []
                for busid in req.get("busids", []):
                    out, err, rc = unbind_device(busid)
                    results.append({"busid": busid, "rc": rc, "out": out, "err": err})
                conn.send(json.dumps({"results": results}).encode())
                self.log(f"Provádím unbind pro klienta {addr}: {req.get('busids')}")

            else:
                conn.send(json.dumps({"error": "unknown action"}).encode())
                self.log(f"Neznámá akce od klienta {addr}: {action}")
        except Exception as exc:
            try:
                conn.send(json.dumps({"error": str(exc)}).encode())
            except Exception:
                pass
            self.log(f"Chyba při zpracování klienta {addr}: {exc}")
        finally:
            conn.close()

    def refresh_devices(self):
        self.listbox.delete(0, tk.END)
        self.device_list = []
        try:
            devices = list_usb_devices()
            for device in devices:
                text = f"{device['busid']} | {device['name']} {device['vendor_product']}"
                self.listbox.insert(tk.END, text)
                self.device_list.append(device)
            self.log(f"Seznam zařízení obnoven ({len(devices)})")
        except Exception as exc:
            self.log(f"Chyba při načítání zařízení: {exc}")

    def _selected_busids(self):
        return [self.device_list[idx]["busid"] for idx in self.listbox.curselection()]

    def bind_selected(self):
        busids = self._selected_busids()
        if not busids:
            self.log("Vyber prosím alespoň jedno zařízení pro bind.")
            return
        for busid in busids:
            out, err, rc = bind_device(busid)
            self.log(f"Bind {busid}: rc={rc} out={out or '<no output>'} err={err or '<no error>'}")
        self.refresh_devices()

    def unbind_selected(self):
        busids = self._selected_busids()
        if not busids:
            self.log("Vyber prosím alespoň jedno zařízení pro unbind.")
            return
        for busid in busids:
            out, err, rc = unbind_device(busid)
            self.log(f"Unbind {busid}: rc={rc} out={out or '<no output>'} err={err or '<no error>'}")
        self.refresh_devices()

    def log(self, message):
        self.root.after(0, lambda: self._append_log(message))

    def _append_log(self, message):
        self.log_widget.configure(state="normal")
        self.log_widget.insert(tk.END, message + "\n")
        self.log_widget.see(tk.END)
        self.log_widget.configure(state="disabled")

    def _on_close(self):
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    gui = UsbServerGui()
    gui.run()
