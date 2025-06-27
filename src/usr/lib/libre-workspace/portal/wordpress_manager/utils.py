import os
import subprocess
import json

from app_dashboard.models import DashboardEntry
import unix.unix_scripts.unix
import caddy_configuration.utils

def get_all_wordpress_sites():
    """Fetches all WordPress sites from the database."""
    os.system("mkdir -p /var/www/libreworkspace-wordpress/")
    # Get all subdirectories in /var/www/libreworkspace-wordpress/
    entries = os.listdir("/var/www/libreworkspace-wordpress/")
    # Have a look to every subdirectory and check if a lw_config.json file exists
    sites = []
    for entry in entries:
        entry_path = os.path.join("/var/www/libreworkspace-wordpress/", entry)
        if os.path.isdir(entry_path):
            config_file = os.path.join(entry_path, "lw_config.json")
            if os.path.isfile(config_file):
                # Read the lw_config.json file and extract the necessary information
                with open(config_file, 'r') as f:
                    site_info = f.read()
                    try:
                        site_data = json.loads(site_info)
                        site_data['id'] = entry  # Add the entry ID for identification
                        sites.append(site_data)
                    except json.JSONDecodeError:
                        print(f"Error decoding JSON for site {entry}. Skipping this entry.")
    return sites


def delete_wordpress_instance(entry_id):
    """Deletes a WordPress instance by its ID."""
    all_sites = get_all_wordpress_sites()
    site = next((s for s in all_sites if s.get("id") == entry_id), None)
    if not site:
        print(f"WordPress instance with ID {entry_id} not found.")
        return "WordPress instance not found."
    
    # Remove the caddy reverse proxy entry
    domain = site.get("domain")
    subprocess.Popen(f'bash -c "sleep 4; libre-workspace-remove-webserver-entry {domain}"', shell=True)

    instance_dir = f"/var/www/libreworkspace-wordpress/{entry_id}"
    if not os.path.exists(instance_dir):
        print(f"Instance directory {instance_dir} does not exist. Cannot delete.")
        return
    # Remove the instance directory
    subprocess.Popen(
        'bash -c "docker-compose -f {}/docker-compose.yml down --volumes; sleep 1; rm -rf {}"'.format(instance_dir, instance_dir),
        shell=True,
    )

    # Remove the app card entry from the dashboard
    if not domain:
        DashboardEntry.objects.filter(link=f"https://{domain}").delete()  # Remove the dashboard entry


    print(f"Deleting WordPress instance with ID: {entry_id}")


# def create_wordpress_instance(name, domain, admin_password, admin_email, locale):
def create_wordpress_instance(name, domain):
    """Creates or updates a WordPress instance."""
    random_port = subprocess.getoutput("shuf -i 1000-65000 -n 1")
    # Check if the port is already in use:
    while subprocess.getoutput(f"lsof -i :{random_port}"):
        random_port = subprocess.getoutput("shuf -i 1000-65000 -n 1")

    random_db_password = subprocess.getoutput("openssl rand -base64 12")
    random_db_root_password = subprocess.getoutput("openssl rand -base64 12")

    # Create the directory for the WordPress instance
    instance_dir = f"/var/www/libreworkspace-wordpress/{domain}"
    os.makedirs(instance_dir, exist_ok=True)

    # Preapare all the files:
    os.system(f"cp /usr/lib/libre-workspace/portal/wordpress_manager/wordpress_template/docker-compose.yml {instance_dir}/docker-compose.yml")
    os.system("sed -i 's/SED_PORT/" + random_port + "/g' " + f"{instance_dir}/docker-compose.yml")
    os.system("sed -i 's/SED_DB_PASSWORD/" + random_db_password + "/g' " + f"{instance_dir}/docker-compose.yml")
    os.system("sed -i 's/SED_ROOT_DB_PASSWORD/" + random_db_root_password + "/g' " + f"{instance_dir}/docker-compose.yml")

    # Create the lw_config.json file
    config_data = {
        "name": name,
        "domain": domain,
        "port": random_port,
        "db_password": random_db_password,
        "db_root_password": random_db_root_password,
    }

    config_file_path = os.path.join(instance_dir, "lw_config.json")
    with open(config_file_path, 'w') as config_file:
        json.dump(config_data, config_file, indent=4)

    caddy_configuration.utils.create_reverse_proxy(
        name=f"Wordpress: {name}",
        domain=domain,
        port=None, # Take the default port for the outside
        internal_https= "int.de" in domain,  # Use internal HTTPS for .int.de domains
        target_url=f"http://localhost:{random_port}",
    )

    # Run the docker-compose command to start the WordPress instance
    subprocess.Popen(
        [
            "bash", 
            "/usr/lib/libre-workspace/portal/wordpress_manager/wordpress_template/install_wordpress_instance.sh",
            instance_dir,
            # admin_password,
            # admin_email,
            # domain,
            # name,
            # locale,
            # random_db_password,
        ],
    )

