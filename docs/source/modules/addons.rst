******
Addons
******

Addons are a way to extend the functionality of the core system. 
They are currently implemented as a way to add new service-components to the system.

.. hint:: text
    Whenever [NAME] is be mentioned in the article below, it should be replaced with the name of the addon in only lowercase letters.



Addon Structure
===============

Addons could be stored in a single .zip file. However for more complexity and functionality they are now packaged and shipped in a .deb file.
A good starting point is to use the addon creator inside the Libre Workspace Portal (Systemkonfiguration -> Addons -> Create Addon). It will generate the basic structure for you, even if you are not using any docker containers.
The addon control files are stored in the directory ``/var/lib/libre-workspace/modules/[NAME]``.
It should contain the following structure:

.. code-block:: bash

    - /var/lib/libre-workspace/modules/[NAME]/
        - [NAME].conf
        - setup_[NAME].sh
        - update_[NAME].sh
        - remove_[NAME].sh
        - update_env.sh (optional)
        - [NAME].png / [NAME].svg / [NAME].jpg / [NAME].webp
        - LICENSE 
        - patches/ (optional)
            - 1970-01-01_my_first_patch.sh (optional)
        - any other files needed for the installation of the addon (optional)

If you want to distribute your config add a LICENSE file. Apache 2.0 is highly recommended: https://www.apache.org/licenses/LICENSE-2.0.html#apply )

An example of the structure of the addon nocodb would be:

.. code-block:: bash

    - /var/lib/libre-workspace/modules/nocodb/
        - patches/ (optional)
            - 1970-01-01_my_first_patch.sh (optional)
        - nocodb.conf
        - setup_nocodb.sh
        - update_nocodb.sh
        - remove_nocodb.sh
        - nocodb.png
        - LICENSE


[NAME].conf
-----------

This file contains the configuration for the addon. It is a simple text file with the following format:

.. code-block:: bash

    id="[NAME]"
    name="[Nice Name]"
    description="[DESCRIPTION]"
    author="[AUTHOR]"
    email="[EMAIL]"
    url="[URL]"

An example of nocodb.conf would be:

.. code-block:: bash

    id="nocodb"
    name="NocoDB"
    description="Database Management Tool"
    author="NocoDB Developers"
    email="db@example.com"
    url="db"

the url should be only the third level domain name, without the protocol or the path.
The shorter the better. Make sure it doesn't conflict with any other addon you want to install.
You are able to add multiple urls to the addon. Just separate them with a comma. For example: ``url="db,db2"``
In special cases you can also keep the url empty. Set then the url to ``url=""``.


setup_[NAME].sh
---------------

This file is a simple shell script which is executed when the administrator installs the service (or module) in the system configuration.
It is automatically executed as root. Three variables are passed to the script:

- $DOMAIN: The domain name of the service example: ``int.de``
- $ADMIN_PASSWORD: The password of the administrator which is used for the ldap instance or the system user "systemv" which has also admin rights with sudo
- $IP: The IP address of the server
- $LDAP_DC: The domain component of the ldap instance

It is a good practice to store the config of the service in the ``/root/[NAME]`` directory, for example the docker-compose.yml file. 
**The addon detection is based on the existence of this folder.** For example even patches are not run, if this folder ``/root/[NAME]`` does not exist. And it will be easier for system administrators to find the config of the service in the future.
Also you have to mind adding an entry to the ``/etc/caddy/Caddyfile`` to make the service accessible.

The current working directory is the root directory of the addon. It may be at /var/lib/libre-workspace/modules/[NAME].
Please do not use cd in all your scripts, because it could lead to unexpected behavior. At least if you are using them, make sure to run ``cd -`` at the end.

An example of setup_nocodb.sh would be:

.. code-block:: bash

  #!/bin/bash
  # This script gets three variables passed: $DOMAIN, $ADMIN_PASSWORD, $IP, $LDAP_DC
  mkdir -p /root/nocodb
  # Dont forget to escape " with a backslash:
  echo "version: \"2.1\"
  services: 
    nocodb: 
      depends_on: 
        root_db: 
          condition: service_healthy
      environment: 
        NC_DB: \"mysql2://root_db:3306?u=noco&p=faiTh8ra&d=root_db\"
      image: \"nocodb/nocodb:latest\"
      ports: 
        - \"23260:8080\"
      restart: unless-stopped
      volumes: 
        - \"./nc_data:/usr/app/data\"
    root_db: 
      environment: 
        MYSQL_DATABASE: root_db
        MYSQL_PASSWORD: faiTh8ra
        MYSQL_ROOT_PASSWORD: faiTh8ra
        MYSQL_USER: noco
      healthcheck: 
        retries: 10
        test: 
          - CMD
          - mysqladmin
          - ping
          - \"-h\"
          - localhost
        timeout: 20s
      image: \"mysql:8.0.32\"
      restart: unless-stopped
      volumes: 
        - \"./db_data:/var/lib/mysql\"
  " > /root/nocodb/docker-compose.yml

  docker-compose -f /root/nocodb/docker-compose.yml up -d
  
  echo "db.$DOMAIN {
      #tls internal
      reverse_proxy localhost:23260
  }

  " >> /etc/caddy/Caddyfile

  # If domain is "int.de" uncomment the tls internal line for internal https
  # IT IS RECOMMENDED THAT YOU DO NOT EDIT THESE 3 LINES unless you know what you're doing.
  # (Usually you don't have to edit them at all)
  if [ "$DOMAIN" = "int.de" ]; then
    sed -i 's/#tls internal/tls internal/g' /etc/caddy/Caddyfile
  fi

  systemctl restart caddy

