*****************
Samba File Shares
*****************

At the current time Libre Workspace doesn't provide this management in the web portal yet so you have to manage them by hand.
Normally you want to create a group first, which you can easily do via the libre workspace portal.

In this example we will create a samba share called ``myshare`` which is only accessible for the group ``mygroup``.

.. code-block:: bash

    # Make sure the group mygroup exists (web interface)
    mkdir -p /data/samba/myshare
    chown -R root:"mygroup" /data/samba/myshare
    chmod 770 /data/samba/myshare

    nano /etc/samba/smb.conf
    # Make sure this is included once in the file:

.. code-block:: ini

    [global]
    ; Generic Share Settings for ACLs (Essential for AD DC)
    ; This section sets standard VFS modules for all shares below it.
    ; It ensures Windows ACLs work correctly with your file system.
    vfs objects = acl_xattr
    map acl inherit = yes
    store dos attributes = yes


And then add the share at the end of the file like this:

.. code-block:: ini
  
    [myshare]
    path = /data/samba/myshare
    valid users = @mygroup
    browsable = yes
    writable = yes
    read only = no


.. code-block:: bash

    # Restart samba
    systemctl restart samba-ad-dc


Windows Access
==============

You can now access the share via Windows Explorer like this: ``\\int.de\myshare``
Make sure that you are logged in with a user which is member of the group ``mygroup``.


Linux Access
============

You can access the share via cifs like this:

.. code-block:: bash

    mount -t cifs -o username=yourusername //int.de/myshare /mnt/myshare


Or via e.g. nemo via ``smb://int.de/myshare``.
The domain would be here ``INT``.