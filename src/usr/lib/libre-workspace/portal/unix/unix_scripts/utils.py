# To this file unix.py (django) and also service.py (not django) can access
import subprocess
import os
import requests


def is_backup_running(additional_id=None):
    # Check if a process with the name backup.sh in it is running
    if additional_id:
        return "backup.sh " + additional_id in subprocess.getoutput("ps -aux")
    return "backup.sh" in subprocess.getoutput("ps -aux")


def get_last_n_backups(n=5, additional_id=None):
    history_dir = "/var/lib/libre-workspace/portal/history/"
    key_addition = ""
    if additional_id:
        history_dir = "/var/lib/libre-workspace/portal/additional_backup_" + additional_id
        key_addition = "_" + additional_id
    return_value = []
    all_filenames = []
    for filename in os.listdir(history_dir):
        if filename.startswith("borg_errors_"):
            all_filenames.append(filename)
    all_filenames.sort(reverse=True)
    # Get the last n filenames
    all_filenames = all_filenames[:n]
    for filename in all_filenames:
        filepath = os.path.join(history_dir, filename)
        lines = []
        with open(filepath, "r") as f:
            lines = f.readlines()
        error = False
        if len(lines) > 0:
            error = True
        return_value.append({
            "date": filename.replace("borg_errors_", "").replace(".log", ""),
            "content": lines,
            "status": "error" if error else "success"
        })
    return return_value


def check_domain_online_status(domain, result_list=[""], index=0):
    """Returns http status code of the domain. If lower than 400, the domain is online."""
    try:
        response = requests.get("https://" + domain, timeout=10, verify=False)
        result_list[index] = {"domain": domain, "status_code": response.status_code}
        print(f"Checked domain {domain}, status code: {response.status_code}")
        print(index)
        print(result_list)
        print("-------------------")
        return {"domain": domain, "status_code": response.status_code}
    except requests.exceptions.RequestException as e:
        result_list[index] = {"domain": domain, "status_code": 500, "error": str(e)}
        return {"domain": domain, "status_code": 500, "error": str(e)}


def get_ram_usage():
    rv = {}
    rv["total_ram"] = subprocess.getoutput("free -h").split("\n")[1].split()[1].replace("Gi", "").replace("Mi", "")
    ram_usage = subprocess.getoutput("free -h").split("\n")[1].split()[2]
    if "Mi" in ram_usage:
        rv["ram_usage"] = str(int(ram_usage.replace("Mi", ""))/1024).replace(".", ",")
    else:
        rv["ram_usage"] = ram_usage.replace("Gi", "")
    rv["ram_percent"] = int(float(rv["ram_usage"].replace(",", ".")) / float(rv["total_ram"].replace(",", ".")) * 100)

    return rv


def get_cpu_usage(five_min=False):
    if five_min:
        load_avg = subprocess.getoutput("cat /proc/loadavg").split(" ")[1]
    else:
        load_avg = subprocess.getoutput("cat /proc/loadavg").split(" ")[0]
    cpu_number = subprocess.getoutput("nproc")
    return int(float(load_avg) / float(cpu_number) * 100)


def get_disks_stats():
    # Return disk name, the mountpoint, the foll size and the used size.
    lines = subprocess.getoutput("df -h")

    lines = lines.split("\n")
    lines = lines[1:]
    disks = []
    for line in lines:
        if "error" in line.lower() or "warning" in line.lower():
            continue
        line = line.split(" ")
        while '' in line:
            line.remove('')
        name = line[0]
        if "/dev/loop" in name or "udev" in name or "tmpfs" in name or "overlay" in name or "fuse" in name or "bindfs" in name:
            continue
        size = line[1]
        # If the size is in megabytes, skip this disk, because it is very small
        if "M" in size:
            continue
        disk = {}
        disk["name"] = name.replace("/dev/", "")
        disk["size"] = size
        disk["used"] = line[2]
        disk["used_percent"] = line[4].replace("%", "")
        disk["mountpoint"] = line[5]
        try:
            float(disk["size"].replace("G", "").replace("T", "").replace("M", "").replace("K", "").replace(",", ""))
            float(disk["used"].replace("G", "").replace("T", "").replace("M", "").replace("K", "").replace(",", ""))
            float(disk["used_percent"])
            disks.append(disk)
        except:
            continue
    return disks


def is_caddy_running():
# Check if caddy is running
    try:
        output = subprocess.check_output(["systemctl", "is-active", "caddy"], stderr=subprocess.STDOUT)
        return output.decode().strip() == "active"
    except subprocess.CalledProcessError:
        return False