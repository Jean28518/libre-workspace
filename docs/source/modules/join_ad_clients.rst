*************************
Join Clients to AD Domain
*************************

Because Libre Workspace uses Samba as Active Directory Domain Controller, both Linux and Windows clients can be joined to the integrated AD domain.
In these example instructions, we assume the domain is ``int.de``. Please replace it with your actual domain.

To enable AD joining for clients, you currently have to set the ufw rules yourself:

.. code-block:: bash
    LOCALSUBNET="192.168.1.0/24"  # Adjust this to your local subnet where your clients are located.
    sudo ufw allow from $LOCALSUBNET to any port 53
    sudo ufw allow from $LOCALSUBNET to any port 88
    sudo ufw allow from $LOCALSUBNET to any port 135
    sudo ufw allow from $LOCALSUBNET to any port 139
    sudo ufw allow from $LOCALSUBNET to any port 445
    sudo ufw allow from $LOCALSUBNET to any port 464
    sudo ufw allow from $LOCALSUBNET to any port 636
    sudo ufw allow from $LOCALSUBNET to any port 7389
    sudo ufw allow from $LOCALSUBNET to any port 3268
    sudo ufw allow from $LOCALSUBNET to any port 3269


.. note:: If you dont want to open up these ports to all your linux clients, you can also use our user and group sync script described in some chapters after this one. For that we will use the Libre Workspace API.


Joining Linux Clients
=====================

- Make sure your clients server DNS is set to the IP of your Libre Workspace server.

.. code-block:: bash

    sudo -i
    hostnamectl set-hostname client1 # Set a proper hostname
    apt update
    apt install realmd sssd sssd-tools adcli krb5-user packagekit vim -y
    ping INT.DE -c 4 # Verify that the domain is reachable

    # Join the domain (the password is the one of the ADMINISTRATOR user):
    realm join --user=ADMINISTRATOR INT.DE
    # Verify the join:
    realm list

    # Now configure SSSD to create home directories on login:
    systemctl enable sssd
    pam-auth-update --enable mkhomedir

    # Check User info: Try to get user info from the domain
    # (replace myuser with an actual user from the domain)
    id myuser@int.de

    # Disable showing user list in LightDM greeter
    echo "[Seat:*]
    greeter-show-manual-login=true
    greeter-hide-users=true
    " > /etc/lightdm/lightdm.conf
    
    # Allow login with short names (without domain part)
    sed -i 's/use_fully_qualified_names = True/use_fully_qualified_names = False/' /etc/sssd/sssd.conf
    echo "default_domain_suffix = int.de" >> /etc/sssd/sssd.conf

    # Reboot your client to finalize everything


Joining Windows Clients
=======================

- Make sure your clients server DNS is set to the IP of your Libre Workspace server.
- Make sure the name of your Windows client is set properly (e.g., CLIENT1).
- Run as Administrator in Windows PowerShell:

.. code-block:: powershell

    # Test if Windows finds the DC:
    nltest /dsgetdc:int.de

    # Join the domain (the password is the one of the ADMINISTRATOR user):
    Add-Computer -DomainName int.de -Credential ADMINISTRATOR@INT.DE -Restart

    # After reboot, you can login with domain users.