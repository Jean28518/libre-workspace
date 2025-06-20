import os
import subprocess
from lac.settings import MEDIA_ROOT, MEDIA_URL
from unix.unix_scripts import unix
import time

def get_all_available_addons():
    """
    Returns a list of available addons. Searches for all apt packages called libre-workspace-module-<addon_id>.
    """

    addons = []
    output = subprocess.run(
        ["apt", "search", "libre-workspace-module-"],
        capture_output=True,
        text=True,
        check=True
    ).stdout
    for line in output.splitlines():
        if "libre-workspace-module-" in line:
            addon_id = line.split()[0].replace("/stable", "")
            addon_id = addon_id.replace("libre-workspace-module-", "")
            information = subprocess.run(
                ["apt", "show", f"libre-workspace-module-{addon_id}"],
                capture_output=True,
                text=True,
                check=True
            ).stdout

            new_addon = {
                "id": addon_id,
                "name": "",
                "description": "",
                "version": "",
                "maintainer": "",
                "homepage": "",
                "installed": False,
                "icon_url": "",
            }
            in_description = False
            # Parse the information to extract details
            for info_line in information.splitlines():
                if info_line.startswith("Version:"):
                    new_addon["version"] = info_line.split(":")[1].strip()
                elif info_line.startswith("Maintainer:"):
                    new_addon["maintainer"] = info_line.split(":")[1].strip()
                elif info_line.startswith("Description:"):
                    new_addon["description"] = info_line.replace("Description:", "").strip()
                    in_description = True
                elif in_description and info_line.startswith(" "):
                    # Continue the description if it is indented
                    new_addon["description"] += " " + info_line.strip()
                elif in_description and not info_line.startswith(" "):
                    # Stop the description if a new line starts without indentation
                    in_description = False
                elif info_line.startswith("Homepage:"):
                    new_addon["homepage"] = info_line.replace("Homepage:", "").strip()
                elif info_line.startswith("Installed-Size:"):
                    # Check if the addon is installed
                    installed_check = subprocess.run(
                        ["dpkg", "-l", f"libre-workspace-module-{addon_id}"],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    new_addon["installed"] = installed_check.returncode == 0
            
            # Download the favicon if it not already exists in the static directory
            icon_path = os.path.join(MEDIA_ROOT, f"{addon_id}.ico")
            icon_path_png = os.path.join(MEDIA_ROOT, f"{addon_id}.png")
            if not os.path.exists(icon_path) and not os.path.exists(icon_path_png):
                try:
                    cleaned_url = new_addon["homepage"].strip()
                    if cleaned_url.endswith("/"):
                        cleaned_url = cleaned_url[:-1]
                    subprocess.run(
                        ["wget", "-q", "-O", icon_path, cleaned_url + f"/favicon.ico"],
                        check=True
                    )
                    # Check if the file size is greater than 0 bytes
                    if os.path.getsize(icon_path) == 0:
                        print(f"Downloaded icon for addon {addon_id} is empty. Using no icon.")
                        os.remove(icon_path)
                        new_addon["icon_url"] = ""
                    else:
                        new_addon["icon_url"] = "/" + os.path.join(MEDIA_URL, f"{addon_id}.ico")
                except subprocess.CalledProcessError:
                    print(f"Failed to download icon for addon {addon_id}. Using no icon.")
                    # If wget fails, we can skip downloading the icon
                    pass
            else:
                if os.path.exists(icon_path):
                    # If the icon already exists, use it
                    new_addon["icon_url"] = "/" + os.path.join(MEDIA_URL, f"{addon_id}.ico")
                elif os.path.exists(icon_path_png):
                    # If the PNG icon already exists, use it
                    new_addon["icon_url"] = "/" + os.path.join(MEDIA_URL, f"{addon_id}.png")
                else:
                    # If neither icon exists, set icon_url to empty
                    new_addon["icon_url"] = ""

            # If icon_url is empty: try it with open graph image
            if new_addon["icon_url"] == "":
                try:
                    html_content = subprocess.run(
                        ["wget", "-qO-", new_addon["homepage"]],
                        capture_output=True,
                        text=True,
                        check=True
                    ).stdout
                    # Search for the Open Graph image tag
                    start_index = html_content.find('<meta property="og:image" content="')
                    if start_index != -1:
                        start_index += len('<meta property="og:image" content="')
                        end_index = html_content.find('"', start_index)
                        if end_index != -1:
                            og_image_url = html_content[start_index:end_index]
                            # Download the Open Graph image
                            icon_path = os.path.join(MEDIA_ROOT, f"{addon_id}.png")
                            subprocess.run(
                                ["wget", "-q", "-O", icon_path, og_image_url],
                                check=True
                            )
                            # Check if the file size is greater than 0 bytes
                            if os.path.getsize(icon_path) > 0:
                                new_addon["icon_url"] = "/" + os.path.join(MEDIA_URL, f"{addon_id}.png")
                            else:
                                print(f"Downloaded Open Graph image for addon {addon_id} is empty. Using no icon.")
                                os.remove(icon_path)
                except subprocess.CalledProcessError:
                    print(f"Failed to download Open Graph image for addon {addon_id}. Using no icon.")
                    # If wget fails, we can skip downloading the icon
                    pass

            # Name extraction from the package name
            new_addon["name"] = new_addon["id"].replace("libre-workspace-module-", "").replace("-", " ").title()

            addons.append(new_addon)

    # Sort addons by name
    addons.sort(key=lambda x: x["name"].lower())
    # print(f"Available addons: {addons}")
    return addons


def install_addon(addon_id):
    """
    Installs the addon with the given addon_id.
    """
    try:
        subprocess.Popen(
            ["apt", "install", "-y", f"libre-workspace-module-{addon_id}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return
    except subprocess.CalledProcessError as e:
        print(f"Failed to install addon {addon_id}: {e}")
        return f"Failed to install addon {addon_id}: {e}"
    

def uninstall_addon(addon_id):
    """
    Removes the addon with the given addon_id. Also removes the whole module from the server and deletes all (user) data related to the addon.
    """
    try:
        message = unix.remove_module(addon_id)
        if message is not None:
            print(f"Message from remove_module: {message}")
            return message
        time.sleep(10)  # Wait for the module to be removed
        subprocess.Popen(
            ["apt", "remove", "-y", f"libre-workspace-module-{addon_id}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(2)
        return
    except subprocess.CalledProcessError as e:
        print(f"Failed to remove addon {addon_id}: {e}")
        return f"Failed to remove addon {addon_id}: {e}"