You can get inspiration of more complicated setups here: https://github.com/Jean28518/libre-workspace/tree/main/src/lac/unix/unix_scripts (Don't mind the addons folder there. Have a look to the other folders like matrix, nextcloud, ... . They have almost the same structure as the addons)

update_[NAME].sh
----------------

This file is a simple shell script which is executed when the administrator updates the service (or module) in the system configuration.
It is normally executed as root every day, if the admin has enabled the automatic updates of this service.
If you don't want to update the service, just leave the file empty. But its important to have the file.

An example of update_nocodb.sh would be:

.. code-block:: bash

    #!/bin/bash
    docker-compose -f /root/nocodb/docker-compose.yml pull
    docker-compose -f /root/nocodb/docker-compose.yml up -d

remove_[NAME].sh
----------------

This file is a simple shell script which is executed when the administrator removes the service (or module) from the system configuration.
It is automatically executed as root. It is a good practice to remove the complete folder ``/root/[NAME]`` directory, because the addon detection is based on the existence of this folder.
It is also good practice to remove all correponding data. 
For example, if you have a database, you should remove the database and the database user.

The current working directory is the root directory of the addon. It may be at /var/lib/libre-workspace/modules/[NAME].
Please do not use cd in all your scripts, because it could lead to unexpected behavior. At least if you are using them, make sure to run ``cd -`` at the end.

An example of remove_nocodb.sh would be:

.. code-block:: bash

    #!/bin/bash
    # This script gets three variables passed: $DOMAIN, $ADMIN_PASSWORD, $IP, $LDAP_DC
    docker-compose -f /root/nocodb/docker-compose.yml down --volumes
    rm -rf /root/nocodb


    # Remove the entry from the Caddyfile
    sed -i "/db.$DOMAIN {/,/}/d" /etc/caddy/Caddyfile
    # On more complicated entries you can also use:
    # libre-workspace-remove-webserver-entry db.$DOMAIN
    
    systemctl restart caddy


update_env.sh
-------------

This file is a simple shell script which is executed when the administrator updates the environment of the system configuration,
which could be the master password (also changes the LDAP administrator password) or the IP address of the server, under which it is accessible.
If your addon doesn't rely on the IP address or the master password, you can ignore this file. It is then not necessary to have it.

In our example of nocodb we don't need this file, because we don't rely on the IP address or the master password.
So we don't even have to create this file.


patches
-------

For future updates of the addon, you can add patches to the patches folder (which is optional)
It is a good practice to name the patch at the date when it was created, so you can easily see the order of the patches.
These patch scripts are executed after a daily backup and update of the system or daily at 02:00 am. 
The run order is based on the filename. The patch with the oldest date is executed first.
The patch scripts are executed as root and the current working directory is the root directory of the addon.
The environment variables $DOMAIN, $ADMIN_PASSWORD, $IP and $LDAP_DC are passed to the script and are available in the script.

The patch should only patch your addon once.
But for this you have to check by yourself if the patched settings are present or not. This can be different for every single patch.
Also it is highly recommended to keep your addon constistent over time, so it should disable itself after 1 year of its release.

Here you can see an example of a redis patch for nextloud:

.. code-block:: bash
      
    #!/bin/bash

    # IS THIS PATCH OLDER THAN 365 DAYS?
    # Get the current file name
    FILE_NAME=$(basename $0)
    # Get the date of the filename which is like this: 2024-06-25
    DATE=${FILE_NAME:0:10}
    # Check if the file is older than 365 days
    if [ $(( ($(date +%s) - $(date -d $DATE +%s)) / 86400 )) -gt 365 ]; then
      echo "Patch is older than 365 days. Exiting patch."
      exit 0
    fi


    # Check if we need to apply the patch
    # Is redis installed?
    if [ -x "$(command -v redis-server)" ]; then
      echo "Redis is already installed. Exiting patch."
      exit 0
    fi

    # BEGIN APPLYING PATCH
    # Install redis and php packages
    apt-get install redis php-redis php-apcu php-memcache pwgen -y

    # ... do the rest 


General Tips
============

- Never experiment on production systems. Always test your scripts on a test system first.
- It is a good practice by running the commands line by line manually on a test system to see if everything works as expected.