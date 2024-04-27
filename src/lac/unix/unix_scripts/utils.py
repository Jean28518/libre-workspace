# To this file unix.py (django) and also service.py (not django) can access
import subprocess


def is_backup_running():
    # Check if a process with the name backup.sh in it is running
    return "backup.sh" in subprocess.getoutput("ps -aux")