#!/bin/bash

# We need the domain:
. /etc/libre-workspace/libre-workspace.env

# This script adds a user to this linux-server and to the guacamole database.
# If the user already exists, the script is able to handle this case.

# This script should be run as root
if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

# We need these variables:
# USERNAME
# PASSWORD
# ADMIN_STATUS

# Check if the number of arguments is equal to 3
if [ "$#" -ne 3 ]; then
    echo "Illegal number of parameters"
    echo "Usage: $0 <username> <password> <admin_status>"
    exit 1
fi

USERNAME=$1
PASSWORD=$2
ADMIN_STATUS=$3 # Values: 1=admin, 0=user

# If password is empty, then generate a random password
if [ -z "$PASSWORD" ]; then
    PASSWORD=$(openssl rand -base64 32)
fi

########################## Unix Authentication ##########################

change_password() {
    local username=$1
    local password=$2
    pam-auth-update --force --disable krb5
    passwd $username <<< "$password"$'\n'"$password"
    pam-auth-update --force --enable krb5
}

# Check if the user already exists
if id "lw.$USERNAME" &>/dev/null; then
    echo "User lw.$USERNAME already exists"
    # Change the password
    change_password lw.$USERNAME $PASSWORD
else
    # Add the user
    useradd -m -s /bin/bash lw.$USERNAME
    change_password lw.$USERNAME $PASSWORD
    echo "User lw.$USERNAME has been added"
fi

# Add the user to the sudo group if the user is an admin
if [ $ADMIN_STATUS = "1" ] ; then
    usermod -aG sudo lw.$USERNAME
    echo "User lw.$USERNAME has been added to the sudo group"
fi

# Disable ssh password authentication for the user

# Get the line number of the user in the sshd_config file
LINE_NUMBER=$(grep -n "Match User lw.$USERNAME" /etc/ssh/sshd_config | cut -d: -f1)
# Delete this line and the next line
sed -i "$LINE_NUMBER,+1d" /etc/ssh/sshd_config

echo "
Match User lw.$USERNAME 
    PasswordAuthentication no
" >> /etc/ssh/sshd_config
systemctl restart sshd

########################## Guacamole Database ##########################
MYSQL_HOST="localhost"
MYSQL_PORT="3307"
MYSQL_DATABASE="guacamole"
MYSQL_USER="guacamole"
MYSQL_PASSWORD="epho8Uk0"

# Check if the user already exists in the guacamole database, table guacamole_user
# The documentation about adding a user is:
# -- Generate salt
# SET @salt = UNHEX(SHA2(UUID(), 256));

# -- Create guacamole_entity
# INSERT INTO guacamole_entity (name, type) VALUES ('USER', 'USER');
# ENTITY_ID = SELECT entity_id FROM guacamole_entity WHERE name='USER';

# -- Create user and hash password with salt
# INSERT INTO guacamole_user (entity_id, password_salt, password_hash)
#      VALUES ($ENTITY_ID, @salt, UNHEX(SHA2(CONCAT('mypassword', HEX(@salt)), 256)));

if mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE -e "SELECT * FROM guacamole_entity WHERE name='$USERNAME'" | grep -q "$USERNAME"; then
    echo "User $USERNAME already exists in the guacamole database"
    # Update the password
    ENTITY_ID=$(mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE -e "SELECT entity_id FROM guacamole_entity WHERE name='$USERNAME'" | tail -n 1)
    echo $ENTITY_ID
    SALT=$(mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE -e "SELECT password_salt FROM guacamole_user WHERE entity_id=$ENTITY_ID" | tail -n 1)
    mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE -e "UPDATE guacamole_user SET password_hash=UNHEX(SHA2(CONCAT('$PASSWORD', HEX('$SALT')), 256)) WHERE entity_id=$ENTITY_ID"
else
    # Add the user
    mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE -e "SET @salt = UNHEX(SHA2(UUID(), 256)); INSERT INTO guacamole_entity (name, type) VALUES ('$USERNAME', 'USER'); SET @entity_id = LAST_INSERT_ID(); INSERT INTO guacamole_user (entity_id, password_salt, password_hash, password_date) VALUES (@entity_id, @salt, UNHEX(SHA2(CONCAT('$PASSWORD', HEX(@salt)), 256)), NOW());"
    echo "User $USERNAME has been added to the guacamole database"
fi


