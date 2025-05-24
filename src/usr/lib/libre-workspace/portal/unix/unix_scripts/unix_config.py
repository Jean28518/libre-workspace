# This code is duplicated in the unix.py file for internal use.
# We need this for our service.py because it does not like the unix.py file.
import os


# Change current directory to the directory of this script
os.chdir(os.path.dirname(os.path.realpath(__file__)))

# If the config file does not exist, create it
if not os.path.isfile("/etc/libre-workspace/libre-workspace.conf"):
    os.system("touch /etc/libre-workspace/libre-workspace.conf")  
    

config = {}

def read_config_file():
    # Read the config file
    for line in open("/etc/libre-workspace/libre-workspace.conf"):
        if line.strip().startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        # remove the " and ' characters from the outer ends of the string
        config[key.strip()] = value.strip("'\"\n ")

def write_config_file():
    # Write the config file
    with open("/etc/libre-workspace/libre-workspace.conf", "w") as f:
        for key, value in config.items():
            if value == "true" or value == "false" or value.isnumeric():
                f.write(f"{key}={value}\n")
            else:
                f.write(f"{key}=\"{value}\"\n")


def get_value(key, default=""):
    read_config_file()
    # Get the value of a key from the config file
    if key in config:
        return config[key]
    else:
        return default


def set_value(key, value):
    read_config_file()
    value = str(value)
    # Set the value of a key in the config file
    if value != "":
        config[key] = value
    elif key in config:
        del config[key]
    print(f"Setting {key} to {value}")
    write_config_file()