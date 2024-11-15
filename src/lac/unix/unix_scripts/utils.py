# To this file unix.py (django) and also service.py (not django) can access
import subprocess


def is_backup_running():
    # Check if a process with the name backup.sh in it is running
    return "backup.sh" in subprocess.getoutput("ps -aux")


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