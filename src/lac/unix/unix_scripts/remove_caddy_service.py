# Needs one argument: hostname of the service
# Removes a service entry from the Caddyfile e.g. "cloud.example.com"

import sys
import os

# Get first argument which is the hostname of the service
hostname = sys.argv[1]

# Check if we are running as root
if os.geteuid() != 0:
    print("This script must be run as root.")
    sys.exit(1)

# Read Caddyfile
with open("/etc/caddy/Caddyfile", "r") as f:
    lines = f.readlines()
    # Iterate over all lines in the Caddyfile looking for the hostname
    beginning_index = -1
    brackets_level = 0
    ending_index = -1
    for i in range(len(lines)):
        line = lines[i]
        if line.strip().startswith("#"):
            continue
        line = line.split("#")[0]
        line = line.strip()
        if line.startswith(f"{hostname}"):
            beginning_index = i
            print("Found beginning index", beginning_index)
        if beginning_index != -1:
            # Count { in the line
            brackets_level += line.count("{")
            # Count } in the line
            brackets_level -= line.count("}")
        
        if beginning_index != -1 and brackets_level == 0:
            # If the brackets level is 0, we found the end of the service entry
            ending_index = i
            print("Found ending index", ending_index)
            break
    
    # Remove all lines from the beginning index to the ending index
    if beginning_index != -1 and ending_index != -1:
        print(f"Removing service entry for {hostname} from Caddyfile")
        lines = lines[:beginning_index] + lines[ending_index+1:]

# Write the new Caddyfile
with open("/etc/caddy/Caddyfile", "w") as f:
    f.writelines(lines)
    print("Service entry removed from Caddyfile")
    os.system("systemctl restart caddy")
    sys.exit(0)