# Add admin status to the user if the user is an admin
# The documentation about adding an admin is:
# The guacamole_system_permission table contains the following columns:
# - user_id
#   The value of the user_id column of the entry associated with the user owning this permission.
# - permission
#   The permission being granted. This column can have one of three possible values: ADMINISTER, which grants the ability to administer the entire system (essentially a wildcard permission), CREATE_CONNECTION, which grants the ability to create connections, CREATE_CONNECTION_GROUP, which grants the ability to create connections groups, or CREATE_USER, which grants the ability to create users.
if [ $ADMIN_STATUS = "1" ] ; then
    ENTITY_ID=$(mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE -e "SELECT entity_id FROM guacamole_entity WHERE name='$USERNAME'" | tail -n 1)
    if mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE -e "SELECT * FROM guacamole_system_permission WHERE entity_id=$ENTITY_ID AND permission='ADMINISTER'" | grep -q "ADMINISTER"; then
        echo "User $USERNAME is already an admin in the guacamole database"
    else
        mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE -e "INSERT INTO guacamole_system_permission (entity_id, permission) VALUES ($ENTITY_ID, 'ADMINISTER')"
        echo "User $USERNAME has been added as an admin to the guacamole database"
    fi
else
    # Remove the admin status from the user if the user is still an admin in the guacamole database
    ENTITY_ID=$(mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE -e "SELECT entity_id FROM guacamole_entity WHERE name='$USERNAME'" | tail -n 1)
    if mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE -e "SELECT * FROM guacamole_system_permission WHERE entity_id=$ENTITY_ID AND permission='ADMINISTER'" | grep -q "ADMINISTER"; then
        mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE -e "DELETE FROM guacamole_system_permission WHERE entity_id=$ENTITY_ID AND permission='ADMINISTER'"
        echo "User $USERNAME has been removed as an admin from the guacamole database"
    else
        echo "User $USERNAME is not an admin in the guacamole database"
    fi
fi



# Now we add the connection to the linux server to the guacamole database for the user
# The documentation about adding a connection is:
# -- Create connection
# INSERT INTO guacamole_connection (connection_name, protocol) VALUES ('Cloud Desktop $USERNAME', 'rdp');

# -- Determine the connection_id
# SELECT * FROM guacamole_connection WHERE connection_name = 'Cloud Desktop $USERNAME' AND parent_id IS NULL;

# -- Add parameters to the new connection
# INSERT INTO guacamole_connection_parameter VALUES ($CONNEXTION_ID, 'hostname', '172.17.0.1'); # The IP of the docker host
# INSERT INTO guacamole_connection_parameter VALUES ($CONNEXTION_ID, 'port', '3389');
# INSERT INTO guacamole_connection_parameter VALUES ($CONNEXTION_ID, 'username', '$USERNAME');
# INSERT INTO guacamole_connection_parameter VALUES ($CONNEXTION_ID, 'password', '$PASSWORD');
# INSERT INTO guacamole_connection_parameter VALUES ($CONNEXTION_ID, 'security', 'any');
# INSERT INTO guacamole_connection_parameter VALUES ($CONNEXTION_ID, 'ignore-cert', 'true');
if mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE -e "SELECT * FROM guacamole_connection WHERE connection_name='Cloud Desktop $USERNAME' AND parent_id IS NULL" | grep -q "Cloud Desktop $USERNAME"; then
    echo "Connection Cloud Desktop $USERNAME already exists in the guacamole database"
    # Update the connection:
    CONNECTION_ID=$(mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE -e "SELECT connection_id FROM guacamole_connection WHERE connection_name='Cloud Desktop $USERNAME' AND parent_id IS NULL" | tail -n 1)
    mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE -e "UPDATE guacamole_connection_parameter SET parameter_value='$PASSWORD' WHERE connection_id=$CONNECTION_ID AND parameter_name='password'"
else
    # Add the connection
    mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE -e "INSERT INTO guacamole_connection (connection_name, protocol) VALUES ('Cloud Desktop $USERNAME', 'rdp')"
    CONNECTION_ID=$(mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE -e "SELECT connection_id FROM guacamole_connection WHERE connection_name='Cloud Desktop $USERNAME' AND parent_id IS NULL" | tail -n 1)
    mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE -e "INSERT INTO guacamole_connection_parameter VALUES ($CONNECTION_ID, 'hostname', '172.17.0.1')"
    mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE -e "INSERT INTO guacamole_connection_parameter VALUES ($CONNECTION_ID, 'port', '3389')"
    mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE -e "INSERT INTO guacamole_connection_parameter VALUES ($CONNECTION_ID, 'username', 'lw.$USERNAME')"
    mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE -e "INSERT INTO guacamole_connection_parameter VALUES ($CONNECTION_ID, 'password', '$PASSWORD')"
    mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE -e "INSERT INTO guacamole_connection_parameter VALUES ($CONNECTION_ID, 'security', 'any')"
    mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE -e "INSERT INTO guacamole_connection_parameter VALUES ($CONNECTION_ID, 'ignore-cert', 'true')"
    # Set keyboard layout to de
    mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE -e "INSERT INTO guacamole_connection_parameter VALUES ($CONNECTION_ID, 'server-layout', 'de-de-qwertz')"
    echo "Connection Cloud Desktop $USERNAME has been added to the guacamole database"
fi


