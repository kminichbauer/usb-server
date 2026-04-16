import os
import re
import subprocess


def run(cmd):
    use_shell = isinstance(cmd, str)
    result = subprocess.run(
        cmd,
        shell=use_shell,
        capture_output=True,
        text=True
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def sudo_run(args):
    if os.geteuid() != 0:
        args = ["sudo", "-n"] + args
    return run(args)


def parse_usbip_list(output):
    devices = []
    current = None

    for line in output.splitlines():
        busid_match = re.match(r"^\s*-\s*busid\s+(\S+)(?:\s+\(([^)]+)\))?", line)
        if busid_match:
            if current:
                devices.append(current)
            current = {
                "busid": busid_match.group(1),
                "vendor_product": busid_match.group(2) or "",
                "name": ""
            }
            continue

        if current and line.strip() and not line.strip().startswith("Public Key"):
            if not current["name"]:
                current["name"] = line.strip()

    if current:
        devices.append(current)

    return devices


def parse_usbip_remote_list(output):
    devices = []
    for line in output.splitlines():
        remote_match = re.match(
            r"^\s*-\s*(?:\S+\s+)?(?P<busid>\d+-\d+\.\d+)(?:\s+\((?P<vidpid>[^)]+)\))?\s*(?::\s*)?(?P<name>.*)$",
            line
        )
        if remote_match:
            devices.append({
                "busid": remote_match.group("busid"),
                "vendor_product": remote_match.group("vidpid") or "",
                "name": remote_match.group("name").strip() or ""
            })
    return devices


def list_usb_devices():
    out, err, rc = run("usbip list -l")
    if rc != 0:
        raise RuntimeError(err or "Failed to list local USB devices")
    return parse_usbip_list(out)


def list_remote_devices(ip):
    out, err, rc = run(f"usbip list -r {ip}")
    if rc != 0:
        raise RuntimeError(err or "Failed to list remote USB devices")
    return parse_usbip_remote_list(out)


def bind_device(busid):
    return sudo_run(["usbip", "bind", "-b", busid])


def unbind_device(busid):
    return sudo_run(["usbip", "unbind", "-b", busid])


def attach_device(ip, busid):
    return sudo_run(["usbip", "attach", "-r", ip, "-b", busid])


def detach_port(port):
    return sudo_run(["usbip", "detach", "-p", port])


def start_usbipd():
    return sudo_run(["usbipd", "-D"])
