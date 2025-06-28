import os
import unix.unix_scripts.unix
import subprocess
from app_dashboard.models import DashboardEntry

caddyfile_path = os.path.join(os.getenv("CADDY_CONFIG_DIR", "/etc/caddy"), "Caddyfile")


def get_all_caddy_entries():
    """
    Returns a list of all Caddy entries.
    """
   
    if not os.path.exists(caddyfile_path):
        print(f"Caddyfile not found at {caddyfile_path}")
        return []
    
    with open(caddyfile_path, 'r') as file:
        caddy_entries = file.readlines()
    
    last_bracket_count = 0 # 0: outside of a block, >0: inside a block
    entries = [] # entry = { "name": "NocoDB", "block": "db.int.de { \n ..." }
    last_comment_line = None
    id_counter = 0
    for i in range(len(caddy_entries)):
        if caddy_entries[i].strip().startswith("#"):
            last_comment_line = caddy_entries[i].strip()

        # Count the brackets to determine if we are inside a block
        bracket_count = last_bracket_count 
        for char in caddy_entries[i]:
            if char == '{':
                bracket_count += 1
            elif char == '}':
                bracket_count -= 1
            elif char == '#':
                break

        if last_bracket_count == 0 and bracket_count > 0:
            # We are starting a new block
            if last_comment_line is not None:
                # Give it the name of the last comment line
                entries.append({"name": last_comment_line.replace("#", "").strip(), "block": [caddy_entries[i]], "id": id_counter, "urls_unsafe": caddy_entries[i].replace("{", "")})
                id_counter += 1
            else:
                # Generate the name from the first domain in the block
                domain_parts = caddy_entries[i].split()
                if domain_parts:
                    domain_name = domain_parts[0].strip()
                    entries.append({"name": domain_name, "block": [caddy_entries[i]], "id": id_counter, "urls_unsafe": caddy_entries[i].replace("{", "")})
                    id_counter += 1
                else: 
                    entries.append({"name": "Line " + str(i), "block": [caddy_entries[i]]})
        elif last_bracket_count > 0 and bracket_count > 0:
            # We are inside a block, add the line to the last entry
            entries[-1]["block"].append(caddy_entries[i])
        elif last_bracket_count > 0 and bracket_count == 0:
            # We are closing a block
            entries[-1]["block"].append(caddy_entries[i])

        
        # Clear last comment line if we are currently not in a comment
        # This is to ensure that the last comment line is only used for the very next line.
        if not caddy_entries[i].strip().startswith("#"):
            last_comment_line = None
        
        last_bracket_count = bracket_count

    # Convert the blocks to strings
    for entry in entries:
        entry["block"] = "".join(entry["block"]).strip()

    # Mark the essential entries:
    for entry in entries:
        # Mark the PORTAL-ENTRY as essential (access to this django app here)
        if entry["name"] in ["PORTAL-ENTRY"]:
            entry["essential"] = True
            entry["name"] = "Libre Workspace Portal Entry"
        else:
            entry["essential"] = False
        # Mark the access entry as essential if it has the reverse proxy rule
        if "rewrite*/welcome/accessreverse_proxylocalhost:11123" in entry["block"].replace("\n", "").replace("\r", "").replace(" ", ""):
            entry["essential"] = True
            entry["name"] = "How to access page"
        if "root*/var/www/cert/" in entry["block"].replace("\n", "").replace("\r", "").replace(" ", ""):
            entry["essential"] = True
            entry["name"] = "Certificates"
    return entries


def delete_caddy_entry(entry_id):
    """Deletes a Caddy entry by its ID.
    """
    entries = get_all_caddy_entries()
    entry_to_delete = next((e for e in entries if e.get("id") == entry_id), None)
    
    if not entry_to_delete:
        return False
    
    # Find the first line of the block to delete
    first_line = entry_to_delete["block"].splitlines()[0].strip()

    found_line = -1
    with open(caddyfile_path, 'r') as file:
        caddyfile_lines = file.readlines()
        for i, line in enumerate(caddyfile_lines):
            if line.strip() == first_line:
                found_line = i
                break

    number_of_lines_to_delete = entry_to_delete["block"].count("\n") + 1  # +1 for the first line itself
    # Remove the block from the caddyfile with sed
    print(f"Removing {number_of_lines_to_delete} lines starting from line {found_line + 1} in {caddyfile_path}")
    os.system(f"sed -i '{found_line + 1},{found_line + number_of_lines_to_delete}d' {caddyfile_path}")
    
    remove_orphaned_comment_lines(entry_to_delete["name"])  # Remove orphaned comment lines

    clean_newlines()  # Clean up the file after deletion

    restart_caddy()


