************
Installation
************

You can either install libre workspace as a .deb file on an existing Debian or Ubuntu server, 
or you can install it on a bare metal system using the provided ISO image (recommended).

Installation using the ISO image (recommended)
==============================================

.. note::

    The ISO image is based on debian netinstall and will install a minimal debian system with the libre workspace package.
    This is the recommended and easiest way to install libre workspace on your own.

1. You can download the ISO image from the `releases page <https://github.com/Jean28518/libre-workspace/releases/latest>`_.
2. Write the ISO image to a USB stick using `balena etcher <https://etcher.balena.io/>`_ or run it e.g. in a virtual machine.

.. tip::

    If you want to test the ISO image in a virtual machine, you can use `VirtualBox <https://www.virtualbox.org/>`_.
    It is important to set the network adapter to "Bridged Adapter" in the settings of the virtual machine.

1. Boot the installation media, the installer will start automatically.
2. Almost all points are done automatically unless you are asked for the disk partitioning.
   If you are asked for the disk partitioning, you can select "Guided - use entire disk" and confirm the following questions with "Yes".

.. tip::

   If you want to create a RAID or want to set the data directory to another disk, you can do so by selecting "Manual" and following the instructions.
   If you choose '/data' as a mountpoint, Libre Workspace will use this directory as the data directory and stores all nextcloud data there.
   

1. After the installation is complete, the system will reboot. Discover the IP address of the system and open it in your browser. Otherwise you can just follow the instructions of the server display.

.. note::

    From now you can also access the server via SSH. The default user is 'systemv' and the password is currently 'LibreWorkspace'.

1. At the webpage an installer opens. You will be asked to set a password for the admin user. This has to be very secure, because it is also used as administrative password for the other components like nextcloud or samba-dc. **At the current time you can't change your password later.**
2. In the next step you can choose which components you want to install. At the moment this can't be changed later automatically. Samba-DC (central user management) is always automatically installed.
3. In the Domain Settings you can choose if the libre workspace server should be externally accessible. This can't be changed later automatically. An external access is highly recommended if you want easy access to your data from outside your home network and don't want to handle DNS-Settings on your own. But for that you need a domain name.

.. tip::
    If you are unsure whether to use public or private access, it is recommended to use the private access.
    For this you don't need a domain name and you can still access your data from outside your home network via VPN.

10. Now the installation starts. This can take a while. There are instructions displayed on the screen, how to access the libre workspace after the installation is complete.
11. Your login at the web interface is "Administrator" with the password you set in step 6.

.. warning::

    If your server is accessible from the internet, consieder to disable the password login and only allow ssh login via ssh key. 
    You can find instructions for this `here <https://www.thomas-krenn.com/en/wiki/SSH_public_key_authentication_under_Ubuntu>`_.

Installation on an existing Debian or Ubuntu system
===================================================

.. note::

    This is not recommended for beginners. It is recommended to use the ISO image instead.

1. Download the latest .deb file from the `releases page <https://github.com/Jean28518/linux-arbeitsplatz-central/releases/latest>`_.
2. You can install the .deb file with the following command:

.. code-block:: bash

    sudo apt install ./linux-arbeitsplatz.deb
    sudo systemctl start linux-arbeitsplatz-web
    # If you don't run the welcome assistant:
    sudo systemctl start linux-arbeitsplatz-unix

This will install the the webserver caddy and the management portal which listens on port 443.

.. note::

    If you are using another webserver/reverse proxy you can ignore the caddy installation and disable it by running ``sudo systemctl disable caddy --now``.


Now you can decide if you want to run the libre workspace automated install script or if you want to configure it manually.

Automated install script
------------------------

You can now access the libre workspace portal via https by the IP.
A detailed explanation of the installation script can be found upper in the section "Installation using the ISO image".

Manual configuration
--------------------

This is not recommended for beginners. This only installs the Libre Workspace Portal.
With this option you can "connect" existing installations of nextcloud, samba-dc ... to the management portal.

If you are using caddy, replace the two last caddy blocks in the caddyfile e.g. with the following (you may want to change the domain):

.. code-block:: yaml

    portal.int.de {
        handle_path /static* {
            root * /var/www/linux-arbeitsplatz-static
            file_server
            encode zstd gzip
        }
        handle_path /media* {
            root * /usr/share/linux-arbeitsplatz/media
            file_server
            encode zstd gzip
        }
        reverse_proxy localhost:11123
    }

If you are using another webserver/reverse proxy you have to configure it yourself. The management portal listens via http on port 11123.

It is mandatory to configure the cfg file at /usr/share/linux-arbeitsplatz/cfg. If you want to use the active directory functionality you have to care about yourself about the installation of this. The LDAP configuration is done in the cfg file.
By default, ldap is disabled. Your default login at the web interface is "Administrator" with the password "LibreWorkspace". More details can be found in the cfg file.