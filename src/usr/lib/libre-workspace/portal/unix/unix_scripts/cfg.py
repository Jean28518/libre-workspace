import os

# Config service which edits and gets the config in the cfg file

def get_config_path():
    # Check if the "cfg" file is in the parent/parent directory
    if os.path.isfile("../../cfg"):
        return os.getcwd() + "/../../cfg"
    # Check if the "cfg" file is in the parent/pareent/parent/parent directory (for development)
    elif os.path.isfile("../../../../cfg"):
        return os.getcwd() + "/../../../../cfg"
    elif os.path.isfile("/usr/share/linux-arbeitsplatz/cfg"):
        return "/usr/share/linux-arbeitsplatz/cfg"
    else:
        return "!ERROR: cfg file not found!"

def get_value(key, default):
    # Open cfg file
    with open(get_config_path(), "r") as f:
        # Read all lines
        lines = f.readlines()
        # Iterate over all lines
        for line in lines:
            line_parts = line.split("=")
            if line_parts[0].replace(" ", "").replace("export", "") == key:
                # If the value is surrounded by " ", remove them
                if line_parts[1].strip().startswith("\"") and line_parts[1].strip().endswith("\""):
                    return line_parts[1].strip()[1:-1]
                else:
                    return line_parts[1].strip()
            
        
        return default
    
def set_value(key, value):
    # Open cfg file
    with open(get_config_path(), "r") as f:
        # Read all lines
        lines = f.readlines()
        # Iterate over all lines
        settings_found = False
        for i in range(len(lines)):
            line = lines[i]
            line_parts = line.split("=")
            if line_parts[0].replace(" ", "").replace("export", "") == key:
                lines[i] = f'export {key}="{value}"\n'
                settings_found = True
               
        if not settings_found:
            lines.append(f'export {key}="{value}"\n')
    
    # Write all lines back to the cfg file
    with open(get_config_path(), "w") as f:
        f.writelines(lines)