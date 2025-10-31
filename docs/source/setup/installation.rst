************
Installation
************

You can either install Libre Workspace as a .deb file on an existing Debian server, or you can install it on a bare metal system using the provided ISO image.

Installation using the ISO image
================================

.. tip::

    Watch the YouTube playlist (in German) for a complete installation guide: `Youtubelist <https://www.youtube.com/playlist?list=PL26JW41WknwissQLa5JSEnGui9rHppYXB>`_.

.. note::

    The ISO image is based on Debian netinstall and will install a minimal Debian system with the Libre Workspace package. This is the recommended and easiest way to install Libre Workspace on your own.

1. You can download the ISO image from the `releases page <https://github.com/Jean28518/libre-workspace/releases/latest>`_.
2. Write the ISO image to a USB stick using `balenaEtcher <https://etcher.balena.io/>`_ or run it, for example, in a virtual machine.

.. tip::

    If you want to test the ISO image in a virtual machine, you can use `VirtualBox <https://www.virtualbox.org/>`_. It is important to set the network adapter to "Bridged Adapter" in the virtual machine's settings.

3. Boot the installation media (choose graphical install); the installer will start automatically.
4. Almost all points are done automatically unless you are asked for disk partitioning. If you are asked for disk partitioning, you can select "Guided - use entire disk" and confirm the following questions with "Yes."

.. tip::

    If you want to create a RAID or set the data directory to another disk, you can do so by selecting "Manual" and following the instructions. If you choose '/data' as a mount point, Libre Workspace will use this directory as the data directory and store all Nextcloud data there.

5. After the system installation is complete, the system will reboot and install the portal. This takes about 5 to 10 minutes, during which the screen may remain black. Find the system's IP address and open it in your browser; otherwise, follow the instructions on the server display.

.. note::

    From now on, you can also access the server via SSH. The default user is 'systemv' and the password is currently 'LibreWorkspace'.

6. On the webpage, an installer opens. You will be asked to set a password for the admin user. This has to be very secure because it is also used as the administrative password for the other components like Nextcloud or Samba-DC.
7. In the next step, you can choose which components you want to install. At the moment, this can't be changed later automatically. Samba-DC (central user management) is always automatically installed.
8. In the Domain Settings, you can choose if the Libre Workspace server should be externally accessible. This can't be changed later automatically. External access is highly recommended if you want easy access to your data from outside your home network and don't want to handle DNS settings on your own. But for that, you need a domain name.

.. tip::
    If you are unsure whether to use public or private access, it is recommended to use the private access. For this, you don't need a domain name and you can still access your data from outside your home network via a VPN.

9. Now the installation starts. This can take a while. Instructions are displayed on the screen on how to access Libre Workspace after the installation is complete.

.. note::

    The server needs access to the internet to download the necessary packages. As a DNS server, `Quad9 <https://www.quad9.net/>`_ is used.

10. Your login at the web interface is "Administrator" with the password you set in step 6.

.. warning::

    If your server is accessible from the internet, consider disabling the password login and only allowing SSH login via an SSH key. You can find instructions for this `here <https://www.thomas-krenn.com/en/wiki/SSH_public_key_authentication_under_Ubuntu>`_.

Installation on an existing Debian system
=========================================

.. note::

    This is not recommended for beginners. It is recommended to use the ISO image instead.

You can download and install the .deb file with the following commands:

.. code-block:: bash
    
    # Setup Repository
    sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
    curl -1sLf 'https://repo.libre-workspace.org/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/libre-workspace-archive-keyring.gpg
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/libre-workspace-archive-keyring.gpg] https://repo.libre-workspace.org stable main" | sudo tee /etc/apt/sources.list.d/libre-workspace-stable.list > /dev/null
    sudo apt update

    # Install Libre Workspace Portal
    sudo apt install libre-workspace-portal
    # This message can be ignored:
    # N: Download is performed unsandboxed as root as file '/root/libre-workspace-portal.deb' couldn't be accessed by user '_apt'. - pkgAcquire::Run (13: Permission denied)
    # If you don't run the graphical welcome assistant:
    sudo systemctl enable libre-workspace-service --now

This will install the webserver Caddy and the management portal which listens on port 443.

.. note::

    If you are using another web server/reverse proxy, you can ignore the Caddy installation and disable it by running ``sudo systemctl disable caddy --now``. But with this, you have to configure all reverse proxies on your own. You can always see the current configuration of Caddy in ``/etc/caddy/Caddyfile``.

Now you can decide if you want to run the Libre Workspace automated install script or if you want to configure it manually.

Automated install script
------------------------

You can now access the Libre Workspace portal via https by the IP. A detailed explanation of the installation script can be found above in the section "Installation using the ISO image."

.. tip::

    If you want to follow the installation output, you can run ``journalctl -u libre-workspace-portal.service -f``.

Manual configuration
--------------------

This is not recommended for complete beginners in Linux administration. The recommended Linux distribution is Debian (Stable). With this option, you are also able to "connect" existing installations of Nextcloud, Samba-DC, etc. to the management portal (but also the automated install script for the rest is available here).

If you are using Caddy, replace the two last Caddy blocks in the Caddyfile, for example, with the following (you may want to change the domain):

.. code-block:: yaml

    portal.int.de {
        handle_path /static* {
            root * /var/www/libre-workspace-static
            file_server
            encode zstd gzip
        }
        handle_path /media* {
            root * /var/lib/libre-workspace/portal/media
            file_server
            encode zstd gzip
        }
        reverse_proxy localhost:11123
    }

If you are using another web server/reverse proxy, you have to configure it yourself. The management portal listens via http on port 11123.

It is mandatory to configure the cfg file at /etc/libre-workspace/portal/portal.conf. If you want to use the active directory functionality, you have to take care of the installation yourself. The LDAP configuration is done in the cfg file. By default, LDAP is disabled. Your default login at the web interface is "Administrator" with the password "LibreWorkspace." More details can be found in the cfg file.

You also have to ensure /etc/libre-workspace/libre-workspace.env, which is used for addon and module handling. The following variables are mandatory to be set. An example would be:

.. code-block:: bash

    export IP="1.2.3.4"
    export ADMIN_PASSWORD="AdminPasswordOfTheLDAPDomainOtherwiseSetItToAnEmptyString"
    export DOMAIN="int.de"
    export LDAP_DC="dc=int,dc=de" # Keep it empty if you don't use LDAP
    export LANGUAGE="en" # or "de"

Libre Workspace Lite
====================

You can also just install the management portal without the other components. This is called "Libre Workspace Lite." Start the installation via the web interface as you would for normal installations. In the component selection, you can deselect all components. Then the installation will only install the management portal, the webserver Caddy, Docker, and Docker Compose. Here, you can also define how the management portal should be accessible. The default is via https on port 23816. Afterwards, it is possible to install the other components and addons via the management portal.