# Now we have to add the connection to the user via the guacamole_connection_permission table
# The fields are: ENTITY_ID, CONNECTION_ID, PERMISSION
# As permission we use READ
ENTITY_ID=$(mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE -e "SELECT entity_id FROM guacamole_entity WHERE name='$USERNAME'" | tail -n 1)
if mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE -e "SELECT * FROM guacamole_connection_permission WHERE entity_id=$ENTITY_ID AND connection_id=$CONNECTION_ID AND permission='READ'" | grep -q "READ"; then
    echo "Connection Cloud Desktop $USERNAME is already assigned to user $USERNAME in the guacamole database"
else
    mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE -e "INSERT INTO guacamole_connection_permission (entity_id, connection_id, permission) VALUES ($ENTITY_ID, $CONNECTION_ID, 'READ')"
    echo "Connection Cloud Desktop $USERNAME has been assigned to user $USERNAME in the guacamole database"
fi

create_autostart() {
    local username=$1
    local script_name=$2

    mkdir -p /home/lw.$USERNAME/.config/autostart

    echo "[Desktop Entry]
Type=Application
Exec=/home/lw.$username/.scripts/$script_name
X-GNOME-Autostart-enabled=true
NoDisplay=false
Hidden=false
Name=$script_name
Comment=Created by the Libre Workspace
" > /home/lw.$username/.config/autostart/$script_name.desktop
    
}

mkdir -p /home/lw.$USERNAME/.scripts
cp /usr/lib/libre-workspace/modules/desktop/scripts/* /home/lw.$USERNAME/.scripts/
chmod +x /home/lw.$USERNAME/.scripts/*
for SCRIPT in /home/lw.$USERNAME/.scripts/*; do
    SCRIPT_NAME=$(basename $SCRIPT)
    create_autostart $USERNAME $SCRIPT_NAME
done

mkdir -p /home/lw.$USERNAME/.local/share/applications
tee /home/lw.$USERNAME/.local/share/applications/libre-workspace-portal.desktop << EOF
[Desktop Entry]
Version=1.0
Name=Libre Workspace Portal
Comment=portal.$DOMAIN
Exec=chromium --class=WebApp-LibreWorkspacePortal --name=WebApp-LibreWorkspacePortal --user-data-dir=/home/lw.$USERNAME/.local/share/ice/profiles/LibreWorkspacePortal "https://portal.$DOMAIN/"
Terminal=false
X-MultipleArgs=false
Type=Application
Icon=libre-workspace
Categories=GTK;WebApps;
MimeType=text/html;text/xml;application/xhtml_xml;
StartupWMClass=WebApp-LibreWorkspacePortal
StartupNotify=true
X-WebApp-Browser=Chromium
X-WebApp-URL=https://portal.$DOMAIN/
X-WebApp-CustomParameters=
X-WebApp-Navbar=true
X-WebApp-PrivateWindow=false
X-WebApp-Isolated=true
EOF



## SETUP NEXTCLOUD MOUNT VIA RCLONE ##
sudo apt install rclone -y

# Add a Nextcloud auth token for the user
NC_PASS=$(openssl rand -base64 32)
OUTPUT=$(sudo -u www-data env NC_PASS="$NC_PASS" php /var/www/nextcloud/occ user:auth-tokens:add --password-from-env "$USERNAME")
# Extract the token from the output (replace "app password: " with nothing)
TOKEN=$(echo $OUTPUT | sed 's/.*app password: //')
mkdir -p /home/lw.$USERNAME/Nextcloud

# Add a rclone config for the user
RCLONE_CONFIG="/home/lw.$USERNAME/.config/rclone/rclone.conf"
mkdir -p /home/lw.$USERNAME/.config/rclone

# Obscure the Nextcloud password so rclone can reveal it later
OBSCURED_PASS=$(rclone obscure "$TOKEN")

cat > "$RCLONE_CONFIG" << EOF
[nextcloud]
type = webdav
url = https://cloud.$DOMAIN/remote.php/dav/files/$USERNAME/
vendor = nextcloud
user = $USERNAME
pass = $OBSCURED_PASS
EOF

chmod 600 $RCLONE_CONFIG
chmod 700 /home/lw.$USERNAME/.config/rclone

# Add script to autostart to mount nextcloud via rclone
tee /home/lw.$USERNAME/.scripts/mount_nextcloud.sh << EOF
#!/bin/bash
rclone --config /home/lw.$USERNAME/.config/rclone/rclone.conf mount nextcloud: /home/lw.$USERNAME/Nextcloud --vfs-cache-mode writes --daemon
EOF
chmod +x /home/lw.$USERNAME/.scripts/mount_nextcloud.sh
create_autostart $USERNAME "mount_nextcloud.sh"


chmod 770 /home/lw.$USERNAME/
chown -R lw.$USERNAME:lw.$USERNAME /home/lw.$USERNAME/