def remove_orphaned_comment_lines(comment):
    """Removes orphaned comment lines from the Caddyfile.
    
    Orphaned comment lines are those that do not have a corresponding block of code.
    """
   # Now try to find the comment line and remove it
    comment_line = comment.strip()
    if not comment_line.startswith("#"):
        comment_line = f"# {comment_line}"
    found_line = -1
    with open(caddyfile_path, 'r') as file:
        caddyfile_lines = file.readlines()
        for i, line in enumerate(caddyfile_lines):
            if i == 0 :
                if line.strip() == comment_line and caddyfile_lines[i+1].strip() == "":
                    found_line = i
                    break
            elif i < len(caddyfile_lines) - 1:
                if line.strip() == comment_line and caddyfile_lines[i-1].strip() == "" and caddyfile_lines[i+1].strip() == "":
                    found_line = i
                    break
            elif i == len(caddyfile_lines) - 1:
                if line.strip() == comment_line and caddyfile_lines[i-1].strip() == "":
                    found_line = i
                    break

    if found_line != -1:
        print(f"Removing comment line at {found_line + 1} in {caddyfile_path}")
        os.system(f"sed -i '{found_line + 1}d' {caddyfile_path}")


def clean_newlines():
     # Make sure that there are not more than 2 empty lines anywhere in the file
    with open(caddyfile_path, 'r') as file:
        caddyfile_lines = file.readlines()
    with open(caddyfile_path, 'w') as file:
        empty_line_count = 0
        for line in caddyfile_lines:
            if line.strip() == "":
                empty_line_count += 1
                if empty_line_count <= 2:
                    file.write(line)
            else:
                empty_line_count = 0
                file.write(line)

def add_caddy_entry(name, block):
    """Adds a new Caddy entry.
    Also adds a DNS entry in Samba for the domain, if domain is a int.de one.
    """
    urls = block.splitlines()[0].strip()
    first_url = urls.split()[0].replace("http://", "").replace("https://", "").strip()  # Get the first URL and remove http:// or https://

    with open(caddyfile_path, 'a') as file:
        file.write(f"\n\n# {name}\n")
        file.write(block + "\n")

    clean_newlines()  # Clean up the file after adding a new entry

    # Ensure the DNS name of the first url is valid
    ip = unix.unix_scripts.unix.get_server_ip()  # Get the server IP address
    unix.unix_scripts.unix.ensure_dns_entry_in_samba(ip, first_url)  # Ensure the DNS entry is in the Samba DNS

    restart_caddy()
    return True  # Indicate success


def restart_caddy():
    subprocess.Popen(["bash", "-c", "sleep 0.5; systemctl restart caddy"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def create_reverse_proxy(name, domain, port=None, internal_https=False, target_url="http://localhost:8000", wordpress_instance=False):
    """Creates a reverse proxy entry in the Caddyfile.
    Also adds a DNS entry in Samba for the domain, if domain is a int.de one.
    
    Args:
        name (str): The name of the reverse proxy.
        domain (str): The domain for the reverse proxy.
        port (int, optional): The port for the reverse proxy. Defaults to None.
        internal_https (bool, optional): Whether to use internal HTTPS. Defaults to False.
        target_url (str, optional): The target URL for the reverse proxy. Defaults to "http://localhost:8000".
    """

    # Ensure in the domain is only a valid domain name
    if not domain or not isinstance(domain, str) or not domain.strip() and not domain.strip().replace(".", "").replace("http://", "").replace("https://", "").isalnum():
        return "Invalid domain name provided. It must be a non-empty string containing only alphanumeric characters and dots. http:// and https:// are allowed as well."
    
    # Make sure the port is an integer if provided
    if port is not None:
        if not isinstance(port, int) or port < 1 or port > 65535:
            return "Port must be an integer between 1 and 65535."

    caddy_block = domain.strip()
    if port:
        caddy_block += f":{port}"
    
    caddy_block += " {\n"
    if internal_https:
        caddy_block += "  tls internal\n"
    caddy_block += f"  reverse_proxy {target_url}"

    # If https:// in target url we need to add: 
    #   {
    #     transport http {
    #       tls_insecure_skip_verify
    #     }
    #   }
    if target_url.startswith("https://"):
        caddy_block += " {\n"
        caddy_block += "    transport http {\n"
        caddy_block += "      tls_insecure_skip_verify\n"
        caddy_block += "    }\n"
        caddy_block += "  }\n"
    else:
        caddy_block += "\n"


    caddy_block += "}\n"

    new_dashboard_entry = DashboardEntry(
        title=name,
        description=f"",
        link=f"https://{domain}",
        icon_url="",
        is_system=False,
        order=8,  # Default order, can be adjusted later
    )
    if wordpress_instance:
        new_dashboard_entry.title = name.replace("Wordpress:", "").strip()  # Remove "Wordpress:" from the title
        new_dashboard_entry.icon_url = "/static/lac/icons/wordpress.webp"
    new_dashboard_entry.save()  # Save the dashboard entry to the database


    # Add the entry to the Caddyfile
    if add_caddy_entry(name, caddy_block):
        return f"Reverse proxy entry '{name}' created successfully."
    
    return "Failed to create reverse proxy entry. Please check the Caddyfile path and permissions."
    

def create_backup_of_caddyfile():
    """Creates a backup of the Caddyfile.
    
    The backup is created in the same directory as the Caddyfile with a timestamp.
    """
    os.system(f"cp {caddyfile_path} {caddyfile_path}.backup.libreworkspace")