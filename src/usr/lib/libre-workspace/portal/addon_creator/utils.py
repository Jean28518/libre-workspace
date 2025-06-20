import shutil
import zipfile
import os
import datetime
from jinja2 import Template
from django.conf import settings
import time
import subprocess
DJANGO_ROOT = settings.BASE_DIR


def create_addon(cleaned_form):
    """Returns the .zip file in bytes"""
    # Create a new directory inside /tmp
    addon = {}
    addon["id"] = cleaned_form["addon_id"]
    # if the directory already exists, delete it
    if os.path.exists("/tmp/" + addon["id"]):
        shutil.rmtree("/tmp/" + addon["id"])
    if os.path.exists("/tmp/" + addon["id"] + ".zip"):
        os.remove("/tmp/" + addon["id"] + ".zip")

    addon["name"] = cleaned_form["addon_name"]
    addon["description"] = cleaned_form["addon_description"]
    addon["author"] = cleaned_form["addon_author"]
    addon["mail"] = cleaned_form["addon_author_email"]
    addon["url"] = cleaned_form["addon_url"]
    addon["docker_compose"] = cleaned_form["addon_docker_compose"]
    addon["internal_port"] = cleaned_form["addon_internal_port"]
    addon["project_homepage"] = cleaned_form["project_homepage"]
    addon["year"] = datetime.datetime.now().year

    # Copy the file content of DJANGO_ROOT/addon_creator/addon_template to /tmp/addon_id
    shutil.copytree(f"{DJANGO_ROOT}/addon_creator/addon_template", f"/tmp/{addon['id']}")

    # For every file in the directory replace "addon" in the filename with the addon_id
    for root, dirs, files in os.walk(f"/tmp/{addon['id']}"):
        for file in files:
            new_file = file.replace("addon", addon["id"])
            os.rename(os.path.join(root, file), os.path.join(root, new_file))

    # Write the docker-compose.yml content to the file
    with open(f"/tmp/{addon['id']}/docker-compose.yml", "w") as f:
        f.write(addon["docker_compose"])

    # Write the Description into the control file
    description_lines = addon["description"].split("\n")
    # Replace Description: 
    os.system(f"sed -i 's/Description: .*/Description: {description_lines[0]}/' /tmp/{addon['id']}/control")
    # Add the rest of the description
    for line in description_lines[1:]:
        os.system(f"echo ' {line}' >> /tmp/{addon['id']}/control")
    
    # Handle the logo
    if cleaned_form['addon_logo'] is not None:
        file = cleaned_form['addon_logo']
        # Get the file extension
        extension = file.name.split(".")[-1]
        with open(f"/tmp/{addon['id']}/{addon['id']}.{extension}", "wb") as f:
            f.write(file.read())

    for root, dirs, files in os.walk(f"/tmp/{addon['id']}"):
        for file in files:           
            with open(os.path.join(root, file), "r") as f:
                try:
                    content = f.read()
                    template = Template(content)
                    content = template.render(addon=addon)
                    with open(os.path.join(root, file), "w") as f:
                        f.write(content)
                except:
                    pass

    # Create the deb package:
    os.system(f"mkdir -p /tmp/{addon['id']}/deb/DEBIAN")
    os.system(f"mv /tmp/{addon['id']}/control /tmp/{addon['id']}/deb/DEBIAN/control")
    os.system(f"mv /tmp/{addon['id']}/postinst /tmp/{addon['id']}/deb/DEBIAN/postinst")
    os.system(f"mv /tmp/{addon['id']}/install /tmp/{addon['id']}/deb/DEBIAN/install")
    os.system(f"chmod 755 /tmp/{addon['id']}/deb/DEBIAN/postinst")
    os.system(f"chmod 755 /tmp/{addon['id']}/deb/DEBIAN/install")
    os.system(f"mkdir -p /tmp/{addon['id']}/deb/usr/lib/libre-workspace/modules/{addon['id']}")
    os.system(f"mv /tmp/{addon['id']}/*.sh /tmp/{addon['id']}/deb/usr/lib/libre-workspace/modules/{addon['id']}/")
    os.system(f"mv /tmp/{addon['id']}/addon.conf /tmp/{addon['id']}/deb/usr/lib/libre-workspace/modules/{addon['id']}/")
    os.system(f"mv /tmp/{addon['id']}/LICENSE /tmp/{addon['id']}/deb/usr/lib/libre-workspace/modules/{addon['id']}/")
    os.system(f"mv /tmp/{addon['id']}/docker-compose.yml /tmp/{addon['id']}/deb/usr/lib/libre-workspace/modules/{addon['id']}/")
    os.system(f"mv /tmp/{addon['id']}/README.md /tmp/{addon['id']}/deb/usr/lib/libre-workspace/modules/{addon['id']}/")
    # Logo:
    os.system(f"mv /tmp/{addon['id']}/{addon['id']}* /tmp/{addon['id']}/deb/usr/lib/libre-workspace/modules/{addon['id']}/")
    # Create the deb package
    os.system(f"dpkg-deb --build /tmp/{addon['id']}/deb /tmp/{addon['id']}/libre-workspace-module-{addon['id']}.deb")

    readme = f"""# Addon: {addon['name']}
Author: {addon['author']} ({addon['mail']})
Homepage {addon['project_homepage']}

{addon['description']}

## How to install
Upload this .zip file OR the .deb file to your Libre-Workspace instance via the Addon Manager inside the portal. 
Alternatively install the .deb package via apt.

## How to rebuild the .deb package
If you want to rebuild the addon, you can use the following command:

```bash
# Start inside this directory
dpkg-deb --build deb libre-workspace-module-{addon['id']}.deb
```
    """

    # Write the README.md file
    with open(f"/tmp/{addon['id']}/README.md", "w") as f:
        f.write(readme)

    # Create a .zip file from the directory (working directory is /tmp)
    # subprocess.run(["zip", "-r", f"{addon['id']}.zip", f"{addon['id']}"], env={"PWD": "/tmp"})
    os.system(f"cd /tmp; zip -r {addon['id']}.zip {addon['id']}")
    time.sleep(2)
  
    # Read the .zip file in bytes
    with open(f"/tmp/{addon['id']}.zip", "rb") as f:
        addon_zip = f.read()
    return addon_zip