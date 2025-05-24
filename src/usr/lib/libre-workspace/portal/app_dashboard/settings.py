import os
import json

cfg = {}
file_path = "/var/lib/libre-workspace/portal/app_dashboard_settings.json"


# Save the configuration to the file as json
def set_value(key, value):
    cfg[key] = value
    with open(file_path, "w") as file:
        file.write(json.dumps(cfg))


def get_value(key, default=None):
    if key in cfg:
        return cfg[key]
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as file:
                cfg.update(json.loads(file.read()))
                if key in cfg:
                    return cfg[key]
        except:
            pass
    cfg[key] = default
    return default

def get_all_values():
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as file:
                cfg.update(json.loads(file.read()))
        except:
            pass
    return cfg