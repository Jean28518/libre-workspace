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

    # Create a .zip file from the directory (working directory is /tmp)
    # subprocess.run(["zip", "-r", f"{addon['id']}.zip", f"{addon['id']}"], env={"PWD": "/tmp"})
    os.system(f"cd /tmp; zip -r {addon['id']}.zip {addon['id']}")
    time.sleep(2)
  
    # Read the .zip file in bytes
    with open(f"/tmp/{addon['id']}.zip", "rb") as f:
        addon_zip = f.read()
    return addon_zip